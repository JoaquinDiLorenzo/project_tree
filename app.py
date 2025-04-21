import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pyperclip
import streamlit as st
from git import Repo

# === FUNCIÓN PARA CONSTRUIR EL ÁRBOL DE CARPETAS DE FORMA BONITA ===

def generate_pretty_tree(root_dir, show_sizes=False, not_start=[], not_in=[]):
    root_path = Path(root_dir)
    tree_text = [f"Estructura de: {root_path.name}\n{'=' * 30}"]
    _build_tree(tree_text, root_path, prefix="", is_last=True,
                show_sizes=show_sizes, not_start=not_start, not_in=not_in)
    return "\n".join(tree_text)

# Función recursiva auxiliar para recorrer carpetas y construir el árbol
def _build_tree(tree_text, directory, prefix, is_last, show_sizes, not_start, not_in):
    connector = "└── " if is_last else "├── "
    tree_text.append(f"{prefix}{connector}{directory.name}/")

    new_prefix = prefix + ("    " if is_last else "│   ")
    try:
        items = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name))
    except Exception:
        return  # Ignora carpetas inaccesibles (por permisos, etc.)

    # Filtrar carpetas/archivos excluidos
    items = [item for item in items 
             if item.name not in not_in and not any(item.name.startswith(s) for s in not_start)]

    # Recorrer los ítems filtrados
    for index, item in enumerate(items):
        is_last_item = (index == len(items) - 1)
        if item.is_dir():
            _build_tree(tree_text, item, new_prefix, is_last_item, show_sizes, not_start, not_in)
        else:
            size = f" ({os.path.getsize(item)} bytes)" if show_sizes else ""
            connector = "└── " if is_last_item else "├── "
            tree_text.append(f"{new_prefix}{connector}{item.name}{size}")

# === FUNCIONES AUXILIARES ===

# Extrae el contenido de un ZIP en una carpeta temporal
def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

# Encuentra la carpeta raíz real de un proyecto extraído (si solo hay una carpeta dentro)
def find_project_root(base_path):
    children = list(base_path.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return base_path

# Obtiene todas las subcarpetas (excluyendo las que el usuario no quiere mostrar)
def get_all_subdirs(path, not_start=[], not_in=[]):
    subdirs = []

    for root, dirs, _ in os.walk(path):
        root_path = Path(root)

        # Aplicar filtro de exclusión directamente a dirs
        dirs[:] = [d for d in dirs if d not in not_in and not any(d.startswith(s) for s in not_start)]

        for d in dirs:
            full_path = root_path / d
            subdirs.append(full_path)

    return [path] + sorted(subdirs)

# === INTERFAZ CON STREAMLIT ===

st.title("🌳 Generador de Estructura de Proyectos")
st.markdown("Sube un ZIP o ingresa un link de GitHub para generar la estructura de carpetas.")

# Entrada de archivos ZIP o URL de GitHub
uploaded_file = st.file_uploader("📦 Sube tu proyecto (ZIP)", type="zip")
github_url = st.text_input("🔗 O pega una URL de GitHub")
show_sizes = st.checkbox("Mostrar tamaños de archivos")

# Carpetas a excluir, introducidas por el usuario
exclude_folders_input = st.text_input("Excluir carpetas (separadas por coma)", "venv, env, __pycache__, .git")
not_in = [f.strip() for f in exclude_folders_input.split(",")]
not_start = ['.']  # También excluir las que empiezan con punto (ocultas)

project_path = None
base_dir_to_remove = None
selected_dir = None

# Si se subió un ZIP
if uploaded_file:
    temp_dir = Path(uploaded_file.name.replace(".zip", ""))
    temp_dir.mkdir(exist_ok=True)
    base_dir_to_remove = temp_dir  # Guardar para borrar después
    extract_zip(uploaded_file, temp_dir)
    project_path = find_project_root(temp_dir)

    # Mostrar lista de carpetas disponibles (ya filtradas) para seleccionar desde dónde generar el árbol
    all_subdirs = get_all_subdirs(project_path, not_start=not_start, not_in=not_in)
    selected_dir = st.selectbox(
        "📁 Carpeta desde la cual generar el árbol",
        options=all_subdirs,
        format_func=lambda p: str(p.relative_to(project_path))
    )

# Si se ingresó una URL de GitHub válida
elif github_url and github_url.startswith("https://github.com/"):
    try:
        project_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
        temp_root = tempfile.mkdtemp(prefix="gh_")
        temp_dir = Path(temp_root) / project_name
        Repo.clone_from(github_url, temp_dir)

        base_dir_to_remove = Path(temp_root)  # Para limpieza después

        # Eliminar carpeta .git después de clonar
        git_folder = temp_dir / ".git"
        if git_folder.exists():
            shutil.rmtree(git_folder, ignore_errors=True)

        project_path = find_project_root(temp_dir)
        selected_dir = project_path  # Mostrar siempre desde raíz en repositorios GitHub
    except Exception as e:
        st.error(f"Error al clonar el repositorio: {e}")
        project_path = None

# === GENERACIÓN Y VISUALIZACIÓN DEL ÁRBOL ===

if selected_dir:
    tree_text = generate_pretty_tree(
        selected_dir,
        show_sizes=show_sizes,
        not_start=not_start,
        not_in=not_in
    )

    # Mostrar árbol en pantalla
    st.code(tree_text, language="plaintext")

    # Botón para copiar el resultado al portapapeles
    if st.button("📋 Copiar al portapapeles"):
        pyperclip.copy(tree_text)
        st.success("¡Estructura copiada al portapapeles!")

# === LIMPIEZA TEMPORAL ===

# Permite borrar archivos protegidos
def on_rm_error(func, path, exc_info):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Borrar carpeta temporal si existe
if base_dir_to_remove and base_dir_to_remove.exists():
    try:
        shutil.rmtree(base_dir_to_remove, onerror=on_rm_error)
    except Exception:
        pass

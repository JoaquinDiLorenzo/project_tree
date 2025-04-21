import os
from pathlib import Path

def generate_pretty_tree(root_dir, output_file="project_structure.txt", show_sizes=False, not_start=[], not_in=[]):
    root_path = Path(root_dir)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Estructura de: {root_path.name}\n{'=' * 30}\n")
        _build_tree(f, root_path, prefix="", is_last=True, show_sizes=show_sizes, not_start=not_start, not_in=not_in)  # ¡Pasamos los parámetros aquí!

def _build_tree(f, directory, prefix, is_last, show_sizes, not_start, not_in):  # Añadimos los parámetros
    # Determinar el símbolo del nivel actual
    connector = "└── " if is_last else "├── "
    f.write(f"{prefix}{connector}{directory.name}/\n")

    # Actualizar el prefijo para los elementos hijos
    new_prefix = prefix + ("    " if is_last else "│   ")

    # Obtener y ordenar elementos (carpetas primero)
    items = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name))
    items = [item for item in items if item.name not in not_in and not any(item.name.startswith(s) for s in not_start)]

    for index, item in enumerate(items):
        is_last_item = (index == len(items) - 1)
        if item.is_dir():
            _build_tree(f, item, new_prefix, is_last_item, show_sizes, not_start, not_in)  # Pasamos los parámetros aquí también
        else:
            size = f" ({os.path.getsize(item)} bytes)" if show_sizes else ""
            connector = "└── " if is_last_item else "├── "
            f.write(f"{new_prefix}{connector}{item.name}{size}\n")

# Ejemplo de uso
generate_pretty_tree(
    r"D:\joaquin\Escritorio\letterboxdrecommender",
    show_sizes=True,
    not_start=['.'],
    not_in=['venv', 'env', '__pycache__']
)
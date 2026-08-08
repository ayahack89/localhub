from pathlib import Path


# ============================================================
# LOCALHUB PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# REPOSITORY ROOT
# ============================================================

REPOSITORY_ROOT = PROJECT_ROOT / "Repositories"


# ============================================================
# GET REPOSITORY ROOT
# ============================================================

def get_repository_root():
    return REPOSITORY_ROOT


# ============================================================
# GET DIRECTORY CONTENTS
# ============================================================

def get_directory_contents(relative_path=""):

    current_path = (REPOSITORY_ROOT / relative_path).resolve()

    # Security check
    if not current_path.is_relative_to(REPOSITORY_ROOT):
        raise PermissionError("Invalid repository path")

    if not current_path.exists():
        raise FileNotFoundError("Directory does not exist")

    if not current_path.is_dir():
        raise NotADirectoryError("Path is not a directory")

    items = []

    for path in sorted(
        current_path.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower())
    ):

        item_relative_path = path.relative_to(REPOSITORY_ROOT)

        items.append({
            "name": path.name,
            "relative_path": item_relative_path.as_posix(),
            "is_directory": path.is_dir(),
        })

    return items


# ============================================================
# GET FILE
# ============================================================

def get_file(relative_path):

    file_path = (REPOSITORY_ROOT / relative_path).resolve()

    # Security check
    if not file_path.is_relative_to(REPOSITORY_ROOT):
        raise PermissionError("Invalid file path")

    if not file_path.exists():
        raise FileNotFoundError("File does not exist")

    if not file_path.is_file():
        raise IsADirectoryError("Path is not a file")

    return file_path
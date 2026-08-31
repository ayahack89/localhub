from pathlib import Path

# Directories and files blocked from direct access or listing
PROTECTED_NAMES = {
    ".localhub",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
}


def is_protected_path(target_path: Path, repo_root: Path) -> bool:
    """Check if target_path falls inside protected directories or contains sensitive files."""
    try:
        rel = target_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True

    for part in rel.parts:
        if part in PROTECTED_NAMES:
            return True
        if part.startswith(".env"):
            return True
    return False


_ACTIVE_REPOSITORY_ROOT = None


def set_repository_root(path):
    """Set the active repository root for the current session."""
    global _ACTIVE_REPOSITORY_ROOT
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Repository directory does not exist: {path}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {path}")
    _ACTIVE_REPOSITORY_ROOT = resolved


def get_repository_root():
    """Return the active repository root, falling back to cwd."""
    if _ACTIVE_REPOSITORY_ROOT is not None:
        return _ACTIVE_REPOSITORY_ROOT
    return Path.cwd().resolve()


def get_directory_contents(relative_path=""):
    repo_root = get_repository_root()
    current_path = (repo_root / relative_path).resolve()

    # Prevent directory traversal outside repository root
    if not current_path.is_relative_to(repo_root):
        raise PermissionError("Invalid repository path")

    if is_protected_path(current_path, repo_root):
        raise PermissionError("Access denied to protected directory")

    if not current_path.exists():
        raise FileNotFoundError("Directory does not exist")

    if not current_path.is_dir():
        raise NotADirectoryError("Path is not a directory")

    items = []

    for path in sorted(
        current_path.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower())
    ):
        if is_protected_path(path, repo_root):
            continue

        item_relative_path = path.relative_to(repo_root)

        items.append({
            "name": path.name,
            "relative_path": item_relative_path.as_posix(),
            "is_directory": path.is_dir(),
            "size": path.stat().st_size if path.is_file() else 0,
        })

    return items


def get_file(relative_path):
    repo_root = get_repository_root()
    file_path = (repo_root / relative_path).resolve()

    # Prevent traversal outside repository root
    if not file_path.is_relative_to(repo_root):
        raise PermissionError("Invalid file path")

    if is_protected_path(file_path, repo_root):
        raise PermissionError("Access denied to protected file")

    if not file_path.exists():
        raise FileNotFoundError("File does not exist")

    if not file_path.is_file():
        raise IsADirectoryError("Path is not a file")

    return file_path
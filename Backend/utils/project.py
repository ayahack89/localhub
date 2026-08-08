from pathlib import Path

# Show current dir
def current_dir():
    C_dir = Path.cwd().name
    return C_dir


# Show current path
def current_path():
    C_path = Path.cwd()
    return C_path
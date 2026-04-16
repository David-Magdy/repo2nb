import pathlib
import fnmatch

DEFAULT_IGNORE = [
    "__pycache__", "*.pyc", "node_modules", ".DS_Store", "venv", ".venv", ".env", "*.egg-info", "dist", "build", ".git", ".pytest_cache", ".hypothesis", ".coverage",
    "uv.lock", ".python-version", "pyproject.toml"
]

def should_ignore(path: pathlib.Path) -> bool:
    name = path.name
    for pattern in DEFAULT_IGNORE:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False

def traverse(root_path: pathlib.Path) -> tuple[list, bool]:
    has_git = (root_path / ".git").is_dir()
    
    tree = []
    
    def _walk(current_path: pathlib.Path):
        if should_ignore(current_path):
            return
            
        files = []
        dirs = []
        for child in sorted(current_path.iterdir()):
            if should_ignore(child):
                continue
            if child.is_dir():
                dirs.append(child)
            else:
                files.append(child)
                
        tree.append((current_path, files))
        for d in dirs:
            _walk(d)
            
    _walk(root_path)
    return tree, has_git

import pathlib

from pathspec import GitIgnoreSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPatternError

DEFAULT_IGNORE = [
    "__pycache__", "*.pyc", "node_modules", ".DS_Store", "venv", ".venv", ".env", "*.egg-info", "dist", "build", ".git", ".pytest_cache", ".hypothesis", ".coverage",
    "uv.lock", ".python-version", "pyproject.toml",
    ".repo2nb", ".repo2nbignore"
]

IGNORE_FILENAME = ".repo2nbignore"


def _parse_lines(lines, source):
    """Yield valid gitignore-pattern lines; warn and skip malformed ones."""
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        try:
            GitIgnoreSpec.from_lines([stripped])
        except GitWildMatchPatternError as e:
            print(f"[repo2nb] WARNING: skipping malformed line in {source}: {stripped!r} ({e})")
            continue
        yield stripped


def load_ignore_spec(repo_path: pathlib.Path, extra_ignore=None) -> GitIgnoreSpec:
    lines = list(DEFAULT_IGNORE)
    for ext in sorted(extra_ignore or []):
        ext = ext.lower()
        lines.append("*" + ext if ext.startswith(".") else "*" + ext)
    ignore_file = repo_path / IGNORE_FILENAME
    if ignore_file.is_file():
        # ponytail: read as latin-1 to never crash on odd encodings; patterns are ascii in practice
        raw = ignore_file.read_text(encoding="utf-8", errors="replace").splitlines()
        lines.extend(_parse_lines(raw, IGNORE_FILENAME))
    return GitIgnoreSpec.from_lines(lines)


def traverse(root_path: pathlib.Path, extra_ignore=None) -> tuple[list, bool]:
    has_git = (root_path / ".git").is_dir()
    spec = load_ignore_spec(root_path, extra_ignore)

    def ignored(rel: str) -> bool:
        return spec.match_file(rel) or spec.match_file(rel + "/")

    tree = []

    def _walk(current_path: pathlib.Path):
        files = []
        dirs = []
        for child in sorted(current_path.iterdir()):
            rel = child.relative_to(root_path).as_posix()
            if ignored(rel):
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

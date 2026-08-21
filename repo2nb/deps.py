import ast
import pathlib
import subprocess
import sys

# Common import-name -> pip-name mismatches.
_IMPORT_ALIASES = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "bs4": "beautifulsoup4",
    "git": "gitpython",
    "dotenv": "python-dotenv",
}

_SUBPROCESS_TIMEOUT = 60


def _clean_requirements(lines) -> list:
    """Keep plain requirement specifiers; drop comments, blanks, options (-e ., -r, --hash...)."""
    reqs = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        reqs.append(line)
    return reqs


def _export(command: list, tool: str) -> list | None:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT, check=False
        )
    except FileNotFoundError:
        print(f"[repo2nb] '{tool}' not found on PATH — falling back to next dependency source.")
        return None
    except subprocess.TimeoutExpired:
        print(f"[repo2nb] '{tool}' timed out — falling back to next dependency source.")
        return None
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        msg = detail[-1] if detail else f"exit code {result.returncode}"
        print(f"[repo2nb] '{tool} export' failed ({msg}) — falling back to next dependency source.")
        return None
    return _clean_requirements(result.stdout.splitlines())


def _export_poetry(repo_path: pathlib.Path) -> list | None:
    return _export(
        ["poetry", "export", "--format", "requirements.txt", "--without-hashes"],
        "poetry",
    )


def _export_uv(repo_path: pathlib.Path) -> list | None:
    return _export(
        ["uv", "export", "--format", "requirements-txt", "--no-hashes", "--no-emit-project"],
        "uv",
    )


def _from_requirements_txt(repo_path: pathlib.Path) -> list | None:
    lines = (repo_path / "requirements.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    return _clean_requirements(lines)


def _scan_imports(py_files: list, internal: set) -> list:
    stdlib = set(sys.stdlib_module_names)
    mods = set()
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    third_party = {_IMPORT_ALIASES.get(m, m) for m in mods if m not in stdlib and m not in internal}
    return sorted(third_party)


def resolve_dependencies(repo_path: pathlib.Path, tree: list) -> tuple[list | None, str]:
    """Resolve pinned dependencies locally. Returns (requirements, source); ([], source) means none needed."""
    pyproject = repo_path / "pyproject.toml"

    if (repo_path / "poetry.lock").is_file() and pyproject.is_file() and "[tool.poetry]" in pyproject.read_text(encoding="utf-8", errors="replace"):
        reqs = _export_poetry(repo_path)
        if reqs is not None:
            return reqs, "poetry.lock (via poetry export)"

    if (repo_path / "uv.lock").is_file():
        reqs = _export_uv(repo_path)
        if reqs is not None:
            return reqs, "uv.lock (via uv export)"

    if (repo_path / "requirements.txt").is_file():
        return _from_requirements_txt(repo_path), "requirements.txt"

    py_files = [f for _, files in tree for f in files if f.suffix == ".py"]
    internal = set()
    for _, files in tree:
        for f in files:
            rel = f.relative_to(repo_path)
            internal.add(rel.stem if len(rel.parts) == 1 else rel.parts[0])
    return _scan_imports(py_files, internal), "AST import scan (unpinned)"

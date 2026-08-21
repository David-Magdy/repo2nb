import json
import os
import pathlib

STATE_DIR = ".repo2nb"
MANIFEST_NAME = "manifest.json"


def load_manifest(repo_path: pathlib.Path):
    manifest_path = repo_path / STATE_DIR / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"[repo2nb] No manifest found at {manifest_path} — run a full generation first "
            f"(python -m repo2nb {repo_path})."
        )
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"[repo2nb] Manifest at {manifest_path} is corrupted ({e}) — delete it and re-run a full generation.") from e


def save_manifest(repo_path: pathlib.Path, manifest: dict):
    state_dir = repo_path / STATE_DIR
    state_dir.mkdir(exist_ok=True)
    tmp = state_dir / (MANIFEST_NAME + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    os.replace(tmp, state_dir / MANIFEST_NAME)


def ensure_gitignore_entries(repo_path: pathlib.Path, entries: list):
    """Idempotently append entries to .gitignore, logging every write to the terminal."""
    gitignore = repo_path / ".gitignore"
    existing_lines = []
    created = False
    if gitignore.is_file():
        existing_lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        created = True

    to_add = [e for e in entries if e not in existing_lines]
    if not to_add:
        return

    with open(gitignore, "a", encoding="utf-8") as f:
        if existing_lines and existing_lines[-1].strip():
            f.write("\n")
        for entry in to_add:
            f.write(entry + "\n")
            print(f"[repo2nb] Added '{entry}' to .gitignore")
    if created:
        print("[repo2nb] Created .gitignore")

import pathlib
import sys

import nbformat

from .converter import _is_binary
from .notebook import content_hash, make_writefile_cell
from .state import load_manifest, save_manifest
from .targets import get_target
from .traversal import traverse


def _current_hashes(repo_path: pathlib.Path, ignore_extra: set) -> dict:
    tree, _ = traverse(repo_path, extra_ignore=ignore_extra)
    hashes = {}
    for dir_path, files in tree:
        for f in files:
            if f.suffix.lower() == ".ipynb" or _is_binary(f):
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            hashes[f.relative_to(repo_path).as_posix()] = content_hash(content)
    return hashes


def _diff(current: dict, old: dict) -> tuple[list, list, list]:
    added = sorted(set(current) - set(old))
    deleted = sorted(set(old) - set(current))
    modified = sorted(r for r in set(current) & set(old) if current[r] != old[r])
    return added, modified, deleted


def _report(added, modified, deleted):
    for rel in added:
        print(f"  + added:    {rel}")
    for rel in modified:
        print(f"  ~ modified: {rel}")
    for rel in deleted:
        print(f"  - deleted:  {rel}")
    if not (added or modified or deleted):
        print("  (no changes — notebook already up to date)")


def sync(repo_path: pathlib.Path, notebook_path: pathlib.Path = None, dry_run: bool = False,
         ignore_extra: set = None):
    manifest = load_manifest(repo_path)

    target = get_target(manifest.get("target", "kaggle"))
    nb_path = pathlib.Path(notebook_path or manifest.get("notebook", ""))
    if not nb_path.is_file():
        sys.exit(f"[repo2nb] Target notebook '{nb_path}' not found. Pass --notebook PATH.")

    current = _current_hashes(repo_path, set(ignore_extra or manifest.get("ignore_extra") or []))
    added, modified, deleted = _diff(current, manifest.get("files", {}))

    action = "Would update" if dry_run else "Updating"
    print(f"[repo2nb] {action} {nb_path}:")
    _report(added, modified, deleted)
    if dry_run:
        print("[repo2nb] Dry run — no changes written.")
        return
    if not (added or modified or deleted):
        return

    nb = nbformat.read(str(nb_path), as_version=4)
    index = {}
    for i, cell in enumerate(nb.cells):
        tag = cell.get("metadata", {}).get("repo2nb")
        if isinstance(tag, dict) and tag.get("path"):
            index[tag["path"]] = i

    # Modified: replace source in place; Deleted: drop the cell entirely.
    for rel in modified:
        content = (repo_path / rel).read_text(encoding="utf-8")
        cell = nb.cells[index[rel]]
        new_cell = make_writefile_cell(rel, content, prefix=target.WORKDIR_PREFIX)
        cell.source = new_cell.source
        cell.metadata["repo2nb"] = new_cell.metadata["repo2nb"]
    for i in sorted((index[rel] for rel in deleted), reverse=True):
        del nb.cells[i]

    # Added: append after the last tagged file cell (no smart placement).
    insert_at = max(index.values()) + 1 if index else len(nb.cells)
    for offset, rel in enumerate(added):
        content = (repo_path / rel).read_text(encoding="utf-8")
        nb.cells.insert(insert_at + offset, make_writefile_cell(rel, content, prefix=target.WORKDIR_PREFIX))

    tmp = nb_path.with_suffix(nb_path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    tmp.replace(nb_path)

    manifest["files"] = current
    save_manifest(repo_path, manifest)
    print(f"[repo2nb] Synced {len(added) + len(modified) + len(deleted)} change(s).")

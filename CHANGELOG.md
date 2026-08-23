# Changelog

## 0.2.1 — 2026-08-23

Hot-fix release on top of 0.2.0.

### Fixed
- **`reverse` hardened against symlink-based path traversal.** Each write target is now canonicalized against the real filesystem at write time and rejected if it resolves outside the destination root — including escapes through a symlinked subdirectory or file planted inside `--output` (previously reachable under `--force`). Symlink loops are skipped gracefully with a warning instead of crashing. Regression-tested for all three cases.

### Changed
- Project renamed to **repo2nb CLI** (PyPI package and repo name unchanged).
- Documentation reorganized: README is now a quick-start overview; full command details moved to `TUTORIAL.md`, plus new `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md`.
- README badges added: license, release, Made-with-Python, PyPI downloads/month.

## 0.2.0

Seven features, all backward-compatible with the existing `python -m repo2nb ./my_project` invocation.

### Added
- **`.repo2nbignore` support**, optional gitignore-syntax file (globs + `!` negation, via `pathspec`) to exclude files from the generated notebook. Applied after the built-in defaults and `--ignore-extra`, so its negations override both. Malformed lines are skipped with a warning. repo2nb still never reads your real `.gitignore`.
- **Dependency auto-detection**, resolves dependencies locally at generation time: `poetry export` → `uv export` → `requirements.txt` → AST import scan (unpinned). Output is always a plain `%pip install` cell; poetry/uv are optional local tools, never required on Kaggle/Colab. Disable with `--no-deps`.
- **Reverse mode (`repo2nb reverse <notebook>`)**, reconstruct the local file tree from a generated notebook ("nb2repo"). Validates cell-metadata paths against directory traversal, refuses non-empty output dirs without `--force`, tolerates deleted cells.
- **Incremental sync (`repo2nb sync <repo>`)**, one-directional (repo → notebook) incremental update: added files get appended cells, modified files updated in place, deleted files removed entirely. `--dry-run` previews changes; state lives in `.repo2nb/manifest.json`, written atomically only after a successful notebook write.
- **Colab target (`--target colab`)**, auth cell uses `google.colab.userdata.get` with a Colab-specific secrets tutorial written against Colab's actual UI. Colab's auto-generated `sample_data/` directory is added to `.gitignore` (just like `.virtual_documents/` for Kaggle). Drive mounting intentionally not included.
- **Hidden/collapsed setup cells**, injected setup cells grouped under a `## 🔧 repo2nb setup (safe to collapse)` header with best-effort per-platform collapse metadata (`jupyter.source_hidden` / Colab `cellView: form`). Cells always still run on Run All.
- Every generated file cell is now tagged in cell metadata (`repo2nb.path` / `hash` / `generated_by`), the foundation for reverse and sync.

### Changed
- The in-notebook security/gitignore warning cell has been **removed**; `.gitignore` updates (`.virtual_documents/`, `.repo2nb/`) now happen automatically at generation time and are logged to the terminal instead.
- Generation writes `.repo2nb/manifest.json` for sync and auto-adds it to `.gitignore`, along with the target platform's system directories (`.virtual_documents/` for Kaggle, `sample_data/` for Colab).
- Minimum Python version bumped to 3.10 (uses `sys.stdlib_module_names`).
- `click` dependency replaced by stdlib `argparse`; new required dependency: `pathspec`.

### Fixed
- Repeated generations no longer duplicate `.gitignore` entries.

# TUTORIAL.md — repo2nb in depth

Everything the [README](README.md) didn't bore you with: every flag, every subcommand, every convention.

## Table of contents

- [Converting a repo (`convert`, the default command)](#converting-a-repo)
- [Dependency auto-detection](#dependency-auto-detection)
- [`.repo2nbignore`](#repo2nbignore)
- [Reverse mode (`reverse`) — nb2repo](#reverse-mode-reverse--nb2repo)
- [Incremental sync (`sync`)](#incremental-sync-sync)
- [Colab support](#colab-support)
- [Setup cells & collapsing](#setup-cells--collapsing)
- [Conventions & gotchas](#conventions--gotchas)

---

## Converting a repo

```bash
python -m repo2nb ./my_project --output my_project_kaggle.ipynb
```

Then upload the resulting `.ipynb` to Kaggle (File → Import Notebook) or Colab.

### All options

| Option | What it does | Default |
|---|---|---|
| `--output`, `-o` | Output `.ipynb` path | `<folder_name>.ipynb` |
| `--target {kaggle,colab}` | Target platform | `kaggle` |
| `--omit-instructions` | Omits warning cells and instructional cheat sheets | off |
| `--ignore-extra ".ext ..."` | Extra file extensions to ignore completely (comma or space separated) | — |
| `--include ".ext ..."` | Force include extensions usually skipped as binary/data | — |
| `--no-deps` | Skip dependency auto-detection and the `%pip install` cell | off |
| `--version` | Print version | — |

### What the generated notebook looks like

1. **Usage instruction** (unless `--omit-instructions`)
2. **🔧 repo2nb setup** — git auth cells (if your repo has a `.git` dir), `%pip install` cell (if dependencies were detected), all under one collapsible header
3. **📂 Phase 2: Repository Construction** — your file tree as `%%writefile` cells
4. **🚀 Phase 3: Your Workspace** — git pull/push cells and the cheat sheet

Every file cell carries hidden metadata (`repo2nb.path`, `hash`) — that's what powers [`reverse`](#reverse-mode-reverse----nb2repo) and [`sync`](#incremental-sync-sync).

## Dependency auto-detection

By default, repo2nb figures out your project's dependencies **locally, at generation time**, and writes one plain `%pip install` cell into the notebook. Resolution order (first available wins):

1. `poetry.lock` (+ `[tool.poetry]` in `pyproject.toml`) → runs `poetry export` locally
2. `uv.lock` → runs `uv export` locally
3. `requirements.txt` → read directly (local/editable installs like `-e .` are stripped)
4. No lockfile → AST scan of your included `.py` files: third-party imports are collected (stdlib and your own modules excluded) and installed **unpinned**

Poetry and uv never need to exist on Kaggle/Colab — they only run on your machine, and only if the matching lockfile is present. If poetry/uv aren't installed locally, repo2nb falls through the chain automatically and tells you what it did.

Pass `--no-deps` to manage installs yourself.

Common import-name → pip-name mismatches (`cv2` → `opencv-python`, `sklearn` → `scikit-learn`, `yaml` → `pyyaml`, …) are handled in the AST path.

## `.repo2nbignore`

Create an optional `.repo2nbignore` file at your repo root to exclude files from the generated notebook using gitignore syntax (globs and `!` negation, powered by [`pathspec`](https://github.com/cpburnz/python-pathspec)):

```
# .repo2nbignore
*.yaml
!config.yaml
data/experiment_42.csv
```

**Precedence** (later layers override earlier ones):

1. Built-in smart-filter defaults (`.venv`, lockfiles, heavy binaries, …)
2. `--ignore-extra` CLI flag
3. `.repo2nbignore`, in file order — so `!config.yaml` above can un-ignore a file caught by any earlier rule

Note the difference to the flags: `--ignore-extra` / `--include` work at the *extension* level across the whole repo, while `.repo2nbignore` patterns can target individual paths. Malformed lines are skipped with a terminal warning instead of failing the run.

> repo2nb deliberately does **not** read your real `.gitignore` — files get gitignored for reasons unrelated to what a training run needs at runtime (a local `.env`, machine-specific configs).

## Reverse mode (`reverse`) — nb2repo

Made edits on Kaggle/Colab and want them back on your machine? Every file cell repo2nb generates is tagged with its repo path in cell metadata, so you can reconstruct the tree from any generated notebook:

```bash
python -m repo2nb reverse my_project_kaggle.ipynb --output restored_project
```

Behavior:

- Refuses to write into a non-empty directory unless you pass `--force`
- Paths in metadata are validated against directory traversal before anything is written (a hand-edited/corrupted notebook can't write outside `--output`)
- Cells you deleted on the platform are simply omitted from the reconstruction
- Works regardless of how deeply nested your repo is (depth is encoded in each cell's metadata path, not in markdown structure)
- Default output directory: `<notebook name>` without extension

This is a plain "extract to folder" step — review the result with `git diff` yourself afterwards. Notebooks heavily hand-edited outside repo2nb's own cells may not reconstruct perfectly.

## Incremental sync (`sync`)

Re-running full generation after every small change is wasteful. `sync` updates an existing notebook in place:

```bash
python -m repo2nb sync ./my_project            # uses the notebook recorded at last generation
python -m repo2nb sync ./my_project --dry-run  # preview changes without touching anything
python -m repo2nb sync ./my_project --notebook other.ipynb
```

How changes are applied:

- **Added** files get a new tagged cell appended after the last file cell (no import-order-smart placement — reorder manually if you care)
- **Modified** files are updated in place, keeping their position
- **Deleted** files have their cells removed entirely (a warning nobody reads is worse than removal)
- Cells you added manually are left untouched

> ⚠️ **Sync is strictly one-directional: local repo → notebook.** It is not a merge tool. If you made edits on Kaggle that you want to keep, run `reverse` first to bring them back into your local repo, then `sync`.

State lives in `.repo2nb/manifest.json` (auto-created at generation, auto-added to your `.gitignore`). Don't edit it; delete it if it gets corrupted, then re-run a full generation. The manifest is written atomically only after the notebook write succeeds, so a crash never leaves it half-updated.

### The recommended round-trip workflow

```bash
# 1. Local: generate and upload
python -m repo2nb ./my_project -o my_project_kaggle.ipynb

# 2. On Kaggle: Run All once, work, push commits via the git cells

# 3a. Local-only changes: incremental update of the notebook
python -m repo2nb sync ./my_project --dry-run   # preview
python -m repo2nb sync ./my_project             # apply

# 3b. Platform-side edits you want to keep: reverse first, THEN sync
python -m repo2nb reverse my_project_kaggle.ipynb -o restored
# merge restored/ into my_project/, commit, then sync as above
```

## Colab support

Pass `--target colab` to generate a notebook for Google Colab instead of Kaggle:

```bash
python -m repo2nb ./my_project --target colab -o my_project_colab.ipynb
```

The auth cell uses Colab's native secrets API (`google.colab.userdata.get`) instead of Kaggle Secrets. To set up your GitHub token in Colab:

1. Click the **key icon (Secrets)** in the left sidebar
2. Click **+ Add new secret**
3. Name it exactly: `GITHUB_TOKEN`
4. Paste your GitHub fine-grained personal access token as the value
5. Toggle **Notebook access** on for this secret

Colab's auto-generated `sample_data/` directory is automatically added to your `.gitignore` (the same way `.virtual_documents/` is for Kaggle), so it never lands in a push from a Colab session.

Drive mounting is intentionally not included — it's not needed for the core convert/run/push loop.

## Setup cells & collapsing

repo2nb-injected setup cells (git auth, pip install) sit under a clearly labeled `## 🔧 repo2nb setup (safe to collapse)` header and carry best-effort collapse metadata per platform. **Collapse behavior is a viewer feature — no `.ipynb` metadata can guarantee hiding everywhere.** Hidden cells always still run on "Run All".

| Platform | Collapse metadata respected? |
|---|---|
| JupyterLab / VS Code | yes (`jupyter.source_hidden`) |
| Kaggle editor | unverified — label is the fallback |
| Colab | form-style rendering via `cellView: form` |
| GitHub renderer / nbviewer | no — the visible label is the fallback |

Since secrets are injected at runtime by the platform's secrets manager and never written into cell source, this is purely cosmetic — nothing sensitive is exposed either way. See [SECURITY.md](SECURITY.md).

## Conventions & gotchas

**Run All only once:** when you first start your platform session, use **"Run All"** to bootstrap the directory structure and recreate the files. After the initial setup, run cells individually as needed — re-running everything may overwrite manual code changes made that session!

**Branch management:** the notebook's git hooks default to `main`. Swap `"main"` for your target branch name in the `git pull` / `git push` cells if you work on a different branch.

**CLI gotcha:** a local folder literally named `sync` or `reverse` will be parsed as the subcommand in `python -m repo2nb sync`. Use a path prefix (`python -m repo2nb ./sync`) to disambiguate.

**What lands in your `.gitignore`:** repo2nb auto-adds its state dir (`.repo2nb/`), plus the platform's system dirs (`.virtual_documents/` for Kaggle targets, `sample_data/` for Colab). Every change is logged to the terminal; nothing is ever appended twice.

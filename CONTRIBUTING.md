# Contributing to repo2nb

Thanks for helping out! repo2nb is a small tool with a deliberate philosophy: **lightweight, dependency-free, and boring where it counts.** Keep that in mind when adding code.

## Development setup

```bash
git clone https://github.com/David-Magdy/repo2nb.git
cd repo2nb

# with uv (recommended, the project ships a lockfile)
uv sync

# or plain pip
python -m venv .venv && source .venv/bin/activate
pip install -e . --group dev
```

Requires Python 3.10+.

## Running the checks

```bash
pytest          # full test suite
ruff check .    # linting. must be clean
```

Both must pass before any PR is merged.

## Project layout

```
repo2nb/
├── cli.py          # argparse entry point + manual subcommand dispatch
├── converter.py    # the convert pipeline (cells, manifest, gitignore)
├── traversal.py    # file walking + pathspec filtering (.repo2nbignore)
├── notebook.py     # cell builders + repo2nb cell/notebook metadata
├── deps.py         # poetry → uv → requirements.txt → AST resolution chain
├── reverse.py      # notebook → files extraction
├── sync.py         # incremental notebook updates
├── state.py        # .repo2nb/manifest.json + gitignore writes
├── warnings.py     # in-notebook instruction cells
└── targets/
    ├── kaggle.py   # platform-specific cells (default target)
    └── colab.py    # platform-specific cells
tests/              # pytest suite + golden snapshots (tests/golden/)
```

## Ground rules

- **Don't break the default invocation.** `python -m repo2nb ./my_project` is a compatibility surface; changes to its output need explicit justification.
- **The notebook is not a log.** Process messages (gitignore writes, dependency sources, skipped files) belong in terminal output, not in generated cells.
- **Never put secrets in cells.** Platform secrets managers inject at runtime; see [SECURITY.md](SECURITY.md).
- **Identify generated cells by metadata**, never by markdown structure or cell order.
- **Degrade gracefully.** Malformed input should produce a clear message and a fallback, not a stack trace.
- New dependencies need a strong reason. Stdlib first.

## Testing expectations

- Every bug fix gets a regression test that fails without the fix.
- New features need tests covering the happy path and at least one graceful-failure path.
- If you change generated-notebook output intentionally, regenerate `tests/golden/kaggle_default.json` (run the converter on the fixture from `test_golden.py`) and say so in the PR.

## Submitting

1. Fork / branch off `main`
2. Make your change with tests
3. Run `pytest` and `ruff check .`
4. Open a PR describing what changed and why. Link any related issues

For bugs and feature discussion before coding, start with an [issue](https://github.com/David-Magdy/repo2nb/issues).

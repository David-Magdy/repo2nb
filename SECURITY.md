# Security Policy

repo2nb's core promise: **your credentials never end up inside the generated notebook.**

## How repo2nb handles secrets

- Your GitHub token is **never hardcoded** into any cell. The generated auth cell fetches it at runtime from the platform's native secrets manager — Kaggle Secrets (`kaggle_secrets.UserSecretsClient`) or Colab (`google.colab.userdata.get`).
- Because injection happens at runtime on the platform, a generated notebook is safe to share publicly: it contains no token material.
- Setup cells carry best-effort *collapse* metadata, but this is cosmetic only — hiding is never part of the security model.

## What repo2nb writes to your machine

- `.gitignore` entries: its own state dir (`.repo2nb/`) and the target platform's system dirs (`.virtual_documents/`, `sample_data/`). Every write is logged to the terminal; nothing is duplicated.
- `.repo2nb/manifest.json`: file paths + SHA-256 content hashes used by `sync`. Contains no secrets and no file contents.
- Generated notebooks: your source files (that's the point) plus per-cell metadata (`path`, content hash, generator version). Nothing else.

If you keep secrets in files inside your repo, they will be embedded in the notebook like any other included file — exclude them with `.repo2nbignore`. Note that repo2nb deliberately does not read your real `.gitignore` for filtering.

## Path safety

`reverse` treats notebook cell metadata as untrusted input: every extracted path is validated to stay inside the output directory before anything is written, so a corrupted or hand-edited notebook cannot traverse outside `--output`.

## Supported versions

| Version | Supported |
|---|---|
| 0.2.x | yes |
| < 0.2 | no |

## Reporting a vulnerability

Please do **not** open a public issue for security reports. Use GitHub's private vulnerability reporting: **Security → Report a vulnerability** on the [repository](https://github.com/David-Magdy/repo2nb/security), or contact the maintainer directly if you prefer.

Include a description, reproduction steps, and the affected version (`python -m repo2nb --version`). You'll get an acknowledgment as soon as the report is triaged.

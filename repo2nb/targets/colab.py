import nbformat.v4 as nbf

from .kaggle import _get_remote_url

NAME = "colab"
WORKDIR_PREFIX = "/content/"
# Colab seeds every session with a sample_data/ directory — never push it.
GITIGNORE_ENTRIES = ["sample_data/"]


def collapse_metadata() -> dict:
    # ponytail: best-effort hide; not all viewers respect cellView — see README compatibility table
    return {"cellView": "form"}


def auth_cells(repo_path, omit_instructions: bool = False) -> list:
    remote_suffix = _get_remote_url(repo_path)

    if omit_instructions:
        setup_md_text = "# 🛠️ Phase 1: Git Authentication & Setup"
    else:
        setup_md_text = (
            "# 🛠️ Phase 1: Git Authentication & Setup\n"
            "---\n"
            "## 🔑 GitHub Token Setup (Colab Secrets)\n\n"
            "Before running this cell:\n"
            "1. In Colab, click the **key icon (Secrets)** in the left sidebar\n"
            "2. Click **+ Add new secret**\n"
            "3. Name it exactly: `GITHUB_TOKEN`\n"
            "4. Paste your GitHub **fine-grained personal access token** as the value\n"
            "   - Scope it to your repo only with **Contents: Read and Write** permission\n"
            "5. Toggle **Notebook access** on for this secret\n"
            "6. Then run this cell — your token will never appear in any output\n\n"
            "---\n"
            "**Working on a different branch?** Change `main` to your target branch name in the `git pull` and `git push` cells below."
        )
    setup_md = nbf.new_markdown_cell(setup_md_text)

    config_code = '!git config --global user.name "YOUR NAME"\n!git config --global user.email "YOUR EMAIL"'
    config_cell = nbf.new_code_cell(config_code)

    remote_code = (
        'from google.colab import userdata\n'
        'import subprocess\n'
        'import os\n\n'
        '# Fetch your Colab Secret (relies on Colab Secrets instead of raw YOUR_TOKEN)\n'
        'token = userdata.get("GITHUB_TOKEN")\n'
        f'remote_url = f"https://{{token}}@github.com/{remote_suffix}"\n\n'
        'subprocess.run(["git", "init"], check=True)\n'
        'subprocess.run(["git", "branch", "-m", "main"], check=True)\n\n'
        'try:\n'
        '    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True, stderr=subprocess.DEVNULL)\n'
        'except subprocess.CalledProcessError:\n'
        '    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)\n\n'
        'print("Remote URL configured successfully. Token was not printed for security.")'
    )
    remote_cell = nbf.new_code_cell(remote_code)

    pull_code = '# Change "main" to your branch name if needed\n!git pull origin main'
    pull_cell = nbf.new_code_cell(pull_code)

    return [setup_md, config_cell, remote_cell, pull_cell]


def workspace_cells(omit_instructions: bool = False) -> list:
    push_code = (
        '# Un-comment the lines below when you are ready to push!\n'
        '# !git add .\n'
        '# !git commit -m "fix from colab session"\n'
        '# !git push origin main'
    )
    push_cell = nbf.new_code_cell(push_code)

    if omit_instructions:
        return [nbf.new_markdown_cell("# 🚀 Phase 3: Your Workspace"), push_cell]

    cheat_sheet_md = nbf.new_markdown_cell(
        "# 🚀 Phase 3: Your Workspace\n"
        "---\n"
        "### <span style='color: #2e7d32;'>**Start manipulating and running your code from here onwards!**</span>\n\n"
        "## Git Cheat Sheet\n"
        "Uncomment the cell below when you are ready to push. Other useful commands:\n"
        "- **Remove a file**: `!git rm path/to/file.ext`\n"
        "- **Remove a folder**: `!git rm -rf path/to/folder`\n"
        "- **Rename a file**: `!git mv old_name.ext new_name.ext`\n"
        "- **Check status**: `!git status`"
    )
    return [cheat_sheet_md, push_cell]

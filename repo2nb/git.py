import pathlib
import nbformat.v4 as nbf

def _get_remote_url(repo_path: pathlib.Path) -> str:
    config_path = repo_path / ".git" / "config"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                in_origin = False
                for line in content.splitlines():
                    line = line.strip()
                    if line == '[remote "origin"]':
                        in_origin = True
                    elif line.startswith('[') and in_origin:
                        in_origin = False
                    elif in_origin and line.startswith('url ='):
                        url = line.split('=', 1)[1].strip()
                        if "github.com" in url:
                            suffix = url.split("github.com")[-1].lstrip(":/").rstrip("/")
                            if suffix.endswith(".git"):
                                return suffix
                            return suffix + ".git"
                        return url
        except Exception:
            pass
    return "user/repo.git"

def get_git_cells(repo_path: pathlib.Path, omit_instructions: bool = False):
    remote_suffix = _get_remote_url(repo_path)
    
    if omit_instructions:
        setup_md_text = "# 🛠️ Phase 1: Git Authentication & Setup"
    else:
        setup_md_text = (
            "# 🛠️ Phase 1: Git Authentication & Setup\n"
            "---\n"
            "Fill in your credentials.\n\n"
            "**Working on a different branch?** Change `main` to your target branch name in the `git pull` and `git push` cells below."
        )
    setup_md = nbf.new_markdown_cell(setup_md_text)
    
    config_code = '!git config --global user.name "YOUR NAME"\n!git config --global user.email "YOUR EMAIL"'
    config_cell = nbf.new_code_cell(config_code)
    
    remote_code = f'%%bash\ngit init\ngit branch -m main\ngit remote add origin "https://YOUR_TOKEN@github.com/{remote_suffix}" 2>/dev/null || git remote set-url origin "https://YOUR_TOKEN@github.com/{remote_suffix}"'
    remote_cell = nbf.new_code_cell(remote_code)
    
    pull_code = '# Change "main" to your branch name if needed\n!git pull origin main'
    pull_cell = nbf.new_code_cell(pull_code)
    
    setup_cells = [setup_md, config_cell, remote_cell, pull_cell]
    
    push_code = (
        '# Un-comment the lines below when you are ready to push!\n'
        '# !git add .\n'
        '# !git commit -m "fix from kaggle session"\n'
        '# !git push origin main'
    )
    push_cell = nbf.new_code_cell(push_code)
    
    if omit_instructions:
        push_cells = [nbf.new_markdown_cell("# 🚀 Phase 3: Your Workspace"), push_cell]
    else:
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
        push_cells = [cheat_sheet_md, push_cell]
        
    return setup_cells, push_cells

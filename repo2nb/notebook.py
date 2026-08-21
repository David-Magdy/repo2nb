import hashlib
from datetime import datetime, timezone

import nbformat
import nbformat.v4 as nbf

from . import __version__


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_markdown_cell(text: str) -> nbformat.NotebookNode:
    return nbf.new_markdown_cell(text)


def make_code_cell(code: str) -> nbformat.NotebookNode:
    return nbf.new_code_cell(code)


def make_writefile_cell(filepath: str, content: str, prefix: str = "/kaggle/working/") -> nbformat.NotebookNode:
    code = f"%%writefile {prefix}{filepath}\n{content}"
    cell = make_code_cell(code)
    cell.metadata["repo2nb"] = {
        "path": filepath,
        "hash": content_hash(content),
        "generated_by": __version__,
    }
    return cell


def make_pip_cell(requirements: list) -> nbformat.NotebookNode:
    return make_code_cell("%pip install -q " + " ".join(requirements))


def assemble_notebook(cells: list, target: str = "kaggle") -> nbformat.NotebookNode:
    nb = nbf.new_notebook()
    nb.cells = cells
    nb.metadata["repo2nb"] = {
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
    }
    return nb

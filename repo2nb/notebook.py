import nbformat.v4 as nbf
import nbformat

def make_markdown_cell(text: str) -> nbformat.NotebookNode:
    return nbf.new_markdown_cell(text)

def make_code_cell(code: str) -> nbformat.NotebookNode:
    return nbf.new_code_cell(code)

def make_writefile_cell(filepath: str, content: str) -> nbformat.NotebookNode:
    code = f"%%writefile /kaggle/working/{filepath}\n{content}"
    return make_code_cell(code)

def assemble_notebook(cells: list) -> nbformat.NotebookNode:
    nb = nbf.new_notebook()
    nb.cells = cells
    return nb

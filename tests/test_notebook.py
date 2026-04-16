from repo2nb.notebook import make_writefile_cell, assemble_notebook, make_markdown_cell

def test_make_writefile_cell():
    cell = make_writefile_cell("my_project/test.py", "print('hello')")
    assert cell.cell_type == "code"
    assert cell.source.startswith("%%writefile /kaggle/working/my_project/test.py\nprint('hello')")

def test_assemble_notebook():
    cells = [make_markdown_cell("Test")]
    nb = assemble_notebook(cells)
    
    assert nb.nbformat == 4
    assert len(nb.cells) == 1
    assert nb.cells[0].source == "Test"

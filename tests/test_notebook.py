from repo2nb.notebook import (
    assemble_notebook,
    content_hash,
    make_markdown_cell,
    make_pip_cell,
    make_writefile_cell,
)


def test_make_writefile_cell():
    cell = make_writefile_cell("my_project/test.py", "print('hello')")
    assert cell.cell_type == "code"
    assert cell.source.startswith("%%writefile /kaggle/working/my_project/test.py\nprint('hello')")


def test_make_writefile_cell_metadata_tag():
    cell = make_writefile_cell("src/model.py", "print('hi')")
    tag = cell.metadata["repo2nb"]
    assert tag["path"] == "src/model.py"
    assert tag["hash"] == content_hash("print('hi')")
    assert tag["hash"].startswith("sha256:")
    assert tag["generated_by"]


def test_make_writefile_cell_custom_prefix():
    cell = make_writefile_cell("a.py", "x", prefix="/content/")
    assert cell.source.startswith("%%writefile /content/a.py\nx")


def test_content_hash_deterministic():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abd")


def test_make_pip_cell():
    cell = make_pip_cell(["numpy", "pandas"])
    assert cell.source == "%pip install -q numpy pandas"


def test_assemble_notebook_metadata():
    nb = assemble_notebook([make_markdown_cell("Test")], target="colab")
    assert nb.nbformat == 4
    assert len(nb.cells) == 1
    meta = nb.metadata["repo2nb"]
    assert meta["target"] == "colab"
    assert meta["version"]
    assert meta["generated_at"]

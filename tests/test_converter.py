import nbformat
from repo2nb.converter import convert

def test_converter_no_git(tmp_path):
    repo_path = tmp_path / "my_project"
    repo_path.mkdir()
    (repo_path / "test.py").write_text("print('hello')")
    
    output_path = tmp_path / "out.ipynb"
    convert(repo_path, output_path)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        nb = nbformat.read(f, as_version=4)
        
    cells = nb.cells
    assert len(cells) == 6
    
    header_cell = cells[3]
    assert header_cell.cell_type == "markdown"
    assert header_cell.source == "# 📁 my_project"
    
    file_title_cell = cells[4]
    assert file_title_cell.cell_type == "markdown"
    assert "test.py" in file_title_cell.source
    
    code_cell = cells[5]
    assert code_cell.cell_type == "code"
    assert "%%writefile" in code_cell.source
    assert "/kaggle/working/test.py" in code_cell.source

def test_converter_depth(tmp_path):
    repo_path = tmp_path / "my_project"
    repo_path.mkdir()
    (repo_path / "test0.py").touch()
    
    sub_dir = repo_path / "level1"
    sub_dir.mkdir()
    (sub_dir / "test1.py").touch()
    
    sub_sub_dir = sub_dir / "level2"
    sub_sub_dir.mkdir()
    (sub_sub_dir / "test2.py").touch()
    
    output_path = tmp_path / "out.ipynb"
    convert(repo_path, output_path)
    
    with open(output_path, "r") as f:
        nb = nbformat.read(f, as_version=4)
        
    markdown_sources = [c.source for c in nb.cells if c.cell_type == "markdown"]
    assert "# 📁 my_project" in markdown_sources
    assert "## 📁 level1" in markdown_sources
    assert "### 📁 level2" in markdown_sources


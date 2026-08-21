import nbformat

from repo2nb.converter import convert


def _make_repo(tmp_path):
    repo_path = tmp_path / "my_project"
    repo_path.mkdir()
    (repo_path / "test.py").write_text("print('hello')")
    return repo_path


def test_converter_no_git(tmp_path):
    repo_path = _make_repo(tmp_path)
    output_path = tmp_path / "out.ipynb"

    convert(repo_path, output_path)

    assert output_path.exists()
    nb = nbformat.read(str(output_path), as_version=4)
    cells = nb.cells

    # usage cell, phase2 header, folder header, .gitignore (auto-created) + test.py with titles
    writefile_cells = [c for c in cells if "repo2nb" in c.metadata]
    assert [c.metadata["repo2nb"]["path"] for c in writefile_cells] == [".gitignore", "test.py"]
    assert "/kaggle/working/test.py" in writefile_cells[1].source

    # no gitignore warning cell in the notebook anymore (moved to terminal logging)
    for cell in cells:
        assert "SECURITY & PUBLISHING WARNING" not in cell.source


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

    nb = nbformat.read(str(output_path), as_version=4)
    markdown_sources = [c.source for c in nb.cells if c.cell_type == "markdown"]
    assert "# 📁 my_project" in markdown_sources
    assert "## 📁 level1" in markdown_sources
    assert "### 📁 level2" in markdown_sources


def test_converter_writes_manifest_and_gitignore(tmp_path):
    repo_path = _make_repo(tmp_path)

    convert(repo_path, tmp_path / "out.ipynb")

    manifest_path = repo_path / ".repo2nb" / "manifest.json"
    assert manifest_path.exists()
    gitignore = repo_path / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text()
    assert ".virtual_documents/" in content
    assert ".repo2nb/" in content
    assert "sample_data" not in content


def test_converter_colab_gitignore_targets_sample_data(tmp_path):
    repo_path = _make_repo(tmp_path)

    convert(repo_path, tmp_path / "out.ipynb", target_name="colab")

    content = (repo_path / ".gitignore").read_text()
    assert "sample_data/" in content
    assert ".repo2nb/" in content
    assert ".virtual_documents" not in content


def test_converter_target_colab(tmp_path):
    repo_path = _make_repo(tmp_path)

    convert(repo_path, tmp_path / "out.ipynb", target_name="colab")

    nb = nbformat.read(str(tmp_path / "out.ipynb"), as_version=4)
    writefile_cells = [c for c in nb.cells if "repo2nb" in c.metadata]
    assert any("/content/test.py" in c.source for c in writefile_cells)
    assert nb.metadata["repo2nb"]["target"] == "colab"


def test_converter_setup_section_collapsed(tmp_path):
    repo_path = tmp_path / "proj"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    (repo_path / "a.py").write_text("import numpy\nx = 1")

    convert(repo_path, tmp_path / "out.ipynb")

    nb = nbformat.read(str(tmp_path / "out.ipynb"), as_version=4)
    sources = [c.source for c in nb.cells]
    assert any("repo2nb setup (safe to collapse)" in s for s in sources)
    pip_cells = [c for c in nb.cells if c.source.startswith("%pip install")]
    assert len(pip_cells) == 1
    assert "numpy" in pip_cells[0].source
    # setup code cells carry collapse metadata and still run on Run All
    assert pip_cells[0].metadata.get("jupyter", {}).get("source_hidden") is True


def test_converter_no_deps_flag(tmp_path):
    repo_path = tmp_path / "proj"
    repo_path.mkdir()
    (repo_path / "a.py").write_text("import numpy")

    convert(repo_path, tmp_path / "out.ipynb", deps=False)

    nb = nbformat.read(str(tmp_path / "out.ipynb"), as_version=4)
    assert not [c for c in nb.cells if "%pip install" in c.source]

import json

import nbformat
import nbformat.v4 as nbf
import pytest

from repo2nb.converter import convert
from repo2nb.sync import sync


def _make_repo(tmp_path):
    repo = tmp_path / "proj"
    (repo / "src").mkdir(parents=True)
    (repo / "main.py").write_text("print('v1')\n")
    (repo / "src" / "util.py").write_text("util = 1\n")
    return repo


def _generate(repo, tmp_path):
    nb_path = tmp_path / "out.ipynb"
    convert(repo, nb_path)
    return nb_path


def _tagged_paths(nb_path):
    nb = nbformat.read(str(nb_path), as_version=4)
    return [c.metadata["repo2nb"]["path"] for c in nb.cells if "repo2nb" in c.metadata]


def _find_cell(nb, rel):
    return next(c for c in nb.cells if c.get("metadata", {}).get("repo2nb", {}).get("path") == rel)


def test_sync_no_changes(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)

    sync(repo, notebook_path=nb_path)

    assert "no changes" in capsys.readouterr().out
    # .gitignore is auto-created by generation and included like any other file
    assert _tagged_paths(nb_path) == [".gitignore", "main.py", "src/util.py"]


def test_sync_added_file_appended_after_last_tagged_cell(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)
    (repo / "new_mod.py").write_text("new = 1\n")

    sync(repo, notebook_path=nb_path)

    paths = _tagged_paths(nb_path)
    assert paths == [".gitignore", "main.py", "src/util.py", "new_mod.py"]
    nb = nbformat.read(str(nb_path), as_version=4)
    new_cell = nb.cells[-1]
    assert "%%writefile" in new_cell.source and "new = 1" in new_cell.source


def test_sync_modified_file_keeps_position_and_id(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)
    nb_before = nbformat.read(str(nb_path), as_version=4)
    target_idx = next(i for i, c in enumerate(nb_before.cells) if "repo2nb" in c.metadata and c.metadata["repo2nb"]["path"] == "main.py")
    cell_id = nb_before.cells[target_idx].get("id")
    old_source = nb_before.cells[target_idx].source

    (repo / "main.py").write_text("print('v2 — changed')\n")
    sync(repo, notebook_path=nb_path)

    nb_after = nbformat.read(str(nb_path), as_version=4)
    assert nb_after.cells[target_idx].source != old_source
    assert "v2 — changed" in nb_after.cells[target_idx].source
    assert nb_after.cells[target_idx].metadata["repo2nb"]["path"] == "main.py"
    if cell_id:
        assert nb_after.cells[target_idx].get("id") == cell_id


def test_sync_deleted_file_removes_cell(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)
    (repo / "src" / "util.py").unlink()

    sync(repo, notebook_path=nb_path)

    paths = _tagged_paths(nb_path)
    assert "src/util.py" not in paths
    nb = nbformat.read(str(nb_path), as_version=4)
    # the writefile cell is gone entirely, not just flagged
    assert not any("repo2nb" in c.metadata and c.metadata["repo2nb"]["path"] == "src/util.py" for c in nb.cells)


def test_sync_dry_run_touches_nothing(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)
    before = nbformat.read(str(nb_path), as_version=4)
    manifest_before = (repo / ".repo2nb" / "manifest.json").read_text()

    (repo / "main.py").write_text("print('edited')\n")
    (repo / "extra.py").write_text("x\n")

    sync(repo, notebook_path=nb_path, dry_run=True)

    after = nbformat.read(str(nb_path), as_version=4)
    assert [c.source for c in after.cells] == [c.source for c in before.cells]
    assert (repo / ".repo2nb" / "manifest.json").read_text() == manifest_before
    assert not list(tmp_path.glob("*.tmp"))


def test_sync_leaves_manual_cells_untouched(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)

    nb = nbformat.read(str(nb_path), as_version=4)
    manual = nbf.new_code_cell("# my precious manual analysis\nplot_stuff()")
    nb.cells.append(manual)
    nbformat.write(nb, str(nb_path))

    (repo / "main.py").write_text("print('v2')\n")
    (repo / "brand_new.py").write_text("n=1\n")
    sync(repo, notebook_path=nb_path)

    nb_after = nbformat.read(str(nb_path), as_version=4)
    manual_cells = [c for c in nb_after.cells if "precious manual analysis" in c.source]
    assert len(manual_cells) == 1
    assert manual_cells[0].source == manual.source


def test_sync_missing_manifest_errors_clearly(tmp_path, capsys):
    repo = _make_repo(tmp_path)
    with pytest.raises(FileNotFoundError) as e:
        sync(repo, notebook_path=tmp_path / "out.ipynb")
    assert "run a full generation first" in str(e.value)


def test_sync_corrupted_manifest_errors_clearly(tmp_path):
    repo = _make_repo(tmp_path)
    _generate(repo, tmp_path)
    (repo / ".repo2nb" / "manifest.json").write_text("{not json!!")

    with pytest.raises(ValueError) as e:
        sync(repo, notebook_path=tmp_path / "out.ipynb")
    assert "corrupted" in str(e.value)


def test_sync_missing_notebook_errors(tmp_path):
    repo = _make_repo(tmp_path)
    _generate(repo, tmp_path)
    (tmp_path / "out.ipynb").unlink()

    with pytest.raises(SystemExit) as e:
        sync(repo)
    assert "--notebook" in str(e.value)


def test_sync_updates_manifest(tmp_path):
    repo = _make_repo(tmp_path)
    nb_path = _generate(repo, tmp_path)
    (repo / "new_mod.py").write_text("new = 1\n")
    (repo / "src" / "util.py").unlink()

    sync(repo, notebook_path=nb_path)

    manifest = json.loads((repo / ".repo2nb" / "manifest.json").read_text())
    assert set(manifest["files"]) == {".gitignore", "main.py", "new_mod.py"}

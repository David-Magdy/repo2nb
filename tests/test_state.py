import json

from repo2nb.state import ensure_gitignore_entries, load_manifest, save_manifest


def test_gitignore_creates_and_logs(tmp_path, capsys):
    ensure_gitignore_entries(tmp_path, [".virtual_documents/"])
    out = capsys.readouterr().out
    assert "Created .gitignore" in out
    assert "Added '.virtual_documents/' to .gitignore" in out
    assert (tmp_path / ".gitignore").read_text() == ".virtual_documents/\n"


def test_gitignore_idempotent_no_duplicates(tmp_path, capsys):
    ensure_gitignore_entries(tmp_path, [".virtual_documents/", ".repo2nb/"])
    capsys.readouterr()  # consume first-run output
    first = (tmp_path / ".gitignore").read_text()

    ensure_gitignore_entries(tmp_path, [".virtual_documents/", ".repo2nb/"])
    second = capsys.readouterr().out

    assert (tmp_path / ".gitignore").read_text() == first
    assert second == ""


def test_gitignore_partial_add_logs_only_new(tmp_path, capsys):
    (tmp_path / ".gitignore").write_text(".virtual_documents/\n")
    ensure_gitignore_entries(tmp_path, [".virtual_documents/", ".repo2nb/"])
    out = capsys.readouterr().out
    assert ".virtual_documents" not in out
    assert "Added '.repo2nb/' to .gitignore" in out


def test_manifest_roundtrip(tmp_path):
    save_manifest(tmp_path, {"files": {"a.py": "sha256:x"}})
    loaded = load_manifest(tmp_path)
    assert loaded["files"] == {"a.py": "sha256:x"}
    assert not (tmp_path / ".repo2nb" / "manifest.json.tmp").exists()


def test_load_manifest_missing(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path)


def test_load_manifest_corrupted(tmp_path):
    (tmp_path / ".repo2nb").mkdir()
    (tmp_path / ".repo2nb" / "manifest.json").write_text("{{{")
    import pytest
    with pytest.raises(ValueError):
        load_manifest(tmp_path)


def test_manifest_json_valid(tmp_path):
    save_manifest(tmp_path, {"files": {}})
    data = json.loads((tmp_path / ".repo2nb" / "manifest.json").read_text())
    assert isinstance(data, dict)

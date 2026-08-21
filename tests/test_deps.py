
from repo2nb.deps import _clean_requirements, _scan_imports, resolve_dependencies


def _tree(repo_path):
    return [(repo_path, sorted(repo_path.iterdir()))]


def test_clean_requirements_strips_options_and_editables():
    lines = ["numpy==1.0", "", "# comment", "-e .", "-r other.txt", "--hash=abc", "pandas"]
    assert _clean_requirements(lines) == ["numpy==1.0", "pandas"]


def test_scan_imports_excludes_stdlib_and_internal(tmp_path):
    (tmp_path / "mylib").mkdir()
    (tmp_path / "mylib" / "__init__.py").touch()
    (tmp_path / "main.py").write_text("import os\nimport numpy\nfrom mylib import x\nimport yaml\nimport cv2")
    (tmp_path / "mylib" / "mod.py").write_text("import PIL")

    internal = {"mylib", "main"}
    reqs = _scan_imports([tmp_path / "main.py", tmp_path / "mylib" / "mod.py"], internal)
    assert reqs == ["numpy", "opencv-python", "pillow", "pyyaml"]


def test_scan_imports_syntax_error_file_skipped(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:")
    assert _scan_imports([bad], set()) == []


def test_resolution_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text("numpy==1.26\n-e .\n# comment\nscipy\n")
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == ["numpy==1.26", "scipy"]
    assert source == "requirements.txt"


def test_fallback_when_poetry_missing(tmp_path, monkeypatch):
    """poetry.lock present but poetry not on PATH -> fall through to requirements.txt."""
    (tmp_path / "poetry.lock").touch()
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'x'\n")
    (tmp_path / "requirements.txt").write_text("requests\n")

    def boom(cmd, **kwargs):
        raise FileNotFoundError("poetry")

    monkeypatch.setattr("subprocess.run", boom)
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == ["requests"]
    assert source == "requirements.txt"


def test_uv_export_used_when_available(tmp_path, monkeypatch):
    (tmp_path / "uv.lock").touch()

    class FakeResult:
        returncode = 0
        stdout = "numpy==2.0\n"
        stderr = ""

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FakeResult()

    monkeypatch.setattr("subprocess.run", fake_run)
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == ["numpy==2.0"]
    assert "uv" in source
    assert calls[0][0] == "uv"


def test_poetry_export_used_when_available(tmp_path, monkeypatch):
    (tmp_path / "poetry.lock").touch()
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n")

    class FakeResult:
        returncode = 0
        stdout = "flask==3.0\n"
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda cmd, **kw: FakeResult())
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == ["flask==3.0"]
    assert source.startswith("poetry.lock")


def test_poetry_lock_without_tool_section_skips_poetry(tmp_path, monkeypatch):
    (tmp_path / "poetry.lock").touch()  # no [tool.poetry] in pyproject -> not a poetry project

    def boom(cmd, **kwargs):
        raise AssertionError("poetry should not be called")

    monkeypatch.setattr("subprocess.run", boom)
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert source == "AST import scan (unpinned)"


def test_ast_fallback_unpinned(tmp_path):
    (tmp_path / "app.py").write_text("import pandas as pd\nfrom sklearn.model_selection import train_test_split")
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == ["pandas", "scikit-learn"]
    assert "unpinned" in source


def test_nothing_found_returns_empty(tmp_path):
    reqs, source = resolve_dependencies(tmp_path, _tree(tmp_path))
    assert reqs == []

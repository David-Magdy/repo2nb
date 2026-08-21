

from repo2nb.traversal import load_ignore_spec, traverse


def _write_ignore(repo_path, lines):
    (repo_path / ".repo2nbignore").write_text("\n".join(lines) + "\n")


def test_default_ignore(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "test.pyc").touch()
    (tmp_path / "test.py").touch()

    tree, has_git = traverse(tmp_path)

    assert has_git is False
    assert len(tree) == 1
    names = {f.name for f in tree[0][1]}
    assert names == {"test.py"}


def test_repo2nbignore_glob_and_negation(tmp_path):
    (tmp_path / "a.yaml").touch()
    (tmp_path / "config.yaml").touch()
    (tmp_path / "keep.py").touch()
    _write_ignore(tmp_path, ["# comment", "*.yaml", "!config.yaml"])

    tree, _ = traverse(tmp_path)
    names = {f.name for f in tree[0][1]}
    assert names == {"config.yaml", "keep.py"}


def test_repo2nbignore_overrides_cli_and_defaults(tmp_path):
    # negation in .repo2nbignore un-ignores a file caught by an earlier layer
    (tmp_path / "config.yaml").touch()
    _write_ignore(tmp_path, ["!config.yaml"])

    tree, _ = traverse(tmp_path, extra_ignore={".yaml"})
    names = {f.name for f in tree[0][1]}
    assert names == {"config.yaml"}


def test_malformed_line_warns_but_does_not_crash(tmp_path, capsys):
    (tmp_path / "x.py").touch()
    _write_ignore(tmp_path, ["!"])  # bare '!' is rejected by pathspec

    tree, _ = traverse(tmp_path)

    assert tree[0][1][0].name == "x.py"
    assert "malformed" in capsys.readouterr().out


def test_no_ignore_file_same_as_before(tmp_path):
    (tmp_path / "data.yaml").touch()
    tree, _ = traverse(tmp_path)
    assert tree[0][1][0].name == "data.yaml"


def test_load_ignore_spec_extra_extensions(tmp_path):
    spec = load_ignore_spec(tmp_path, extra_ignore={".mp4", ".yaml"})
    assert spec.match_file("a/b/c.mp4")
    assert spec.match_file("x.YAML".lower()) or spec.match_file("x.yaml")


def test_deep_nesting_traversed(tmp_path):
    deep = tmp_path
    for i in range(7):
        deep = deep / f"lvl{i}"
        deep.mkdir()
    (deep / "leaf.py").touch()

    tree, _ = traverse(tmp_path)
    all_files = [f for _, files in tree for f in files]
    assert any(f.name == "leaf.py" for f in all_files)


def test_traverse_prunes_ignored_dirs(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").touch()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").touch()

    tree, has_git = traverse(tmp_path)

    assert has_git is True
    assert [d for d, _ in tree] == [tmp_path, tmp_path / "src"]

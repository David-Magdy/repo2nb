import pathlib
from repo2nb.traversal import traverse, should_ignore

def test_should_ignore():
    assert should_ignore(pathlib.Path("__pycache__"))
    assert should_ignore(pathlib.Path("node_modules"))
    assert should_ignore(pathlib.Path("test.pyc"))
    assert not should_ignore(pathlib.Path("test.py"))
    assert should_ignore(pathlib.Path(".git"))

def test_traverse_tree(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "file1.py").touch()
    
    folder1 = tmp_path / "folder1"
    folder1.mkdir()
    (folder1 / "file2.py").touch()
    
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "ignored.pyc").touch()
    
    tree, has_git = traverse(tmp_path)
    
    assert has_git is True
    assert len(tree) == 2
    
    # Root level
    assert tree[0][0] == tmp_path
    assert len(tree[0][1]) == 1
    assert tree[0][1][0].name == "file1.py"
    
    # Sub folder
    assert tree[1][0] == folder1
    assert len(tree[1][1]) == 1
    assert tree[1][1][0].name == "file2.py"

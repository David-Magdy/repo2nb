from repo2nb.git import get_git_cells, _get_remote_url

def test_git_cells(tmp_path):
    setup_cells, push_cells = get_git_cells(tmp_path)
    
    assert len(setup_cells) == 4
    assert len(push_cells) == 2
    
    config_code = setup_cells[1].source
    assert "YOUR NAME" in config_code
    assert "YOUR EMAIL" in config_code
    
    remote_code = setup_cells[2].source
    assert "YOUR_TOKEN" in remote_code
    assert "user/repo.git" in remote_code

def test_get_remote_url(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text('[remote "origin"]\n\turl = https://github.com/myuser/myrepo.git\n')
    
    url = _get_remote_url(tmp_path)
    assert url == "myuser/myrepo.git"

from repo2nb.targets import colab, kaggle


def test_kaggle_git_cells(tmp_path):
    setup_cells = kaggle.auth_cells(tmp_path)
    push_cells = kaggle.workspace_cells()

    assert len(setup_cells) == 4
    assert len(push_cells) == 2

    config_code = setup_cells[1].source
    assert "YOUR NAME" in config_code
    assert "YOUR EMAIL" in config_code

    remote_code = setup_cells[2].source
    assert "kaggle_secrets" in remote_code
    assert "user/repo.git" in remote_code


def test_get_remote_url(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text('[remote "origin"]\n\turl = https://github.com/myuser/myrepo.git\n')

    url = kaggle._get_remote_url(tmp_path)
    assert url == "myuser/myrepo.git"


def test_colab_auth_uses_colab_api(tmp_path):
    cells = colab.auth_cells(tmp_path)

    remote_code = cells[2].source
    assert "google.colab import userdata" in remote_code
    assert "userdata.get" in remote_code
    assert "kaggle_secrets" not in remote_code

    # Colab-specific tutorial, not a reworded Kaggle one
    tutorial = cells[0].source
    assert "Secrets" in tutorial and "sidebar" in tutorial.lower()
    assert "Add-ons" not in tutorial


def test_collapse_metadata():
    assert kaggle.collapse_metadata() == {"jupyter": {"source_hidden": True}}
    assert colab.collapse_metadata() == {"cellView": "form"}

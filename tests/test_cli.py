import pytest

from repo2nb.cli import _convert_parser, _reverse_parser, _sync_parser, main


def test_default_invocation_unchanged():
    """Regression gate: pre-0.2.0 invocation must parse exactly as before."""
    args = _convert_parser().parse_args(["./my_project", "--output", "x.ipynb"])
    assert str(args.repo_path) == "my_project"
    assert str(args.output) == "x.ipynb"
    assert args.target == "kaggle"
    assert args.omit_instructions is False
    assert args.ignore_extra is None
    assert args.include is None
    assert args.no_deps is False


def test_legacy_flags_still_parse():
    args = _convert_parser().parse_args(
        ["./my_project", "-o", "out.ipynb", "--omit-instructions",
         "--ignore-extra", ".mp4 .yaml", "--include", ".csv"]
    )
    assert args.omit_instructions is True
    assert set(args.ignore_extra.split()) == {".mp4", ".yaml"}
    assert args.include == ".csv"


def test_reverse_subcommand():
    args = _reverse_parser().parse_args(["nb.ipynb", "--output", "dir", "--force"])
    assert str(args.notebook_path) == "nb.ipynb"
    assert str(args.output) == "dir"
    assert args.force is True


def test_sync_subcommand():
    args = _sync_parser().parse_args(["./repo", "--notebook", "n.ipynb", "--dry-run"])
    assert str(args.repo_path) == "repo"
    assert str(args.notebook) == "n.ipynb"
    assert args.dry_run is True


def test_invalid_target_rejected(capsys):
    with pytest.raises(SystemExit):
        _convert_parser().parse_args(["./my_project", "--target", "sagemaker"])
    assert "kaggle" in capsys.readouterr().err


def test_folder_named_sync_disambiguated_with_dot_slash(tmp_path, monkeypatch):
    """Documented gotcha: 'sync' alone is the subcommand; './sync' is a repo path."""
    (tmp_path / "sync").mkdir()
    monkeypatch.chdir(tmp_path)

    called = {}
    import repo2nb.cli as cli
    monkeypatch.setattr(cli, "convert", lambda *a, **k: called.update(repo=a[0]))

    main(["./sync"])
    assert called["repo"].name == "sync"


def test_main_dispatches_reverse(tmp_path, monkeypatch):
    import repo2nb.cli as cli
    seen = {}
    monkeypatch.setattr(cli, "reverse", lambda nb, out, force: seen.update(nb=nb, out=out, force=force))

    main(["reverse", "book.ipynb"])
    assert seen["nb"].name == "book.ipynb"
    assert seen["out"].name == "book"  # default output dir
    assert seen["force"] is False


def test_main_dispatches_sync(tmp_path, monkeypatch):
    import repo2nb.cli as cli
    seen = {}
    monkeypatch.setattr(cli, "sync", lambda repo, notebook_path, dry_run: seen.update(repo=repo, dry_run=dry_run))

    main(["sync", "./repo", "--dry-run"])
    assert seen["repo"].name == "repo"
    assert seen["dry_run"] is True

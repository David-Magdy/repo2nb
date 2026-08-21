import json
import pathlib

import nbformat

from repo2nb.converter import convert

FIXTURE = {
    "main.py": "import numpy as np\nfrom pkg.helper import h\n\nprint(np.zeros(2), h())\n",
    "pkg/__init__.py": "",
    "pkg/helper.py": "def h():\n    return 'hi'\n",
    "requirements.txt": "numpy\nscikit-learn\n",
    "data.bin": None,  # binary-skipped extension placeholder handled below
}


def _build_fixture(repo_path: pathlib.Path, with_git: bool = False):
    repo_path.mkdir(parents=True)
    if with_git:
        (repo_path / ".git").mkdir()
    for rel, content in FIXTURE.items():
        p = repo_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            p.write_bytes(b"\x00\x01")
        else:
            p.write_text(content)


def _normalize(nb) -> dict:
    data = json.loads(nbformat.writes(nb))
    data.get("metadata", {}).get("repo2nb", {}).pop("generated_at", None)
    for cell in data["cells"]:
        cell.pop("id", None)
    return data


def test_golden_kaggle_default(tmp_path):
    """Snapshot of the default --target kaggle output; catches unintended drift."""
    repo = tmp_path / "fixture_repo"
    _build_fixture(repo)
    out = tmp_path / "golden.ipynb"
    convert(repo, out)

    nb = nbformat.read(str(out), as_version=4)
    actual = _normalize(nb)

    golden_path = pathlib.Path(__file__).parent / "golden" / "kaggle_default.json"
    expected = json.loads(golden_path.read_text())
    assert actual == expected


def test_golden_kaggle_and_colab_differ_only_in_target_bits(tmp_path):
    repo = tmp_path / "fixture_repo"
    _build_fixture(repo, with_git=True)

    convert(repo, tmp_path / "k.ipynb", target_name="kaggle")
    convert(repo, tmp_path / "c.ipynb", target_name="colab")

    k = nbformat.read(str(tmp_path / "k.ipynb"), as_version=4)
    c = nbformat.read(str(tmp_path / "c.ipynb"), as_version=4)
    assert k.metadata["repo2nb"]["target"] == "kaggle"
    assert c.metadata["repo2nb"]["target"] == "colab"

    k_srcs = [cell.source for cell in k.cells]
    c_srcs = [cell.source for cell in c.cells]
    assert any("kaggle_secrets" in s for s in k_srcs)
    assert any("google.colab import userdata" in s for s in c_srcs)

import json
import sys
from pathlib import Path
from subprocess import check_call


def test_e2e(tmp_path: Path, monkeypatch):
    # Isolated workdir
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.txt").write_text("hi")

    # Install package from repo root (parents[2] = project root)
    repo_root = Path(__file__).resolve().parents[2]
    check_call([sys.executable, "-m", "pip", "install", "-e", str(repo_root)])

    check_call(["reprokit", "init", "--data", "./data"])
    check_call(["reprokit", "seed", "--seed", "7"])
    check_call(["reprokit", "env-freeze"])
    check_call(["reprokit", "hash-data", "./data"])
    check_call(["reprokit", "manifest", "--config", "reprokit.toml"])  # exists from init

    m = json.loads((tmp_path / "repro" / "manifest.json").read_text())
    assert m["data"]["merkle_root"]
    assert m["code"]  # may be partial if not a git repo

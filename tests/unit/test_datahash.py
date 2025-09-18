from pathlib import Path

from reprokit.datahash import write_hash


def test_merkle_changes(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()
    f = d / "x.txt"
    f.write_text("hello")
    out = tmp_path / "h.json"

    h1 = write_hash([str(d)], [], 2, 1024, str(out))
    f.write_text("hello!")
    h2 = write_hash([str(d)], [], 2, 1024, str(out))

    assert h1["merkle_root"] != h2["merkle_root"]

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Iterable
from pathlib import Path

from .utils import git_info, in_container, read_json, write_json

_DEF_MANIFEST = Path("repro/manifest.json")


def _sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_many(paths: Iterable[str]) -> list[str]:
    return [_sha256(Path(p)) for p in paths]


def write(
    run_id: str | None,
    config_paths: list[str],
    out_path: str | Path = _DEF_MANIFEST,
) -> dict:
    data = read_json(Path("repro/data_hash.json"))
    sysinfo = read_json(Path("repro/environment/system.json"))
    seeds = read_json(Path(".repro/seeds.json"))

    host = os.uname().nodename if hasattr(os, "uname") else os.getenv("COMPUTERNAME", "")

    payload = {
        "run_id": run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "code": git_info(),
        "environment": {
            **sysinfo,
            "artifacts": {
                "requirements.lock": str(Path("repro/environment/requirements.lock")),
                "environment.yml": str(Path("repro/environment/environment.yml")),
            },
        },
        "data": data,
        "determinism": seeds,
        "config": {"files": config_paths, "hashes": _hash_many(config_paths)},
        "runtime": {"hostname": host, "container": in_container(), "ts": time.time()},
    }
    write_json(Path(out_path), payload)
    return payload

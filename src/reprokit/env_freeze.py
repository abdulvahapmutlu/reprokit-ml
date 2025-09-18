from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .utils import run, system_snapshot, write_json

_DEF_OUT = Path("repro/environment")


def detect_manager() -> str:
    if Path("poetry.lock").exists() or shutil.which("poetry"):
        return "poetry"
    if shutil.which("conda"):
        return "conda"
    if shutil.which("uv"):
        return "uv"
    return "pip"


def freeze(manager: str = "auto", out_dir: str | Path = _DEF_OUT) -> dict:
    if manager == "auto":
        manager = detect_manager()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if manager == "poetry":
        lock: str = run(["poetry", "export", "--without-hashes", "-f", "requirements.txt"])
        (out / "requirements.lock").write_text(lock)
    elif manager == "conda":
        envyml: str = run(["conda", "env", "export"])
        (out / "environment.yml").write_text(envyml)
    elif manager == "uv":
        lock = run(["uv", "pip", "freeze"])
        (out / "requirements.lock").write_text(lock)
    else:  # pip
        lock = run([sys.executable, "-m", "pip", "freeze"])
        (out / "requirements.lock").write_text(lock)

    sysinfo = system_snapshot()
    write_json(out / "system.json", sysinfo)
    return {"manager": manager, "out": str(out), "system": sysinfo}

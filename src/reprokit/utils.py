from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, cast


class ShellError(RuntimeError):
    def __init__(self, cmd: Sequence[str], exit_code: int, output: str) -> None:
        super().__init__(f"Command failed ({exit_code}): {' '.join(cmd)}\n{output}")
        self.cmd = list(cmd)
        self.exit_code = exit_code
        self.output = output


def run(cmd: Sequence[str], check: bool = True) -> str:
    """Run a command, return text output; raise ShellError on failure if check=True."""
    try:
        res = subprocess.run(
            list(cmd), check=True, capture_output=True, text=True, encoding="utf-8"
        )
        return res.stdout
    except subprocess.CalledProcessError as e:  # pragma: no cover
        msg = (e.stdout or "") + (e.stderr or "")
        if check:
            raise ShellError(cmd, e.returncode, msg) from e
        return msg


def which(name: str) -> str | None:
    from shutil import which as _which

    return _which(name)


def read_json(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return cast(dict[str, Any], json.loads(p.read_text()))


def write_json(path: Path | str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))


def system_snapshot() -> dict[str, Any]:
    import psutil  # runtime dep

    snap: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "ram_total_mb": int(psutil.virtual_memory().total / (1024 * 1024)),
        "gpus": [],
    }
    if which("nvidia-smi"):
        try:
            q = run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader",
                ]
            ).strip()
            snap["gpus"] = [line.strip() for line in q.splitlines() if line.strip()]
        except Exception:  # pragma: no cover
            pass
    return snap


def in_container() -> bool:
    if (
        os.environ.get("DOCKER_CONTAINER")
        or os.environ.get("KUBERNETES_SERVICE_HOST")
        or os.environ.get("DOTNET_RUNNING_IN_CONTAINER") == "true"
    ):
        return True
    try:
        cgroup = Path("/proc/1/cgroup")
        if cgroup.exists() and "docker" in cgroup.read_text():
            return True
    except Exception:  # pragma: no cover
        pass
    return False


def git_info() -> dict[str, Any]:
    def _safe(args: Iterable[str]) -> str | None:
        try:
            return run(list(args)).strip()
        except Exception:
            return None

    has_git = which("git") is not None
    return {
        "commit": _safe(["git", "rev-parse", "HEAD"]) if has_git else None,
        "branch": _safe(["git", "rev-parse", "--abbrev-ref", "HEAD"]) if has_git else None,
        "remote": _safe(["git", "config", "--get", "remote.origin.url"]) if has_git else None,
        "dirty": bool(_safe(["git", "status", "--porcelain"])) if has_git else False,
    }

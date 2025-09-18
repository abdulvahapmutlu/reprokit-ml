from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field


def _toml_loads(text: str) -> dict[str, Any]:
    """Parse TOML using stdlib tomllib on 3.11+; fallback to tomli elsewhere."""
    mod = importlib.import_module("tomllib" if sys.version_info >= (3, 11) else "tomli")
    return cast(dict[str, Any], cast(Any, mod).loads(text))


def _normalize_paths(paths: list[str]) -> list[str]:
    """Convert any OS-specific separators to POSIX for TOML safety."""
    return [Path(p).as_posix() for p in paths]


class ReproConfig(BaseModel):
    data_paths: list[str] = Field(default_factory=list)
    hash_exclude: list[str] = Field(
        default_factory=lambda: ["**/.ipynb_checkpoints/**", "*.tmp", "**/__pycache__/**"]
    )
    algorithm: str = "xxh3+sha256-merkle"
    sample_bytes: int = 1_048_576
    workers: int = 8
    cache_path: str = ".repro/hash-cache.sqlite"


_DEFAULT_TOML = """
# ReproKit-ML configuration
# See docs for fields. Exclude patterns use gitignore-style globs.
[data]
paths = []

[hash]
exclude = ["**/.ipynb_checkpoints/**", "*.tmp", "**/__pycache__/**"]
algorithm = "xxh3+sha256-merkle"
sample_bytes = 1048576
workers = 8
cache_path = ".repro/hash-cache.sqlite"
"""


def write_default_config(data_paths: list[str], add_precommit: bool = True) -> str:
    Path(".repro").mkdir(exist_ok=True)
    Path("repro").mkdir(exist_ok=True)
    path = Path("reprokit.toml")
    path.write_text(_DEFAULT_TOML)
    if data_paths:
        blob = _toml_loads(path.read_text())
        blob.setdefault("data", {})["paths"] = _normalize_paths(data_paths)

        def _dump(d: dict[str, Any]) -> str:
            lines: list[str] = ["[data]"]
            lines.append("paths = [" + ", ".join(f'"{p}"' for p in d["data"]["paths"]) + "]")
            lines.append("")
            lines.append("[hash]")
            h = d["hash"]
            excl = ", ".join(f'"{e}"' for e in h["exclude"])
            lines.append(f"exclude = [{excl}]")
            lines.append(f'algorithm = "{h["algorithm"]}"')
            lines.append(f"sample_bytes = {h['sample_bytes']}")
            lines.append(f"workers = {h['workers']}")
            lines.append(f'cache_path = "{h["cache_path"]}"')
            return "\n".join(lines) + "\n"

        path.write_text(_dump(blob))

    if add_precommit and not Path(".pre-commit-config.yaml").exists():
        from .config_templates import DEFAULT_PRECOMMIT  # lazy import

        Path(".pre-commit-config.yaml").write_text(DEFAULT_PRECOMMIT)
    return str(path)


def load(path: str | Path = "reprokit.toml") -> ReproConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    data = _toml_loads(p.read_text())
    return ReproConfig(
        data_paths=data.get("data", {}).get("paths", []),
        hash_exclude=data.get("hash", {}).get("exclude", []),
        algorithm=data.get("hash", {}).get("algorithm", "xxh3+sha256-merkle"),
        sample_bytes=int(data.get("hash", {}).get("sample_bytes", 1_048_576)),
        workers=int(data.get("hash", {}).get("workers", 8)),
        cache_path=data.get("hash", {}).get("cache_path", ".repro/hash-cache.sqlite"),
    )

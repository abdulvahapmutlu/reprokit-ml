from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _get_env(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val else default


def main() -> None:
    # Config via env (sensible defaults)
    manifest_rel = _get_env("REPROKIT_MANIFEST_PATH", "repro/manifest.json")
    max_age_hours_str = _get_env("REPROKIT_MANIFEST_MAX_AGE_HOURS", "24")

    try:
        max_age_hours = float(max_age_hours_str)
    except ValueError:
        _err(f"Invalid REPROKIT_MANIFEST_MAX_AGE_HOURS={max_age_hours_str!r}; expected a number")
        sys.exit(3)

    path = Path(manifest_rel)

    # 1) Must exist
    if not path.exists():
        _err(f"Manifest missing: {path}")
        sys.exit(1)

    # 2) Must be fresh enough (mtime within threshold)
    try:
        mtime = path.stat().st_mtime
    except OSError as e:
        _err(f"Failed to stat manifest {path}: {e}")
        sys.exit(4)

    age_seconds = time.time() - mtime
    max_age_seconds = max_age_hours * 3600.0

    if age_seconds > max_age_seconds:
        _err(
            f"Manifest is stale: {path} (age={age_seconds/3600:.1f}h > {max_age_hours:.1f}h). "
            f"Regenerate with: reprokit manifest --config <your-config>"
        )
        sys.exit(2)

    # OK
    sys.exit(0)


if __name__ == "__main__":
    main()

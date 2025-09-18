from __future__ import annotations

import os
import sys

if not os.environ.get("PYTHONHASHSEED"):
    print("PYTHONHASHSEED not set; run 'reprokit seed'", file=sys.stderr)
    sys.exit(1)

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

_DEF_CUBLAS = ":16:8"


def _numpy(seed: int) -> dict[str, Any]:
    try:
        import numpy as np

        np.random.seed(seed)
        return {"numpy": True}
    except Exception:
        return {"numpy": False}


def _torch(seed: int) -> dict[str, Any]:
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = _DEF_CUBLAS
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        return {"torch": True, "cublas": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}
    except Exception:
        return {"torch": False}


def _tensorflow(seed: int) -> dict[str, Any]:
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
        os.environ["TF_DETERMINISTIC_OPS"] = "1"
        return {"tensorflow": True}
    except Exception:
        return {"tensorflow": False}


def _jax(seed: int) -> dict[str, Any]:
    try:
        import jax

        _ = jax.random.PRNGKey(seed)
        return {"jax": True}
    except Exception:
        return {"jax": False}


def enable(seed: int, torch: bool = True, tf: bool = True, jax: bool = True) -> dict[str, Any]:
    """Enable deterministic behavior across common frameworks.

    Returns a dict describing what was set for inclusion in manifests.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    info: dict[str, Any] = {"seed": seed, "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED")}
    info.update(_numpy(seed))
    if torch:
        info.update(_torch(seed))
    if tf:
        info.update(_tensorflow(seed))
    if jax:
        info.update(_jax(seed))
    return info


def dump(path: str, info: dict | None = None) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = info or {"seed": int(os.environ.get("PYTHONHASHSEED", "0"))}
    Path(path).write_text(json.dumps(payload, indent=2))

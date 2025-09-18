# ReproKit-ML

[![PyPI version](https://img.shields.io/pypi/v/reprokit-ml.svg)](https://pypi.org/project/reprokit-ml/)
![Python versions](https://img.shields.io/pypi/pyversions/reprokit-ml.svg)
[![CI](https://github.com/USERNAME/reprokit-ml/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/reprokit-ml/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**One-command determinism + manifest for ML projects.**

> Scope is intentionally narrow: *deterministic seeds + environment freeze + Merkle data hash + single manifest*.  
> Keep using MLflow/W&B for experiment tracking and DVC for dataset versioning/remotes.

---

## ✨ Features

- **Determinism on demand:** Seeds Python/NumPy/Torch/TF/JAX and sets framework flags (e.g., cuDNN deterministic).
- **Environment freeze:** Detects pip/conda/poetry/uv and outputs lock artifacts plus `system.json` (OS/CPU/GPU/CUDA snapshot).
- **Merkle data hash:** Fast, sampled hashing (first/last N bytes + random chunks) with a **sqlite cache**; directory-level Merkle root.
- **Single manifest:** JSON binding **code (git)** + **env** + **data hash** + **determinism** + **config** for re-runs and audits.
- **Hooks:** Pre-commit hooks to guard seeds and prompt manifest freshness.

---

## 🚀 Install

From PyPI:
```
pip install reprokit-ml
````

From source (dev):

```
pip install -e .
pre-commit install
```

> Windows users: the examples below use **cmd.exe** .

---

## ⚡ Quickstart (Windows — cmd.exe)

```
:: in your project
reprokit init --data .\data

:: set deterministic behavior
reprokit seed --seed 42

:: freeze environment + system snapshot
reprokit env-freeze

:: hash your data (quote globs on Windows)
mkdir data & echo hello> data\a.txt
reprokit hash-data .\data --exclude "**/.ipynb_checkpoints/**"

:: write a manifest that ties everything together
reprokit manifest --config reprokit.toml
```

Artifacts created:

* `.repro/seeds.json`
* `repro/environment/requirements.lock` (or `environment.yml` if conda)
* `repro/environment/system.json` (platform/CPU/GPU/CUDA)
* `repro/data_hash.json` (Merkle root + stats)
* `repro/manifest.json` (single source of truth)

---

## 🧰 Commands

### `reprokit init`

Bootstraps config and hooks.

```
reprokit init --data .\data --data .\datasets\cifar10
```

* Creates `reprokit.toml` with paths and hashing defaults.
* Creates `.repro/` and `repro/`.
* Writes `.pre-commit-config.yaml` (if missing).

### `reprokit seed`

Applies deterministic knobs in the **current process**.

```
reprokit seed --seed 42
```

Sets:

* Python `PYTHONHASHSEED`, `random.seed`
* NumPy `np.random.seed`
* Torch (if installed): `torch.use_deterministic_algorithms(True)`, cuDNN deterministic, `CUBLAS_WORKSPACE_CONFIG=":16:8"`, etc.
* TensorFlow (if installed): `TF_DETERMINISTIC_OPS=1`, `tf.random.set_seed`
* JAX (if installed): initializes `PRNGKey`

Outputs `.repro/seeds.json`.

### `reprokit env-freeze`

Detects the manager and exports lock files + system snapshot.

```
reprokit env-freeze --out repro\environment
```

### `reprokit hash-data`

Computes a Merkle root over one or more directories.

```
reprokit hash-data .\data .\datasets\cifar10 ^
  --exclude "**/.ipynb_checkpoints/**" --exclude "*.tmp" ^
  --workers 8 --out repro\data_hash.json
```

* Uses sampled hashing for speed (first/last N bytes + random 4KB chunks), with a deterministic per-file RNG seed.
* Caches per-file digests in `.repro/hash-cache.sqlite`.

### `reprokit manifest`

Writes the single manifest binding code/env/data/seeds/config.

```
reprokit manifest --config conf\train.yaml --out repro\manifest.json
```

---

## ⚙️ Configuration (`reprokit.toml`)

Generated on `init`. Example:

```
[data]
paths = ["./data", "./datasets/cifar10"]

[hash]
exclude = ["**/.ipynb_checkpoints/**", "*.tmp", "**/__pycache__/**"]
algorithm = "xxh3+sha256-merkle"
sample_bytes = 1048576
workers = 8
cache_path = ".repro/hash-cache.sqlite"
```

---

## 📦 Manifest (schema sketch)

```
{
  "run_id": "2025-09-17T19:12:33Z",
  "code": {"commit": "3d9e…", "branch": "main", "remote": "…", "dirty": false},
  "environment": {
    "python": "3.11.6",
    "platform": "Windows-10-10.0.22631",
    "gpus": ["NVIDIA RTX …"],
    "artifacts": {
      "requirements.lock": "repro/environment/requirements.lock",
      "environment.yml": "repro/environment/environment.yml"
    }
  },
  "data": {"paths": ["./data"], "merkle_root": "a4f1…"},
  "determinism": {"seed": 42, "PYTHONHASHSEED": "42", "torch": true, "tensorflow": false, "jax": false},
  "config": {"files": ["conf/train.yaml"], "hashes": ["sha256:…"]},
  "runtime": {"hostname": "WIN-…", "container": false, "ts": 1694977953.12}
}
```

---

## 🪄 Tips & FAQs

* **Windows globs**: always quote patterns: `--exclude "**/.ipynb_checkpoints/**"`.
* **Speed vs safety**: sampled hashing is fast and stable; for critical subsets, add a future `--full-file` path (issue welcome).
* **Pre-commit hooks**:

  * `guard_seed` fails if you didn’t run `reprokit seed`.
  * `check_manifest` warns if `repro/manifest.json` is older than 24h (configurable via env).
* **Conda vs Poetry vs pip**: `env-freeze` auto-detects; if multiple are installed, Poetry takes precedence by design. Override with `--manager pip|conda|poetry|uv`.

---

## 🧪 Development

```
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -e . ruff mypy pytest pre-commit
pre-commit install

ruff check .
ruff format --check .
mypy src
pytest -q
```

---

## 🤝 Contributing

Issues and PRs welcome! Good first issues: `--no-cache`, full-file hashing per path, manifest verification command, MLflow/DVC plugins.

---

## 📜 License

MIT — see [LICENSE](LICENSE).

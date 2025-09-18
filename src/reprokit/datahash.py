from __future__ import annotations

import fnmatch
import hashlib
import random
import sqlite3
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import xxhash
from rich.progress import Progress


@dataclass(frozen=True)
class FileMeta:
    path: Path
    size: int
    mtime_ns: int


class HashCache:
    """SQLite-backed cache of per-file digests keyed by (path,size,mtime)."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                  path TEXT PRIMARY KEY,
                  size INTEGER NOT NULL,
                  mtime_ns INTEGER NOT NULL,
                  sample_bytes INTEGER NOT NULL,
                  algo TEXT NOT NULL,
                  digest BLOB NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_meta ON cache(size,mtime_ns)")

    def get(self, meta: FileMeta, sample_bytes: int, algo: str) -> bytes | None:
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute(
                "SELECT digest FROM cache WHERE path=? AND size=? AND mtime_ns=? "
                "AND sample_bytes=? AND algo=?",
                (str(meta.path), meta.size, meta.mtime_ns, sample_bytes, algo),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def put(self, meta: FileMeta, sample_bytes: int, algo: str, digest: bytes) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "REPLACE INTO cache(path,size,mtime_ns,sample_bytes,algo,digest) "
                "VALUES(?,?,?,?,?,?)",
                (str(meta.path), meta.size, meta.mtime_ns, sample_bytes, algo, digest),
            )


def _iter_files(roots: Iterable[str], excludes: list[str]) -> list[Path]:
    files: list[Path] = []
    for r in roots:
        root = Path(r)
        if root.is_file():
            files.append(root)
            continue
        for p in root.rglob("*"):
            if p.is_file():
                rel = str(p.as_posix())
                if any(fnmatch.fnmatch(rel, pat) for pat in excludes):
                    continue
                files.append(p)
    files.sort(key=lambda x: str(x).lower())
    return files


def _hash_file(meta: FileMeta, sample_bytes: int) -> bytes:
    size = meta.size
    h = xxhash.xxh3_128()
    rng = random.Random(xxhash.xxh3_64_hexdigest(meta.path.as_posix().encode()))
    with meta.path.open("rb") as f:
        if size <= sample_bytes:
            h.update(f.read())
        else:
            h.update(f.read(sample_bytes))
            f.seek(max(0, size - sample_bytes))
            h.update(f.read(sample_bytes))
            k = 8
            for _ in range(k):
                pos = rng.randrange(0, max(1, size - 4096))
                f.seek(pos)
                h.update(f.read(4096))
    return h.digest()


def _merkle_root(leaves: list[bytes]) -> str:
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    level = [hashlib.sha256(x).digest() for x in leaves]
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha256(a + b).digest())
        level = nxt
    return level[0].hex()


def write_hash(
    paths: list[str],
    exclude: list[str],
    workers: int,
    sample_bytes: int,
    out: str,
    cache_path: str | None = ".repro/hash-cache.sqlite",
    algo: str = "xxh3+sha256-merkle",
) -> dict:
    files = _iter_files(paths, exclude)
    metas = [FileMeta(p, p.stat().st_size, p.stat().st_mtime_ns) for p in files]
    cache = HashCache(Path(cache_path)) if cache_path else None

    leaves: list[bytes] = []
    with Progress() as progress:
        task = progress.add_task("Hashing files", total=len(metas))

        def _one(m: FileMeta) -> bytes:
            if cache:
                d = cache.get(m, sample_bytes, algo)
                if d is not None:
                    return d
            d = _hash_file(m, sample_bytes)
            if cache:
                cache.put(m, sample_bytes, algo, d)
            return d

        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            for idx, d in enumerate(ex.map(_one, metas)):
                leaves.append(hashlib.sha256(d + str(metas[idx].path).encode()).digest())
                progress.update(task, advance=1)

    root = _merkle_root(leaves)
    payload = {
        "paths": paths,
        "algorithm": algo,
        "merkle_root": root,
        "total_files": len(files),
        "sample_bytes": sample_bytes,
        "excluded": exclude,
    }
    outp = Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(__import__("json").dumps(payload, indent=2))
    return payload

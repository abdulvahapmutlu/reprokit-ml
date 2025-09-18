from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from . import determinism
from .config import write_default_config
from .datahash import write_hash
from .env_freeze import freeze as env_freeze
from .manifest import write as manifest_write

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def init(
    data: Annotated[list[str] | None, typer.Option("--data", help="Data roots to track")] = None,
    add_precommit: bool = True,
) -> None:
    """Bootstrap reproducibility config and cache dirs."""
    data_list = list(data) if data else []
    created = write_default_config(data_paths=data_list, add_precommit=add_precommit)
    console.print(f"[green]Created {created} and .repro/ cache.[/]")
    console.print("Next: run [bold]reprokit seed[/] and [bold]reprokit env-freeze[/].")


@app.command("seed")
def seed_cmd(
    seed: int = 42,
    torch: bool = True,
    tf: bool = True,
    jax: bool = True,
    save: str | None = ".repro/seeds.json",
) -> None:
    info = determinism.enable(seed, torch, tf, jax)
    if save:
        determinism.dump(save, info)
    console.print(f"[green]Determinism enabled (seed={seed}).[/]")


@app.command("env-freeze")
def env_freeze_cmd(manager: str = "auto", out: str = "repro/environment") -> None:
    meta = env_freeze(manager=manager, out_dir=out)
    console.print(f"[green]Environment frozen under {meta['out']} (manager={meta['manager']}).[/]")


@app.command("hash-data")
def hash_data_cmd(
    paths: Annotated[list[str], typer.Argument(help="One or more data roots")],
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", help="Glob patterns to exclude"),
    ] = None,
    workers: Annotated[int, typer.Option(help="Worker threads")] = 8,
    sample_bytes: Annotated[int, typer.Option(help="Sample bytes per edge chunk")] = 1_048_576,
    out: Annotated[str, typer.Option(help="Output JSON")] = "repro/data_hash.json",
    cache: Annotated[str, typer.Option(help="Cache database path")] = ".repro/hash-cache.sqlite",
) -> None:
    excl = list(exclude) if exclude else []
    payload = write_hash(paths, excl, workers, sample_bytes, out, cache)
    console.print(f"[green]Wrote data hash -> {out}[/] (files={payload['total_files']}).")


@app.command("manifest")
def manifest_cmd(
    run_id: Annotated[str | None, typer.Option("--run-id")] = None,
    config: Annotated[
        list[str] | None,
        typer.Option("--config", help="Config files to fingerprint"),
    ] = None,
    out: Annotated[str, typer.Option("--out")] = "repro/manifest.json",
) -> None:
    cfg = list(config) if config else []
    manifest_write(run_id=run_id, config_paths=cfg, out_path=out)
    console.print(f"[green]Manifest written -> {out}[/]")


if __name__ == "__main__":  # pragma: no cover
    app()

from __future__ import annotations
from pathlib import Path
import typer

from bpm.core import store_registry as reg
import os
from bpm.io.yamlio import safe_load_yaml

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _stores_yaml_path() -> Path:
    """
    Return `$BPM_CACHE/stores.yaml` path.
    Falls back to ~/.bpm_cache if BPM_CACHE is unset.
    (We avoid depending on bpm.core.env for maximum compatibility.)
    """
    root = os.environ.get("BPM_CACHE")
    if not root:
        root = str(Path.home() / ".bpm_cache")
    return Path(root) / "stores.yaml"

def _load_stores_yaml() -> dict:
    """
    Load the raw stores.yaml (for list/info printing).
    Kept here so CLI doesn't depend on unneeded registry internals.
    """
    p = _stores_yaml_path()
    if not p.exists():
        # stores maps id -> record dict
        return {"active": None, "stores": {}}
    return safe_load_yaml(p)


@app.command("add")
def add(
    source: str = typer.Argument(..., help="Local path or git URL of a BRS"),
    activate: bool = typer.Option(False, "--activate/--no-activate", help="Activate after adding"),
):
    """
    Add a BRS to the cache registry (and optionally activate it).
    """
    try:
        rec = reg.add(source, activate=activate)
        # Support both dataclass (StoreRecord) and dict returns
        rec_id = getattr(rec, "id", None)
        if rec_id is None and isinstance(rec, dict):
            rec_id = rec.get("id")
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not rec_id:
        rec_id = "(unknown-id)"

    msg = f"[ok] Added store: {rec_id}"
    if activate:
        msg += " (activated)"
    typer.secho(msg, fg=typer.colors.GREEN)


@app.command("activate")
def activate(
    store_id: str = typer.Argument(..., help="Store id to activate (see `bpm resource list`)"),
):
    """
    Set the active BRS (only one active at a time).
    """
    try:
        reg.activate(store_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho(f"[ok] Activated: {store_id}", fg=typer.colors.GREEN)


@app.command("remove")
def remove(
    store_id: str = typer.Argument(..., help="Store id to remove from cache registry"),
):
    """
    Remove a BRS from the registry. (Does not delete the source directory.)
    """
    try:
        reg.remove(store_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho(f"[ok] Removed: {store_id}", fg=typer.colors.GREEN)


@app.command("list")
def list_():
    """
    List cached BRS stores. Active store is marked with '*'.
    """
    data = _load_stores_yaml()
    active = data.get("active")
    stores = data.get("stores") or {}

    if not stores:
        typer.echo("(no stores)")
        raise typer.Exit(code=0)

    # stores is a dict: id -> record
    for sid in sorted(stores.keys()):
        rec = stores.get(sid) or {}
        mark = "*" if sid == active else " "
        # YAML uses 'cache_path' key
        typer.echo(
            f"{mark} {sid}  src={rec.get('source')}  cached={rec.get('cache_path')}"
        )


@app.command("info")
def info(
    store_id: str = typer.Option(None, "--id", help="Specific store id (default: active store)"),
):
    """
    Show details about a store. Defaults to the active store.
    """
    data = _load_stores_yaml()
    active = data.get("active")
    stores = data.get("stores") or {}

    sid = store_id or active
    if not sid:
        typer.secho("Error: no active store and no --id given", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Direct lookup by id in the dict
    match = stores.get(sid)
    if not match:
        typer.secho(f"Error: store not found: {sid}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"id: {match.get('id')}")
    typer.echo(f"source: {match.get('source')}")
    # YAML uses 'cache_path'
    typer.echo(f"cached_path: {match.get('cache_path')}")
    if active == sid:
        typer.echo("active: true")
    else:
        typer.echo("active: false")

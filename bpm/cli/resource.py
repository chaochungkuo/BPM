from __future__ import annotations
from pathlib import Path
import typer
from typing import Optional

from bpm.core import store_registry as reg
from bpm.core import env
import os
from bpm.io.yamlio import safe_load_yaml

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help=(
        "Resource (BRS store) commands.\n\n"
        "Add local BRS folders to the cache, switch the active store,\n"
        "list existing entries, inspect details, or remove an entry."
    ),
)


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
    source: Path = typer.Argument(..., help="Local path or git URL of a BRS"),
    activate: bool = typer.Option(False, "--activate/--no-activate", help="Activate after adding"),
):
    """
    Add a BRS to the cache registry (local path). Optionally activate it immediately.

    Example:
    - bpm resource add ./my-brs --activate
    """
    try:
        rec = reg.add(str(source), activate=activate)
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
    store_id: str = typer.Argument(
        ..., 
        help="Store id to activate (see `bpm resource list`)", 
        autocompletion=lambda ctx, args, incomplete: [sid for sid in (env.load_store_index().stores or {}).keys() if str(sid).startswith(incomplete)],
    ),
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
    store_id: str = typer.Argument(
        ..., 
        help="Store id to remove from cache registry", 
        autocompletion=lambda ctx, args, incomplete: [sid for sid in (env.load_store_index().stores or {}).keys() if str(sid).startswith(incomplete)],
    ),
):
    """
    Remove a BRS from the registry. Non-destructive: does not delete the original source.
    """
    try:
        reg.remove(store_id)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho(f"[ok] Removed: {store_id}", fg=typer.colors.GREEN)


@app.command("list")
def list_(
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    )
):
    """
    List cached BRS stores; the active store is marked with '*'.
    """
    data = _load_stores_yaml()
    active = data.get("active")
    stores = data.get("stores") or {}

    if not stores:
        typer.echo("(no stores)")
        raise typer.Exit(code=0)

    fmt = (format or "table").lower()

    # plain (backward compatible, used by tests)
    if fmt == "plain":
        for sid in sorted(stores.keys()):
            rec = stores.get(sid) or {}
            mark = "*" if sid == active else " "
            # YAML uses 'cache_path' key
            typer.echo(
                f"{mark} {sid}  src={rec.get('source')}  cached={rec.get('cache_path')}"
            )
        return

    if fmt == "json":
        import json
        out = {
            "active": active,
            "stores": {
                sid: {
                    "id": sid,
                    "source": (stores.get(sid) or {}).get("source"),
                    "cache_path": (stores.get(sid) or {}).get("cache_path"),
                }
                for sid in sorted(stores.keys())
            },
        }
        typer.echo(json.dumps(out, indent=2))
        return

    # table format (requires rich)
    try:
        from rich.console import Console
        from rich.table import Table
    except Exception:
        # fallback to plain if rich missing
        for sid in sorted(stores.keys()):
            rec = stores.get(sid) or {}
            mark = "*" if sid == active else " "
            typer.echo(
                f"{mark} {sid}  src={rec.get('source')}  cached={rec.get('cache_path')}"
            )
        return

    table = Table(title="BRS Stores")
    table.add_column("Active", justify="center", width=6)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Source", overflow="fold")
    table.add_column("Cached", overflow="fold")
    for sid in sorted(stores.keys()):
        rec = stores.get(sid) or {}
        table.add_row("*" if sid == active else "", sid, str(rec.get("source")), str(rec.get("cache_path")))
    Console().print(table)


@app.command("info")
def info(
    store_id: str = typer.Option(
        None,
        "--id",
        help="Specific store id (default: active store)",
        autocompletion=lambda ctx, args, incomplete: [sid for sid in (env.load_store_index().stores or {}).keys() if str(sid).startswith(incomplete)],
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default), plain, or json",
        show_default=True,
    ),
):
    """
    Show details for a store (id, source, cached_path, version/commit). Defaults to the active store.
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

    fmt = (format or "table").lower()

    if fmt == "json":
        import json

        payload = {
            "id": match.get("id"),
            "source": match.get("source"),
            "cached_path": match.get("cache_path"),
            "version": match.get("version"),
            "commit": match.get("commit"),
            "last_updated": match.get("last_updated"),
            "active": bool(active == sid),
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    if fmt == "table":
        try:
            from rich.console import Console
            from rich.table import Table
        except Exception:
            fmt = "plain"
        else:
            table = Table(title=f"BRS Store: {sid}")
            table.add_column("Field", style="bold", no_wrap=True)
            table.add_column("Value")
            table.add_row("ID", str(match.get("id")))
            table.add_row("Source", str(match.get("source")))
            table.add_row("Cached Path", str(match.get("cache_path")))
            table.add_row("Version", str(match.get("version", "")))
            table.add_row("Commit", str(match.get("commit", "")))
            table.add_row("Last Updated", str(match.get("last_updated", "")))
            table.add_row("Active", "true" if active == sid else "false")
            Console().print(table)
            return

    # plain output
    typer.echo(f"id: {match.get('id')}")
    typer.echo(f"source: {match.get('source')}")
    typer.echo(f"cached_path: {match.get('cache_path')}")
    typer.echo(f"version: {match.get('version', '')}")
    typer.echo(f"commit: {match.get('commit', '')}")
    typer.echo(f"last_updated: {match.get('last_updated', '')}")
    typer.echo("active: true" if active == sid else "active: false")


@app.command("update")
def update_cmd(
    store_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Specific store id (default: active store)",
        autocompletion=lambda ctx, args, incomplete: [sid for sid in (env.load_store_index().stores or {}).keys() if str(sid).startswith(incomplete)],
    ),
    all: bool = typer.Option(
        False, "--all", help="Update all stores instead of a single one"
    ),
    force: bool = typer.Option(
        False, "--force/--no-force", help="Force refresh even if version unchanged"
    ),
    check: bool = typer.Option(
        False, "--check/--no-check", help="Dry-run: show what would change without modifying cache"
    ),
):
    """
    Update cached BRS store(s) from their source directory.

    - Default: update the active store (or --id to specify).
    - --all: update every registered store.
    - --force: refresh even if versions match.
    - --check: dry-run; prints status without changing anything.
    """
    from bpm.core import store_registry as reg

    idx = env.load_store_index()
    targets: list[str]
    if all:
        targets = sorted((idx.stores or {}).keys())
        if not targets:
            typer.echo("(no stores)")
            raise typer.Exit(code=0)
    else:
        sid = store_id or idx.active
        if not sid:
            typer.secho("Error: no active store and no --id given", err=True, fg=typer.colors.RED)
            raise typer.Exit(code=1)
        targets = [sid]

    for sid in targets:
        # Probe cache vs source versions
        try:
            cache_ver, src_ver, needs = reg.probe_update(sid)
        except Exception as e:
            typer.secho(f"Error probing {sid}: {e}", err=True, fg=typer.colors.RED)
            continue

        if check:
            if src_ver is None:
                typer.echo(f"{sid}: source missing or invalid; cache={cache_ver}")
            elif needs or force:
                typer.echo(f"{sid}: update available {cache_ver} -> {src_ver}")
            else:
                typer.echo(f"{sid}: already up-to-date ({cache_ver})")
            continue

        # Non-dry run: perform update if needed/forced
        try:
            if needs or force:
                before = cache_ver
                reg.update(sid, force=force, check=False)
                # Read after-update version from cache
                after, _, _ = reg.probe_update(sid)
                typer.secho(f"[ok] Updated: {sid} {before} -> {after}", fg=typer.colors.GREEN)
            else:
                # Still refresh metadata/timestamps
                reg.update(sid, check=True)
                typer.echo(f"{sid}: already up-to-date ({cache_ver})")
        except Exception as e:
            typer.secho(f"Error updating {sid}: {e}", err=True, fg=typer.colors.RED)

    raise typer.Exit(code=0)

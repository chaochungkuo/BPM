from pathlib import Path
from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg
from bpm.core import env
from bpm.io.yamlio import safe_load_yaml


def _mk_brs(tmpdir, repo_id: str, name: str = "Demo") -> Path:
    """
    Create a minimal BRS folder with only repo.yaml present.
    """
    src = tmpdir / repo_id
    (src).mkdir(parents=True)
    (src / "repo.yaml").write_text(
        f"id: {repo_id}\nname: {name}\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    return src


def _load_stores_yaml(tmpdir) -> dict:
    p = env.get_cache_dir() / "stores.yaml"
    if not p.exists():
        return {}
    return safe_load_yaml(p)


def test_resource_add_list_activate_remove(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # two local BRS dirs
    brs1 = _mk_brs(tmpdir, "brs_one")
    brs2 = _mk_brs(tmpdir, "brs_two")

    # add first and activate
    r1 = runner.invoke(root_app, ["resource", "add", str(brs1), "--activate"])
    assert r1.exit_code == 0, r1.output
    assert "[ok] Added store:" in r1.output and "(activated)" in r1.output

    # list → one entry, active marked (json for stable assertions)
    rlist1 = runner.invoke(root_app, ["resource", "list", "--format", "json"])
    assert rlist1.exit_code == 0
    import json as _json
    lst_payload = _json.loads(rlist1.output)
    assert lst_payload.get("active") == "brs_one"
    assert "brs_one" in (lst_payload.get("stores") or {})

    # add second (no activate)
    r2 = runner.invoke(root_app, ["resource", "add", str(brs2)])
    assert r2.exit_code == 0, r2.output
    # list → both entries present (json)
    rlist2 = runner.invoke(root_app, ["resource", "list", "--format", "json"])
    assert rlist2.exit_code == 0
    lst2 = _json.loads(rlist2.output)
    assert set((lst2.get("stores") or {}).keys()) >= {"brs_one", "brs_two"}

    # activate second
    ract = runner.invoke(root_app, ["resource", "activate", "brs_two"])
    assert ract.exit_code == 0
    rlist3 = runner.invoke(root_app, ["resource", "list", "--format", "json"])
    lst3 = _json.loads(rlist3.output)
    assert lst3.get("active") == "brs_two"

    # info (active by default)
    rinfo = runner.invoke(root_app, ["resource", "info", "--format", "json"])
    assert rinfo.exit_code == 0
    info = _json.loads(rinfo.output)
    assert info.get("id") == "brs_two"
    assert info.get("active") is True

    # remove first
    rrm = runner.invoke(root_app, ["resource", "remove", "brs_one"])
    assert rrm.exit_code == 0

    rlist4 = runner.invoke(root_app, ["resource", "list", "--format", "json"])
    lst4 = _json.loads(rlist4.output)
    assert "brs_one" not in (lst4.get("stores") or {})
    assert "brs_two" in (lst4.get("stores") or {})

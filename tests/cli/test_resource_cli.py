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

    # list → one entry, active marked
    rlist1 = runner.invoke(root_app, ["resource", "list"])
    assert rlist1.exit_code == 0
    assert "* brs_one" in rlist1.output

    # add second (no activate)
    r2 = runner.invoke(root_app, ["resource", "add", str(brs2)])
    assert r2.exit_code == 0, r2.output
    # list → both entries present
    rlist2 = runner.invoke(root_app, ["resource", "list"])
    assert rlist2.exit_code == 0
    assert " brs_one" in rlist2.output
    assert " brs_two" in rlist2.output

    # activate second
    ract = runner.invoke(root_app, ["resource", "activate", "brs_two"])
    assert ract.exit_code == 0
    rlist3 = runner.invoke(root_app, ["resource", "list"])
    assert "* brs_two" in rlist3.output

    # info (active by default)
    rinfo = runner.invoke(root_app, ["resource", "info"])
    assert rinfo.exit_code == 0
    assert "id: brs_two" in rinfo.output
    assert "active: true" in rinfo.output

    # remove first
    rrm = runner.invoke(root_app, ["resource", "remove", "brs_one"])
    assert rrm.exit_code == 0

    rlist4 = runner.invoke(root_app, ["resource", "list"])
    assert "brs_one" not in rlist4.output
    assert "brs_two" in rlist4.output
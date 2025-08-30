import os
from pathlib import Path
from bpm.core import env, store_registry as reg

def test_add_activate_remove_local(tmpdir, monkeypatch):
    # isolate BPM_CACHE
    cache = tmpdir / "cache"
    monkeypatch.setenv("BPM_CACHE", str(cache))

    # prepare local source BRS
    src = tmpdir / "brs_src"
    (src / "config").mkdir(parents=True)
    (src / "templates").mkdir(parents=True)
    # minimal repo.yaml only (as per spec)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo BRS\ndescription: Minimal\nversion: 0.0.1\nmaintainer: Test <t@e>\n"
    )

    # add
    rec = reg.add(str(src), activate=True)
    assert rec.id == "demo-brs"
    assert Path(rec.cache_path).exists()
    assert env.load_store_index().active == "demo-brs"

    # list
    ids = reg.list_ids()
    assert ids == ["demo-brs"]

    # info
    info = reg.info("demo-brs")
    assert info.version == "0.0.1"

    # update (no-op but refreshes timestamps)
    up = reg.update("demo-brs")
    assert up.id == "demo-brs"

    # remove
    reg.remove("demo-brs")
    assert env.load_store_index().active is None
    assert "demo-brs" not in env.load_store_index().stores
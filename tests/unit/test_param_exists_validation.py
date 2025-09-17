from pathlib import Path
import pytest

from bpm.core.template_service import render as svc_render


def test_param_exists_dir_validation(tmpdir, monkeypatch):
    # Build an in-memory descriptor pointing to a temp template folder
    tpl_id = "x"
    tpl_root = tmpdir / "brs" / "templates" / tpl_id
    tpl_root.mkdir(parents=True)
    # minimal BRS to resolve paths
    (tmpdir / "brs" / "config").mkdir(parents=True)
    (tmpdir / "brs" / "repo.yaml").write_text("id: t\nname: T\ndescription: d\nversion: 0.0.1\nmaintainer: t@e\n")
    (tmpdir / "brs" / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (tmpdir / "brs" / "config" / "authors.yaml").write_text("authors: []\n")
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    # point active BRS to tmp brs
    from bpm.core import store_registry as reg
    rec = reg.add(str(tmpdir / "brs"), activate=True)

    # Write a trivial file to render and the descriptor with exists: dir
    (tpl_root / "a.j2").write_text("ok\n")
    (tpl_root / "template.config.yaml").write_text(
        "id: x\n"
        "description: test exists\n"
        "params:\n"
        "  indir: { type: str, required: true, cli: --indir, exists: dir }\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )

    # Also ensure files exist in the cached BRS path used by the loader
    import os
    from bpm.core import env
    cache_root = env.get_brs_cache_dir()
    cached_tpl = cache_root / "t" / "templates" / tpl_id
    cached_tpl.mkdir(parents=True, exist_ok=True)
    (cached_tpl / "a.j2").write_text("ok\n")
    (cached_tpl / "template.config.yaml").write_text(
        "id: x\n"
        "description: test exists\n"
        "params:\n"
        "  indir: { type: str, required: true, cli: --indir, exists: dir }\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )

    project_dir = Path(tmpdir / "proj").resolve()
    project_dir.mkdir()
    adhoc_dir = tmpdir / "adhoc"
    adhoc_dir.mkdir()

    # Non-existent dir should raise
    with pytest.raises(ValueError):
        svc_render(project_dir, tpl_id, params_kv=["indir=/no/such/dir"], dry=True, adhoc_out=adhoc_dir)

    # Existing dir should pass
    okdir = tmpdir / "data"
    okdir.mkdir()
    svc_render(project_dir, tpl_id, params_kv=[f"indir={okdir}"], dry=True, adhoc_out=adhoc_dir)

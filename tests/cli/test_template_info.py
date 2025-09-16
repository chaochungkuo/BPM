from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs_with_params(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "demo").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "templates" / "demo" / "template.config.yaml").write_text(
        "id: demo\n"
        "description: Demo Params\n"
        "params:\n"
        "  sample_id: {type: str, required: true, cli: --sample-id}\n"
        "  threads: {type: int, required: false, default: 4}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
        "hooks:\n"
        "  post_render: [hooks.x:post]\n"
        "publish:\n"
        "  metrics: {resolver: resolvers.m:collect}\n"
    )
    (src / "templates" / "demo" / "a.j2").write_text("hello\n")
    return src


def test_template_info_json(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_params(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(root_app, ["template", "info", "demo", "--format", "json"])
    assert r.exit_code == 0, r.output

    import json as _json

    data = _json.loads(r.output)
    assert data["id"] == "demo"
    assert data["description"].startswith("Demo")
    # param surface check
    pnames = {p["name"] for p in data.get("params")}
    assert {"sample_id", "threads"}.issubset(pnames)
    # render files included
    assert "a.j2 -> a.txt" in set(data.get("files", []))
    # hooks/publish present
    assert "post_render" in data.get("hooks", {})
    assert "metrics" in data.get("publish", {})


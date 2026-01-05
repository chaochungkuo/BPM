from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs_with_workflow(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "workflows" / "demo").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "workflows" / "demo" / "workflow_config.yaml").write_text(
        "id: demo\n"
        "description: Demo Workflow\n"
        "params:\n"
        "  sample_id: {type: str, required: true, cli: --sample-id}\n"
        "  threads: {type: int, required: false, default: 4}\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
        "  args:\n"
        "    - \"${ctx.params.sample_id}\"\n"
        "  env:\n"
        "    REPORT_DIR: \"${ctx.project_dir}/reports\"\n"
        "hooks:\n"
        "  pre_run: [hooks.env:main]\n"
        "  post_run: [hooks.collect:main]\n"
        "tools:\n"
        "  required: [python]\n"
        "  optional: [quarto]\n"
    )
    (src / "workflows" / "demo" / "run.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "echo \"$1\"\n"
    )
    return src


def test_workflow_info_json(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_workflow(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(root_app, ["workflow", "info", "demo", "--format", "json"])
    assert r.exit_code == 0, r.output

    import json as _json

    data = _json.loads(r.output)
    assert data["id"] == "demo"
    assert data["description"].startswith("Demo")
    assert data["run_entry"] == "run.sh"
    assert "REPORT_DIR" in data.get("run_env", {})
    pnames = {p["name"] for p in data.get("params")}
    assert {"sample_id", "threads"}.issubset(pnames)
    assert "pre_run" in data.get("hooks", {})
    assert "python" in data.get("tools", {}).get("required", [])


def test_workflow_info_plain_and_table(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_workflow(tmpdir)
    reg.add(str(src), activate=True)

    r_plain = runner.invoke(root_app, ["workflow", "info", "demo", "--format", "plain"])
    assert r_plain.exit_code == 0, r_plain.output
    assert "id: demo" in r_plain.output
    assert "run_entry: run.sh" in r_plain.output

    r_table = runner.invoke(root_app, ["workflow", "info", "demo", "--format", "table"])
    assert r_table.exit_code == 0, r_table.output
    assert "Workflow: demo" in r_table.output

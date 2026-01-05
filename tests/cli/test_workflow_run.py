from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.core.project_io import load as load_project
from bpm.cli.main import app as root_app


def _mk_brs_with_workflow(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "workflows" / "clean").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
    )
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "workflows" / "clean" / "workflow_config.yaml").write_text(
        "id: clean\n"
        "description: Demo workflow\n"
        "params:\n"
        "  name: {type: str, required: true, cli: --name}\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
        "  args:\n"
        "    - \"${ctx.params.name}\"\n"
    )
    (src / "workflows" / "clean" / "run.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "name=\"$1\"\n"
        "out=\"${BPM_PROJECT_DIR}/wf_ran.txt\"\n"
        "echo \"WF Hello ${name}\" > \"${out}\"\n"
    )
    return src


def test_workflow_run(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # BRS + activate
    src = _mk_brs_with_workflow(tmpdir)
    reg.add(str(src), activate=True)

    # init a project directory
    proj_name = "250901_Workflow_UKA"
    r = runner.invoke(root_app, ["project", "init", proj_name, "--outdir", str(tmpdir), "--host", "nextgen"])
    assert r.exit_code == 0, r.output

    pdir = tmpdir / proj_name

    # run workflow
    r3 = runner.invoke(
        root_app,
        ["workflow", "run", "clean", "--project", str(pdir / "project.yaml"), "--name", "Alice"],
    )
    assert r3.exit_code == 0, r3.output

    ran = tmpdir / proj_name / "wf_ran.txt"
    assert ran.exists()
    assert ran.read_text().strip() == "WF Hello Alice"

    project = load_project(pdir)
    wfs = project.get("workflows") or []
    assert any(w.get("id") == "clean" and w.get("status") == "completed" for w in wfs)

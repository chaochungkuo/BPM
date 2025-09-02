from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
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

    (src / "workflows" / "clean" / "workflow.yaml").write_text(
        "id: clean\n"
        "description: Demo workflow\n"
        "params:\n"
        "  name: {type: str, required: true}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - out.txt.j2 -> out.txt\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "workflows" / "clean" / "out.txt.j2").write_text(
        "WF Hello {{ ctx.params.name }}\n"
    )
    (src / "workflows" / "clean" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo 'running clean' > ran.txt\n"
    )
    return src


def test_workflow_render_and_run(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # BRS + activate
    src = _mk_brs_with_workflow(tmpdir)
    reg.add(str(src), activate=True)

    # init a project directory
    proj_name = "250901_Workflow_UKA"
    proj_path = "nextgen:/projects/250901_Workflow_UKA"
    r = runner.invoke(root_app, ["project", "init", proj_name, "--project-path", proj_path, "--cwd", str(tmpdir)])
    assert r.exit_code == 0, r.output

    pdir = tmpdir / proj_name

    # render workflow
    r2 = runner.invoke(root_app, ["workflow", "render", "clean", "--dir", str(pdir), "--param", "name=Alice"])
    assert r2.exit_code == 0, r2.output

    out = tmpdir / proj_name / proj_name / "clean" / "out.txt"
    assert out.exists()
    assert out.read_text().strip() == "WF Hello Alice"

    # run workflow
    r3 = runner.invoke(root_app, ["workflow", "run", "clean", "--dir", str(pdir)])
    assert r3.exit_code == 0, r3.output

    ran = tmpdir / proj_name / proj_name / "clean" / "ran.txt"
    assert ran.exists()
    assert "running clean" in ran.read_text()


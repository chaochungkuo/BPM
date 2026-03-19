from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app
from bpm.core.project_io import load as load_project


def _mk_brs_with_run(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
        "policy:\n"
        "  project_name:\n"
        "    example: \"250901_Tumor_RNAseq_UKA\"\n"
        "    regex: '^\\d{6}_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$'\n"
        "    message: \"Use YYMMDD_Parts_Separated_By_Underscores\"\n"
    )
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params:\n"
        "  name: {type: str, required: true}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo \"run step\" > ran.txt\n"
    )
    return src


def test_template_run_marks_completed(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_run(tmpdir)
    reg.add(str(src), activate=True)

    name = "250901_Run_UKA"
    r = runner.invoke(root_app, ["project", "init", name, "--outdir", str(tmpdir), "--host", "nextgen"])
    assert r.exit_code == 0

    # render first (to create folder/entry)
    r2 = runner.invoke(root_app, ["template", "render", "hello", "--dir", str(tmpdir / name), "--param", "name=X"])
    assert r2.exit_code == 0, r2.output

    # run
    r3 = runner.invoke(root_app, ["template", "run", "hello", "--dir", str(tmpdir / name)])
    assert r3.exit_code == 0, r3.output

    # file created by run.sh
    out = tmpdir / name / "250901_Run_UKA" / "hello" / "ran.txt"
    assert out.exists()
    assert out.read_text().strip() == "run step"

    # status updated
    data = load_project(tmpdir / name)
    t = [t for t in data["templates"] if t["id"] == "hello"][0]
    assert t["status"] == "completed"


def test_template_run_auto_detects_project_root_from_nested_cwd(tmpdir, monkeypatch):
    runner = CliRunner()
    base = Path(tmpdir)
    monkeypatch.setenv("BPM_CACHE", str(base / "cache_nested"))

    src = _mk_brs_with_run(base)
    reg.add(str(src), activate=True)

    name = "250901_RunAuto_UKA"
    project_dir = base / name
    r = runner.invoke(root_app, ["project", "init", name, "--outdir", str(base), "--host", "nextgen"])
    assert r.exit_code == 0, r.output

    r2 = runner.invoke(root_app, ["template", "render", "hello", "--dir", str(project_dir), "--param", "name=X"])
    assert r2.exit_code == 0, r2.output

    nested = project_dir / "nested" / "work"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    r3 = runner.invoke(root_app, ["template", "run", "hello"])
    assert r3.exit_code == 0, r3.output

    out = project_dir / name / "hello" / "ran.txt"
    assert out.exists()
    assert out.read_text().strip() == "run step"

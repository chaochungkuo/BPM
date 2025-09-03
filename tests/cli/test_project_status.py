from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.core import env
from bpm.cli.project import app as project_app
from bpm.core.project_io import load as load_project


def test_project_info_and_status(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # build minimal BRS
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
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
    reg.add(str(src), activate=True)

    # init
    name = "250901_Test_UKA"
    r = runner.invoke(project_app, ["init", name, "--outdir", str(tmpdir), "--host", "nextgen"])
    assert r.exit_code == 0, r.output

    # info
    r2 = runner.invoke(project_app, ["info", "--dir", str(tmpdir / name)])
    assert r2.exit_code == 0
    assert "name: 250901_Test_UKA" in r2.output
    assert "status: initiated" in r2.output

    # status (text table-ish)
    r3 = runner.invoke(project_app, ["status", "--dir", str(tmpdir / name)])
    assert r3.exit_code == 0
    assert "Project: 250901_Test_UKA" in r3.output
    assert "Status : initiated" in r3.output
    assert "Templates: 0" in r3.output

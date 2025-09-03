from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.core import env
from bpm.core import brs_loader
from bpm.core.project_io import load as load_project
from bpm.cli.project import app as project_app


def _mk_min_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    # settings with project_name policy
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
        "policy:\n"
        "  project_name:\n"
        "    example: \"250901_Tumor_RNAseq_UKA\"\n"
        "    regex: '^\\d{6}_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$'\n"
        "    message: \"Use YYMMDD_Parts_Separated_By_Underscores\"\n"
    )
    (src / "config" / "authors.yaml").write_text(
        "authors:\n"
        "  - id: ckuo\n    name: Chao-Chung Kuo\n    email: ckuo@ukaachen.de\n"
        "  - id: lgan\n    name: Lin Gan\n    email: lgan@ukaachen.de\n"
    )
    return src


def test_project_init_happy_path(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # minimal BRS
    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    # init a project
    proj_name = "250901_Tumor_RNAseq_UKA"
    result = runner.invoke(
        project_app,
        ["init", proj_name, "--author", "ckuo,lgan", "--outdir", str(tmpdir), "--host", "nextgen"],
    )
    assert result.exit_code == 0, result.output
    assert "[ok] Created project at:" in result.output

    # verify project.yaml
    pdir = tmpdir / proj_name
    data = load_project(pdir)
    assert data["name"] == proj_name
    expected = f"nextgen:{(tmpdir / proj_name).resolve().as_posix()}"
    assert data["project_path"] == expected
    assert data["status"] == "initiated"
    assert [a["id"] for a in data["authors"]] == ["ckuo", "lgan"]


def test_project_init_rejects_bad_name(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    bad_name = "2025-09-01 Bad Name"
    result = runner.invoke(project_app, ["init", bad_name, "--outdir", str(tmpdir)])
    assert result.exit_code != 0
    assert "Invalid project name" in result.output

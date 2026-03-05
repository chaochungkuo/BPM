from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg


def _mk_min_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "illumina_methylation_process").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")
    (src / "templates" / "illumina_methylation_process" / "template.config.yaml").write_text(
        "id: illumina_methylation_process\n"
        "description: Process Illumina methylation arrays\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "illumina_methylation_process" / "a.j2").write_text("hello\n")
    return src


def test_agent_start_recommendation(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(
        root_app,
        ["agent", "start", "--goal", "illumina methylation analysis", "--non-interactive"],
    )
    assert r.exit_code == 0, r.output
    assert "Top template recommendations" in r.output
    assert "illumina_methylation_process" in r.output
    assert "source:" in r.output
    assert "Proposed command:" in r.output
    assert "bpm template render illumina_methylation_process" in r.output


def test_agent_start_confirmation_no(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(
        root_app,
        ["agent", "start", "--goal", "illumina methylation analysis"],
        input="no\n",
    )
    assert r.exit_code == 0, r.output
    assert "Proceed? (yes/no/edit)" in r.output
    assert "Cancelled." in r.output

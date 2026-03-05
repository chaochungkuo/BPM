from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg


def _mk_brs_with_methods(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "illumina_methylation_process").mkdir(parents=True)
    (src / "templates" / "dgea").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "templates" / "illumina_methylation_process" / "template.config.yaml").write_text(
        "id: illumina_methylation_process\n"
        "description: process\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "illumina_methylation_process" / "a.j2").write_text("hello\n")
    (src / "templates" / "illumina_methylation_process" / "METHODS.md").write_text(
        "Methylation preprocessing was performed with noob normalization.\n"
    )
    (src / "templates" / "illumina_methylation_process" / "citations.yaml").write_text(
        "citations:\n"
        "  - id: minfi\n"
        "    text: Aryee et al. minfi package\n"
        "    doi: 10.1093/bioinformatics/btu049\n"
    )

    (src / "templates" / "dgea" / "template.config.yaml").write_text(
        "id: dgea\n"
        "description: dgea\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - b.j2 -> b.txt\n"
    )
    (src / "templates" / "dgea" / "b.j2").write_text("hello\n")
    (src / "templates" / "dgea" / "METHODS.md").write_text(
        "Differential expression analysis was carried out with limma.\n"
    )
    (src / "templates" / "dgea" / "citations.yaml").write_text(
        "- id: limma\n"
        "  text: Ritchie et al. limma package\n"
    )
    return src


def _mk_project(tmpdir):
    pdir = tmpdir / "proj"
    pdir.mkdir(parents=True)
    (pdir / "project.yaml").write_text(
        "schema_version: 1\n"
        "name: DemoProj\n"
        "created: 2026-03-05T00:00:00Z\n"
        "project_path: local:/tmp/DemoProj\n"
        "authors: []\n"
        "status: active\n"
        "templates:\n"
        "  - id: illumina_methylation_process\n"
        "    source_template: illumina_methylation_process\n"
        "    status: completed\n"
        "    params:\n"
        "      array_type: EPIC\n"
        "  - id: dgea\n"
        "    source_template: dgea\n"
        "    status: completed\n"
    )
    (pdir / "illumina_methylation_process" / "results").mkdir(parents=True)
    (pdir / "illumina_methylation_process" / "results" / "run_info.yaml").write_text(
        "timestamp: 2026-03-05T12:00:00Z\n"
        "command: bash run.sh\n"
        "versions:\n"
        "  R: 4.4.0\n"
        "  minfi: 1.48.0\n"
    )
    return pdir


def test_agent_methods_stdout_and_outfile(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_methods(tmpdir)
    reg.add(str(src), activate=True)
    pdir = _mk_project(tmpdir)

    r = runner.invoke(root_app, ["agent", "methods", "--dir", str(pdir), "--style", "concise"])
    assert r.exit_code == 0, r.output
    assert "# Methods Draft" in r.output
    assert "DemoProj" in r.output
    assert "Methylation preprocessing" in r.output
    assert "R | 4.4.0" in r.output
    assert "10.1093/bioinformatics/btu049" in r.output

    out_path = tmpdir / "methods.md"
    r2 = runner.invoke(root_app, ["agent", "methods", "--dir", str(pdir), "--out", str(out_path)])
    assert r2.exit_code == 0, r2.output
    assert out_path.exists()
    txt = out_path.read_text()
    assert "## Citations" in txt
    assert "Differential expression analysis" in txt

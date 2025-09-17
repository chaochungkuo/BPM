from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params:\n"
        "  name: {type: str, required: true, cli: --name}\n"
        "  verbose: {type: bool, default: false, cli: --verbose}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - out.txt.j2 -> out.txt\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "out.txt.j2").write_text(
        "Name={{ ctx.params.name }} Verbose={{ ctx.params.verbose }}\n"
    )
    return src


def test_render_accepts_template_defined_flags(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs(tmpdir)
    reg.add(str(src), activate=True)

    # init project
    proj = tmpdir / "P"
    proj.mkdir()
    (proj / "project.yaml").write_text(
        "schema_version: 1\nname: P\nproject_path: local:/tmp/P\nauthors: []\nstatus: active\ntemplates: []\n"
    )

    r = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "hello",
            "--dir",
            str(proj),
            "--name",
            "Bob",
            "--verbose",
        ],
    )
    assert r.exit_code == 0, r.output

    out = proj / "P" / "hello" / "out.txt"
    assert out.exists()
    assert out.read_text().strip() == "Name=Bob Verbose=True"


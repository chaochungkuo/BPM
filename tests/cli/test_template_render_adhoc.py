from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs_with_template(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
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
        "    - out.txt.j2 -> out.txt\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "out.txt.j2").write_text(
        "Hello {{ ctx.params.name }}\n"
    )
    return src


def test_template_render_adhoc_writes_files_and_meta(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # BRS + activate
    src = _mk_brs_with_template(tmpdir)
    reg.add(str(src), activate=True)

    out_dir = tmpdir / "adhoc_out"

    # render ad-hoc (no project)
    r = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "hello",
            "--out",
            str(out_dir),
            "--param",
            "name=Alice",
        ],
    )
    assert r.exit_code == 0, r.output

    # files written under out_dir directly
    out = out_dir / "out.txt"
    assert out.exists()
    assert out.read_text().strip() == "Hello Alice"

    # bpm.meta.yaml present with source + params
    meta_path = out_dir / "bpm.meta.yaml"
    assert meta_path.exists()
    meta_text = meta_path.read_text()
    assert "brs_id: demo-brs" in meta_text
    assert "template_id: hello" in meta_text
    assert "name: Alice" in meta_text


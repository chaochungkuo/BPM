from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs_with_resolver(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "adhoc_tpl").mkdir(parents=True)
    (src / "templates" / "plain_tpl").mkdir(parents=True)
    (src / "resolvers").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "resolvers" / "out_from_bcl.py").write_text(
        "from pathlib import Path\n\n"
        "def main(ctx):\n"
        "    bcl = ctx.params.get('bcl_dir', '')\n"
        "    return Path(bcl).name\n"
    )

    (src / "templates" / "adhoc_tpl" / "template.config.yaml").write_text(
        "id: adhoc_tpl\n"
        "description: Demo with resolver\n"
        "params:\n"
        "  bcl_dir: {type: str, required: true}\n"
        "render:\n"
        "  adhoc_out_resolver: \"resolvers.out_from_bcl\"\n"
        "  files:\n"
        "    - out.txt.j2 -> out.txt\n"
    )
    (src / "templates" / "adhoc_tpl" / "out.txt.j2").write_text(
        "BCL {{ ctx.params.bcl_dir }}\n"
    )

    (src / "templates" / "plain_tpl" / "template.config.yaml").write_text(
        "id: plain_tpl\n"
        "description: No resolver\n"
        "params:\n"
        "  name: {type: str, required: true}\n"
        "render:\n"
        "  files:\n"
        "    - out.txt.j2 -> out.txt\n"
    )
    (src / "templates" / "plain_tpl" / "out.txt.j2").write_text("Hi {{ ctx.params.name }}\n")
    return src


def test_template_render_adhoc_resolver_derives_out(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.chdir(tmpdir)
    src = _mk_brs_with_resolver(tmpdir)
    reg.add(str(src), activate=True)

    bcl_dir = tmpdir / "data" / "230101_FC1"
    bcl_dir.mkdir(parents=True)

    r = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "adhoc_tpl",
            "--adhoc",
            "--param",
            f"bcl_dir={bcl_dir}",
        ],
    )
    assert r.exit_code == 0, r.output

    out_dir = tmpdir / "230101_FC1"
    out_file = out_dir / "out.txt"
    assert out_file.exists()
    assert "BCL" in out_file.read_text()


def test_template_render_adhoc_prefers_cli_out(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.chdir(tmpdir)
    src = _mk_brs_with_resolver(tmpdir)
    reg.add(str(src), activate=True)

    bcl_dir = tmpdir / "data" / "230101_FC2"
    bcl_dir.mkdir(parents=True)
    explicit = tmpdir / "explicit_out"

    r = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "adhoc_tpl",
            "--adhoc",
            "--out",
            str(explicit),
            "--param",
            f"bcl_dir={bcl_dir}",
        ],
    )
    assert r.exit_code == 0, r.output
    assert (explicit / "out.txt").exists()
    # Resolver-derived folder should not be created implicitly
    assert not (tmpdir / "230101_FC2").exists()


def test_template_render_adhoc_requires_resolver_or_out(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.chdir(tmpdir)
    src = _mk_brs_with_resolver(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "plain_tpl",
            "--adhoc",
            "--param",
            "name=Bob",
        ],
    )
    assert r.exit_code != 0
    assert "requires --out" in r.output.lower() or "adhoc_out_resolver" in r.output

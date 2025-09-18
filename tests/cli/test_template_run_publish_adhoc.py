from typer.testing import CliRunner
from pathlib import Path

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app


def _mk_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "resolvers").mkdir(parents=True)
    (src / "resolvers" / "__init__.py").write_text("")

    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")

    (src / "resolvers" / "find_marker.py").write_text(
        "from pathlib import Path\n"
        "def main(ctx):\n"
        "    p = Path(ctx.cwd) / 'marker'\n"
        "    return str(p) if p.exists() else ''\n"
    )

    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params: {}\n"
        "render:\n"
        "  into: '.'\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
        "publish:\n"
        "  marker_path: {resolver: resolvers.find_marker}\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo OK > marker\n"
    )
    return src


def test_run_publish_updates_bpm_meta(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs(tmpdir)
    reg.add(str(src), activate=True)

    outdir = tmpdir / "adhoc"

    # render ad-hoc
    r = runner.invoke(root_app, ["template", "render", "hello", "--out", str(outdir)])
    assert r.exit_code == 0, r.output

    # run ad-hoc
    r2 = runner.invoke(root_app, ["template", "run", "hello", "--out", str(outdir)])
    assert r2.exit_code == 0, r2.output
    meta = (outdir / "bpm.meta.yaml").read_text()
    assert "status: completed" in meta

    # publish ad-hoc
    r3 = runner.invoke(root_app, ["template", "publish", "hello", "--out", str(outdir)])
    assert r3.exit_code == 0, r3.output
    meta2 = (outdir / "bpm.meta.yaml").read_text()
    assert "published:" in meta2 and "marker_path:" in meta2


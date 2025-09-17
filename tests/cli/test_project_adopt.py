from typer.testing import CliRunner
from pathlib import Path

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app
from bpm.core.project_io import load as load_project


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
        "params: {}\n"
        "render:\n"
        "  into: '.'\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo ok > marker\n"
    )
    return src


def test_project_adopt_and_init_with_adopt(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs(tmpdir)
    reg.add(str(src), activate=True)

    # Create ad-hoc
    adhoc = tmpdir / "adhoc"
    r = runner.invoke(root_app, ["template", "render", "hello", "--out", str(adhoc)])
    assert r.exit_code == 0, r.output
    # Simulate publish info
    meta = adhoc / "bpm.meta.yaml"
    t = meta.read_text()
    meta.write_text(t + "\npublished:\n  marker: test\nstatus: completed\n")

    # Create project and adopt via init --adopt
    r2 = runner.invoke(root_app, ["project", "init", "ProjA", "--outdir", str(tmpdir), "--adopt", str(adhoc)])
    assert r2.exit_code == 0, r2.output
    proj_dir = tmpdir / "ProjA"
    p = load_project(proj_dir)
    ents = p.get("templates") or []
    assert any(e.get("id") == "hello" and e.get("published", {}).get("marker") == "test" for e in ents)

    # Adopt into existing another project
    r3 = runner.invoke(root_app, ["project", "init", "ProjB", "--outdir", str(tmpdir)])
    assert r3.exit_code == 0
    r4 = runner.invoke(root_app, ["project", "adopt", "--dir", str(tmpdir / "ProjB"), "--from", str(adhoc)])
    assert r4.exit_code == 0, r4.output
    p2 = load_project(tmpdir / "ProjB")
    ents2 = p2.get("templates") or []
    assert any(e.get("id") == "hello" for e in ents2)


from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app
from bpm.core.project_io import load as load_project


def _mk_brs_with_publish(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "resolvers").mkdir(parents=True)
    (src / "resolvers" / "__init__.py").write_text("")

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

    (src / "resolvers" / "hello_pub.py").write_text(
        "def main(ctx):\n"
        "    return f\"Hello {ctx.template.id} from {ctx.project.name}\"\n"
    )

    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params: {}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
        "publish:\n"
        "  greeting:\n"
        "    resolver: \"resolvers.hello_pub\"\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo ok > marker\n"
    )
    return src


def test_template_publish_updates_project(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_brs_with_publish(tmpdir)
    reg.add(str(src), activate=True)

    name = "250901_Publish_UKA"
    path = "nextgen:/projects/250901_Publish_UKA"
    r = runner.invoke(root_app, ["project", "init", name, "--project-path", path, "--cwd", str(tmpdir)])
    assert r.exit_code == 0

    # render
    r2 = runner.invoke(root_app, ["template", "render", "hello", "--dir", str(tmpdir / name)])
    assert r2.exit_code == 0, r2.output

    # publish
    r3 = runner.invoke(root_app, ["template", "publish", "hello", "--dir", str(tmpdir / name)])
    assert r3.exit_code == 0, r3.output

    data = load_project(tmpdir / name)
    t = [t for t in data["templates"] if t["id"] == "hello"][0]
    assert t["published"]["greeting"] == "Hello hello from 250901_Publish_UKA"
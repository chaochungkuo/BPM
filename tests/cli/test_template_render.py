from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.cli.main import app as root_app
from bpm.core.project_io import load as load_project


def _mk_brs_with_template(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
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


def _mk_brs_with_path_param(tmpdir):
    src = tmpdir / "brs_path"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "pathy").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-path\nname: Demo Path\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
    )
    (src / "config" / "authors.yaml").write_text("authors: []\n")
    (src / "templates" / "pathy" / "template.config.yaml").write_text(
        "id: pathy\n"
        "description: Demo path param\n"
        "params:\n"
        "  datadir: {type: str, required: true, exists: dir}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
    )
    (src / "templates" / "pathy" / "run.sh.j2").write_text("#!/usr/bin/env bash\nexit 0\n")
    return src


def test_template_render_writes_files_and_updates_project(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # BRS + activate
    src = _mk_brs_with_template(tmpdir)
    reg.add(str(src), activate=True)

    # init a project
    proj_name = "250901_Render_UKA"
    r = runner.invoke(root_app, ["project", "init", proj_name, "--outdir", str(tmpdir), "--host", "nextgen"])
    assert r.exit_code == 0, r.output

    # render
    r2 = runner.invoke(root_app, ["template", "render", "hello", "--dir", str(tmpdir / proj_name), "--param", "name=Alice"])
    assert r2.exit_code == 0, r2.output

    # check file
    out = tmpdir / proj_name / "250901_Render_UKA" / "hello" / "out.txt"
    assert out.exists()
    assert out.read_text().strip() == "Hello Alice"

    # project.yaml updated
    data = load_project(tmpdir / proj_name)
    t = [t for t in data["templates"] if t["id"] == "hello"][0]
    assert t["status"] == "active"
    assert t["params"]["name"] == "Alice"


def test_template_render_hostifies_path_params(tmpdir, monkeypatch):
    runner = CliRunner()
    base = Path(tmpdir)
    monkeypatch.setenv("BPM_CACHE", str(base / "cache2"))

    src = _mk_brs_with_path_param(base)
    reg.add(str(src), activate=True)

    proj_name = "250901_Path_UKA"
    project_dir = base / proj_name
    data_dir = base / "inputs"
    data_dir.mkdir()

    r = runner.invoke(root_app, ["project", "init", proj_name, "--outdir", str(base), "--host", "nextgen"])
    assert r.exit_code == 0, r.output

    r2 = runner.invoke(
        root_app,
        [
            "template",
            "render",
            "pathy",
            "--dir",
            str(project_dir),
            "--param",
            f"datadir={data_dir}",
        ],
    )
    assert r2.exit_code == 0, r2.output

    data = load_project(project_dir)
    entry = [t for t in data["templates"] if t["id"] == "pathy"][0]
    saved = entry["params"]["datadir"]
    expected = f"nextgen:{data_dir.resolve().as_posix()}"
    assert saved == expected

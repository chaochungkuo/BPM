from pathlib import Path

from bpm.core import store_registry as reg
from bpm.core import env, brs_loader
from bpm.core.descriptor_loader import load as load_desc
from bpm.core.context import build as build_ctx
from bpm.core.jinja_renderer import render


def test_renderer_renders_and_sets_executable(tmpdir, monkeypatch):
    # isolate cache
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # prepare a minimal BRS with hello template
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    # descriptor: render run.sh.j2 -> run.sh; run.entry = run.sh
    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params:\n"
        "  name: {type: str, cli: \"--name\", required: true}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\n"
        "echo \"Hello {{ ctx.params.name }} from {{ ctx.project.name }}\"\n"
    )

    # add & activate
    reg.add(str(src), activate=True)

    # load descriptor
    desc = load_desc("hello")

    # build ctx (simulate a project)
    project = {"name": "250901_Demo_UKA", "project_path": "nextgen:/projects/250901_Demo_UKA"}
    brs_cfg = {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}
    ctx = build_ctx(project, desc.id, {"name": "Alice"}, brs_cfg, tmpdir)

    # dry plan
    plan = render(desc, ctx, dry=True)
    assert plan[0].action == "mkdir"
    assert plan[1].action == "render"
    assert plan[-1].action == "chmod"

    # execute
    render(desc, ctx, dry=False)

    out_dir = tmpdir / "250901_Demo_UKA" / "hello"
    run = out_dir / "run.sh"
    assert run.exists()
    content = run.read_text()
    assert "Hello Alice from 250901_Demo_UKA" in content

    # check executable bit (user)
    assert (run.stat().st_mode & 0o111) != 0


def test_renderer_missing_template_raises(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    # descriptor refers to a non-existent src file
    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params: {}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - missing.j2 -> out.txt\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )

    reg.add(str(src), activate=True)
    desc = load_desc("hello")
    project = {"name": "P", "project_path": "nextgen:/P"}
    ctx = build_ctx(project, desc.id, {}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)

    try:
        render(desc, ctx, dry=False)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as e:
        assert "Template not found" in str(e)
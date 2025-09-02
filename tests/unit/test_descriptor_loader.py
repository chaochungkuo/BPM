from pathlib import Path
from bpm.core import store_registry as reg, env
from bpm.core import brs_loader as brs
from bpm.core import descriptor_loader as dl

def test_descriptor_loads_minimal(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    # minimal BRS with one template
    src = tmpdir / "brs"
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "config").mkdir()
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
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
    (src / "templates" / "hello" / "run.sh.j2").write_text("echo hi")

    reg.add(str(src), activate=True)

    d = dl.load("hello")
    assert d.id == "hello"
    assert d.description == "Demo"
    assert d.render_into.endswith("${ctx.template.id}/")
    assert d.render_files == [("run.sh.j2", "run.sh")]
    assert d.run_entry == "run.sh"
    assert "name" in d.params
    assert d.params["name"].required is True

def test_descriptor_id_mismatch_raises(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    src = tmpdir / "brs"
    (src / "templates" / "X").mkdir(parents=True)
    (src / "config").mkdir()
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "templates" / "X" / "template.config.yaml").write_text("id: notX\n")
    reg.add(str(src), activate=True)

    try:
        dl.load("X")
        assert False, "Expected ValueError for id mismatch"
    except ValueError as e:
        assert "Descriptor id mismatch" in str(e)
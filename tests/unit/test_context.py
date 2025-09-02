from pathlib import Path
from bpm.core.context import build

def test_build_ctx_and_helpers(tmpdir):
    project = {"name": "250901_Demo_UKA", "project_path": "nextgen:/projects/250901_Demo_UKA"}
    ctx = build(project, "hello", {"a": 1}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)

    assert ctx.project.name == "250901_Demo_UKA"
    assert ctx.template.id == "hello"
    assert ctx.params["a"] == 1
    assert ctx.cwd == Path(tmpdir)

    # Day-4 materialize behavior (drops host, keeps absolute)
    assert ctx.materialize("nextgen:/x/y") == "/x/y"
    assert ctx.materialize("/abs") == "/abs"

    # hostname + now exist and are strings
    assert isinstance(ctx.hostname(), str)
    assert isinstance(ctx.now(), str)

def test_build_ctx_ad_hoc(tmpdir):
    ctx = build(None, "hello", {}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)
    assert ctx.project is None
    assert ctx.template.id == "hello"
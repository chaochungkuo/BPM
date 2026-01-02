from types import SimpleNamespace
from bpm.utils.interpolate import interpolate_ctx_string

def test_interpolate_simple():
    ctx = SimpleNamespace(project=SimpleNamespace(name="P"), template=SimpleNamespace(id="hello"))
    s = "out=${ctx.project.name}/${ctx.template.id}"
    assert interpolate_ctx_string(s, ctx) == "out=P/hello"

def test_interpolate_missing_value_becomes_empty():
    ctx = SimpleNamespace(project=SimpleNamespace(name=None), template=SimpleNamespace(id="t"))
    s = "x=${ctx.project.name}-y"
    assert interpolate_ctx_string(s, ctx) == "x=-y"

def test_interpolate_mixed_dict_and_object():
    ctx = {"project": SimpleNamespace(name="P"), "template": {"id": "T"}}
    assert interpolate_ctx_string("${ctx.project.name}/${ctx.template.id}", ctx) == "P/T"

def test_interpolate_none_parent_becomes_empty():
    ctx = SimpleNamespace(project=None, template=SimpleNamespace(id="T"))
    assert interpolate_ctx_string("${ctx.project.name}/${ctx.template.id}", ctx) == "/T"

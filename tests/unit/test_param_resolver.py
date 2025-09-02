from bpm.core.param_resolver import resolve

def _desc_with_params():
    class S:
        def __init__(self, name, typ="str", cli=None, required=False, default=None):
            self.name = name
            self.type = typ
            self.cli = cli
            self.required = required
            self.default = default

    class D:
        id = "hello"
        params = {
            "a": S("a", typ="int", default=1),
            "b": S("b", typ="str", cli="--b", required=True),
            "c": S("c", typ="bool", cli="--c", default=False),
            "pat": S("pat", default="${ctx.project.name}/${ctx.template.id}"),
        }
    return D()

def test_precedence_and_types_and_interpolation():
    desc = _desc_with_params()
    project = {
        "name": "P",
        "project_path": "nextgen:/P",
        "templates": [{"id": "hello", "params": {"a": 2}}]
    }
    cli = {"b": "X", "c": "true"}  # b provided (required), c as string bool
    ctx_like = {
        "project": type("P", (), {"name": "P"})(),
        "template": type("T", (), {"id": "hello"})(),
        "params": {}
    }

    out = resolve(desc, cli, project, ctx_like)
    assert out["a"] == 2        # project overrides default(1)
    assert out["b"] == "X"      # required provided via CLI
    assert out["c"] is True     # coerced to bool
    assert out["pat"] == "P/hello"  # interpolated

def test_missing_required_raises():
    desc = _desc_with_params()
    project = {"name": "P", "project_path": "nextgen:/P", "templates": []}
    cli = {}  # missing required 'b'
    try:
        resolve(desc, cli, project, {"project": type("P", (), {"name":"P"})(), "template": type("T", (), {"id":"hello"})(), "params": {}})
        assert False, "Expected ValueError for missing required param"
    except ValueError as e:
        assert "Missing required parameters: b" in str(e)
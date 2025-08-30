from bpm.io.yamlio import safe_dump_yaml, safe_load_yaml

def test_yaml_roundtrip(tmpdir):
    p = tmpdir / "a.yaml"
    data = {"x": 1, "y": ["a", "b"]}
    safe_dump_yaml(p, data)
    loaded = safe_load_yaml(p)
    assert loaded == data

def test_yaml_atomic_overwrite(tmpdir):
    p = tmpdir / "b.yaml"
    safe_dump_yaml(p, {"a": 1})
    safe_dump_yaml(p, {"a": 2})
    assert safe_load_yaml(p) == {"a": 2}
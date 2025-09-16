import pytest
from bpm.io.yamlio import safe_load_yaml, safe_dump_yaml
from bpm.utils.errors import YamlError


def test_safe_load_yaml_raises_on_invalid(tmpdir):
    p = tmpdir / "bad.yaml"
    p.write_text("a: [1, 2\n")  # malformed YAML
    with pytest.raises(YamlError):
        safe_load_yaml(p)


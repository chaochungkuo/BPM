from pathlib import Path

from bpm.core import store_registry as reg
from bpm.core.context import build as build_ctx
from bpm.core.publish_resolver import resolve_all


def test_publish_resolver_updates_project(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = tmpdir / "brs"
    src.mkdir(parents=True, exist_ok=True)          # <-- add this line

    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "resolvers").mkdir(parents=True)
    (src / "resolvers" / "__init__.py").write_text("")
    (src / "resolvers" / "hello_pub.py").write_text(
        "def main(ctx):\n"
        "    return f\"Hello {ctx.template.id} from {ctx.project.name}\"\n"
    )

    reg.add(str(src), activate=True)

    # Project & ctx
    project = {
        "schema_version": 1,
        "name": "P",
        "created": "2025-09-01T00:00:00+00:00",
        "project_path": "nextgen:/P",
        "authors": [],
        "status": "initiated",
        "templates": [],
    }
    ctx = build_ctx(project, "hello", {}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)

    publish_cfg = {
        "greeting": {"resolver": "resolvers.hello_pub"}  # default function name 'main'
    }

    out = resolve_all(publish_cfg, ctx, project)
    assert "greeting" in out
    assert out["greeting"] == "Hello hello from P"

    # Ensure it’s written under the correct template entry
    templates = project.get("templates") or []
    assert len(templates) == 1 and templates[0]["id"] == "hello"
    assert templates[0]["published"]["greeting"] == "Hello hello from P"


def test_publish_resolver_with_args(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = tmpdir / "brs"
    src.mkdir(parents=True, exist_ok=True)          # <-- add this line

    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "resolvers").mkdir(parents=True)
    (src / "resolvers" / "__init__.py").write_text("")
    (src / "resolvers" / "kv.py").write_text(
        "def main(ctx, key='k', value='v'):\n"
        "    return {key: value}\n"
    )

    reg.add(str(src), activate=True)

    project = {"name": "P", "project_path": "nextgen:/P", "templates": []}
    ctx = build_ctx(project, "hello", {}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)

    publish_cfg = {
        "meta": {"resolver": "resolvers.kv", "args": {"key": "a", "value": "b"}}
    }
    out = resolve_all(publish_cfg, ctx, project)
    assert out["meta"] == {"a": "b"}
from pathlib import Path
from typer.testing import CliRunner

from bpm.core import store_registry as reg
from bpm.core import brs_loader
from bpm.core.context import build as build_ctx
from bpm.core.descriptor_loader import Descriptor  # for minimal fake desc
from bpm.core.hooks_runner import run as run_hooks


def test_hooks_runner_executes_in_order(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = tmpdir / "brs"
    src.mkdir(parents=True, exist_ok=True)          # <-- add this line

    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "hooks").mkdir(parents=True)
    (src / "hooks" / "__init__.py").write_text("")
    (src / "hooks" / "write_marker.py").write_text(
        "def main(ctx):\n"
        "    p = ctx.cwd / 'hook_was_here.txt'\n"
        "    p.write_text('ok', encoding='utf-8')\n"
        "    return str(p)\n"
    )

    reg.add(str(src), activate=True)

    # Minimal ctx (project not strictly needed)
    project = {"name": "P", "project_path": "nextgen:/P"}
    ctx = build_ctx(project, "hello", {}, {"repo": {}, "authors": {}, "hosts": {}, "settings": {}}, tmpdir)

    results = run_hooks(["hooks.write_marker"], ctx)
    assert results and results[0][0] == "hooks.write_marker"

    out = tmpdir / "hook_was_here.txt"
    assert out.exists()
    assert out.read_text() == "ok"
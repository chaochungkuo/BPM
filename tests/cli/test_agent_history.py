import json

from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg
from bpm.core.agent_provider import HealthResult, ModelCheckResult


def _mk_min_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "demo").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")
    (src / "templates" / "demo" / "template.config.yaml").write_text(
        "id: demo\n"
        "description: demo template\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "demo" / "a.j2").write_text("hello\n")
    return src


def test_history_lists_sessions(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.setenv("BPM_AGENT_SESSION_DIR", str(tmpdir / "sessions"))
    cfg_path = tmpdir / "agent.toml"
    monkeypatch.setenv("BPM_AGENT_CONFIG", str(cfg_path))

    cfg_path.write_text(
        "version = 1\n"
        "provider = \"openai_compatible\"\n"
        "base_url = \"http://127.0.0.1:11434/v1\"\n"
        "model = \"demo\"\n"
        "timeout_seconds = 60\n"
        "max_tokens = 2000\n"
        "temperature = 0.1\n"
        "token_source = \"none\"\n"
        "token_env_var = \"\"\n"
    )

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    from bpm.cli import agent as agent_cli

    monkeypatch.setattr(
        agent_cli.agent_provider,
        "healthcheck",
        lambda cfg: HealthResult(ok=True, status=200, message="mocked"),
    )
    monkeypatch.setattr(
        agent_cli.agent_provider,
        "check_model_available",
        lambda cfg: ModelCheckResult(ok=True, message="model exists", available_models=["demo"]),
    )

    r1 = runner.invoke(root_app, ["agent", "start", "--goal", "demo", "--non-interactive"])
    assert r1.exit_code == 0, r1.output
    r2 = runner.invoke(root_app, ["agent", "doctor"])
    assert r2.exit_code == 0, r2.output

    r3 = runner.invoke(root_app, ["agent", "history", "--limit", "10"])
    assert r3.exit_code == 0, r3.output
    assert "Recent agent sessions:" in r3.output
    assert "kind=start" in r3.output or "kind=doctor" in r3.output


def test_history_json_and_filter(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.setenv("BPM_AGENT_SESSION_DIR", str(tmpdir / "sessions"))

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(root_app, ["agent", "start", "--goal", "demo", "--non-interactive"])
    assert r.exit_code == 0, r.output

    rj = runner.invoke(root_app, ["agent", "history", "--kind", "start", "--format", "json", "--limit", "5"])
    assert rj.exit_code == 0, rj.output
    data = json.loads(rj.output)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["kind"] == "start"

    rb = runner.invoke(root_app, ["agent", "history", "--kind", "badkind"])
    assert rb.exit_code == 1, rb.output
    assert "invalid kind" in rb.output

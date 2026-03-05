from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg
from bpm.core.agent_config import AgentConfig
from bpm.core.agent_provider import ChatResult, HealthResult, ModelCheckResult


def _mk_min_brs(tmpdir):
    src = tmpdir / "brs"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "illumina_methylation_process").mkdir(parents=True)
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "config" / "settings.yaml").write_text("schema_version: 1\n")
    (src / "config" / "authors.yaml").write_text("authors: []\n")
    (src / "templates" / "illumina_methylation_process" / "template.config.yaml").write_text(
        "id: illumina_methylation_process\n"
        "description: Process Illumina methylation arrays\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "illumina_methylation_process" / "a.j2").write_text("hello\n")
    return src


def test_agent_start_chat_mode(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    from bpm.cli import agent as agent_cli

    cfg = AgentConfig(
        version=1,
        provider="openai_compatible",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.1:8b",
        timeout_seconds=60,
        max_tokens=2000,
        temperature=0.1,
        token_source="none",
        token_env_var="",
    )

    monkeypatch.setattr(agent_cli.agent_config, "load_config", lambda: cfg)
    monkeypatch.setattr(agent_cli.agent_config, "validate_config", lambda _cfg: None)
    monkeypatch.setattr(
        agent_cli.agent_provider,
        "healthcheck",
        lambda _cfg: HealthResult(ok=True, status=200, message="ok"),
    )
    monkeypatch.setattr(
        agent_cli.agent_provider,
        "check_model_available",
        lambda _cfg: ModelCheckResult(ok=True, message="model found", available_models=["llama3.1:8b"]),
    )
    monkeypatch.setattr(
        agent_cli.agent_provider,
        "chat",
        lambda _cfg, _msgs: ChatResult(text="Use template illumina_methylation_process."),
    )

    r = runner.invoke(root_app, ["agent", "start", "--goal", "methylation analysis"], input="quit\n")
    assert r.exit_code == 0, r.output
    assert "Connected to provider" in r.output
    assert "agent> Use template illumina_methylation_process." in r.output
    assert "Session ended." in r.output

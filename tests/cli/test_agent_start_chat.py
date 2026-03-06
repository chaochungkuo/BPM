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
        "params:\n"
        "  genome_assembly:\n"
        "    type: str\n"
        "    default: hg38\n"
        "  quant_method:\n"
        "    type: str\n"
        "    default: salmon\n"
        "  use_umi:\n"
        "    type: bool\n"
        "    default: true\n"
        "run:\n"
        "  entry: run.sh\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "illumina_methylation_process" / "a.j2").write_text("hello\n")
    (src / "templates" / "illumina_methylation_process" / "run.sh.j2").write_text(
        "bpm template render illumina_methylation_process --genome-assembly hg38 --quantification salmon --umi true\n"
    )
    (src / "templates" / "illumina_methylation_process" / "METHODS.md").write_text(
        "Illumina methylation preprocessing used noob normalization.\n"
    )
    (src / "templates" / "illumina_methylation_process" / "citations.yaml").write_text(
        "citations:\n"
        "  - id: minfi\n"
        "    text: minfi package paper\n"
    )
    (src / "templates" / "illumina_methylation_process" / "references.bib").write_text(
        "@article{minfi,\n"
        "  title={minfi}\n"
        "}\n"
    )
    (src / "templates" / "illumina_methylation_process" / "README.md").write_text(
        "# illumina_methylation_process\n\nProcess Illumina methylation arrays.\n"
    )
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
    assert "Hello, I am BPM Agent." in r.output
    assert "BPM Agent Chat" in r.output
    assert "Provider:" in r.output
    assert "Use template illumina_methylation_process." in r.output
    assert "Session ended." in r.output


def test_agent_start_chat_includes_template_and_run_hints(tmpdir, monkeypatch):
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

    captured = {}

    def _chat(_cfg, msgs):
        captured["messages"] = msgs
        return ChatResult(text="ok")

    monkeypatch.setattr(agent_cli.agent_provider, "chat", _chat)

    r = runner.invoke(root_app, ["agent", "start"], input="methylation pipeline\nquit\n")
    assert r.exit_code == 0, r.output

    runtime_hints = [m["content"] for m in captured["messages"] if m.get("role") == "system"]
    combined = "\n".join(runtime_hints)
    assert "Template detail [illumina_methylation_process]:" in combined
    assert "Command policy:" in combined
    assert "Template dossier [illumina_methylation_process]:" in combined
    assert "genome_assembly<str>" in combined
    assert "quant_method<str>" in combined
    assert "use_umi<bool>" in combined
    assert "citations.yaml ids: minfi" in combined
    assert "references.bib keys: minfi" in combined
    assert "METHODS.md summary:" in combined
    assert "--quantification salmon --umi true" in combined

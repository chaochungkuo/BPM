from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core import store_registry as reg
from bpm.core.agent_provider import HealthResult
from bpm.core.agent_provider import ModelCheckResult


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
        "description: demo\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "demo" / "a.j2").write_text("hello\n")
    return src


def test_agent_doctor_success(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    cfg_path = tmpdir / "agent.toml"
    monkeypatch.setenv("BPM_AGENT_CONFIG", str(cfg_path))

    cfg_path.write_text(
        "version = 1\n"
        "provider = \"openai_compatible\"\n"
        "base_url = \"http://127.0.0.1:11434/v1\"\n"
        "model = \"llama3.1:8b\"\n"
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
        lambda cfg: ModelCheckResult(ok=True, message="model exists", available_models=["llama3.1:8b"]),
    )

    r = runner.invoke(root_app, ["agent", "doctor"])
    assert r.exit_code == 0, r.output
    assert "[ok] Config loaded" in r.output
    assert "[ok] Provider endpoint" in r.output
    assert "[ok] Model check" in r.output
    assert "[ok] Active BRS templates discovered" in r.output


def test_agent_doctor_fails_on_missing_model(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    cfg_path = tmpdir / "agent.toml"
    monkeypatch.setenv("BPM_AGENT_CONFIG", str(cfg_path))

    cfg_path.write_text(
        "version = 1\n"
        "provider = \"openai_compatible\"\n"
        "base_url = \"http://127.0.0.1:11434/v1\"\n"
        "model = \"missing-model\"\n"
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
        lambda cfg: ModelCheckResult(ok=False, message="configured model missing", available_models=["demo"]),
    )

    r = runner.invoke(root_app, ["agent", "doctor"])
    assert r.exit_code == 1, r.output
    assert "[fail] Model check: configured model missing" in r.output

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
        "params:\n"
        "  sample_id: {type: str, required: true}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - a.j2 -> a.txt\n"
    )
    (src / "templates" / "demo" / "a.j2").write_text("hello\n")
    return src


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_start_writes_session_log(tmpdir, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))
    monkeypatch.setenv("BPM_AGENT_SESSION_DIR", str(tmpdir / "sessions"))

    src = _mk_min_brs(tmpdir)
    reg.add(str(src), activate=True)

    r = runner.invoke(root_app, ["agent", "start", "--goal", "demo", "--non-interactive"])
    assert r.exit_code == 0, r.output

    files = sorted((tmpdir / "sessions").glob("start-*.jsonl"))
    assert len(files) == 1

    events = _read_jsonl(files[0])
    names = [e.get("event") for e in events]
    assert "start_begin" in names
    assert "start_recommendations" in names
    assert "start_proposal" in names
    assert "start_end" in names


def test_doctor_writes_session_log(tmpdir, monkeypatch):
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

    r = runner.invoke(root_app, ["agent", "doctor"])
    assert r.exit_code == 0, r.output

    files = sorted((tmpdir / "sessions").glob("doctor-*.jsonl"))
    assert len(files) == 1
    events = _read_jsonl(files[0])
    names = [e.get("event") for e in events]
    assert "doctor_start" in names
    assert "doctor_endpoint_ok" in names
    assert "doctor_model_ok" in names
    assert "doctor_end" in names

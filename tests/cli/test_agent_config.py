from typer.testing import CliRunner

from bpm.cli.main import app as root_app


def test_agent_config_non_interactive_writes_file(tmpdir, monkeypatch):
    runner = CliRunner()
    cfg_path = tmpdir / "agent.toml"
    monkeypatch.setenv("BPM_AGENT_CONFIG", str(cfg_path))

    r = runner.invoke(root_app, ["agent", "config", "--non-interactive"])
    assert r.exit_code == 0, r.output
    assert cfg_path.exists()

    content = cfg_path.read_text()
    assert 'provider = "openai"' in content
    assert 'base_url = "https://api.openai.com/v1"' in content
    assert 'model = "gpt-5-nano"' in content

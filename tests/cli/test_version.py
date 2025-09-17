from typer.testing import CliRunner
from bpm.cli.main import app as root_app


def test_version_flag_prints_version():
    runner = CliRunner()
    r = runner.invoke(root_app, ["--version"])
    assert r.exit_code == 0
    assert "bpm " in r.output


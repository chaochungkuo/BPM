from typer.testing import CliRunner

from bpm.cli.main import app as root_app
from bpm.core.project_io import load as load_project, save as save_project


def _write_project(tmpdir):
    project_dir = tmpdir / "Proj"
    save_project(
        project_dir,
        {
            "schema_version": 1,
            "name": "Proj",
            "created": "2026-03-13T00:00:00+00:00",
            "project_path": f"local:{project_dir.resolve().as_posix()}",
            "authors": [],
            "status": "active",
            "templates": [
                {
                    "id": "alpha",
                    "status": "active",
                    "params": {"study_name": "alpha"},
                    "published": {},
                },
                {
                    "id": "beta",
                    "status": "completed",
                    "params": {"input_dir": "../alpha/results"},
                    "published": {"alpha_report": str((project_dir / "alpha" / "reports" / "index.html").resolve())},
                },
            ],
        },
    )
    (project_dir / "alpha" / "results").mkdir(parents=True)
    (project_dir / "alpha" / "results" / "marker.txt").write_text("x")
    (project_dir / "beta").mkdir(parents=True)
    return project_dir


def test_project_rm_template_dry_run(tmpdir):
    runner = CliRunner()
    project_dir = _write_project(tmpdir)

    result = runner.invoke(root_app, ["project", "rm-template", "alpha", "--dir", str(project_dir), "--dry-run", "--force"])
    assert result.exit_code == 0, result.output
    assert "would remove entry" in result.output
    assert "would delete" in result.output

    project = load_project(project_dir)
    assert [t["id"] for t in project["templates"]] == ["alpha", "beta"]
    assert (project_dir / "alpha").exists()


def test_project_rm_template_removes_entry_and_directory(tmpdir):
    runner = CliRunner()
    project_dir = _write_project(tmpdir)

    result = runner.invoke(root_app, ["project", "rm-template", "alpha", "--dir", str(project_dir), "--force"])
    assert result.exit_code == 0, result.output
    assert "Removed template 'alpha'" in result.output

    project = load_project(project_dir)
    assert [t["id"] for t in project["templates"]] == ["beta"]
    assert not (project_dir / "alpha").exists()


def test_project_rm_template_blocks_when_referenced_without_force(tmpdir):
    runner = CliRunner()
    project_dir = _write_project(tmpdir)

    result = runner.invoke(root_app, ["project", "rm-template", "alpha", "--dir", str(project_dir)])
    assert result.exit_code == 1
    assert "still referenced" in result.output

    project = load_project(project_dir)
    assert [t["id"] for t in project["templates"]] == ["alpha", "beta"]
    assert (project_dir / "alpha").exists()

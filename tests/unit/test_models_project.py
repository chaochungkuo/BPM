from bpm.models.project import Project, Author, TemplateEntry, ProjectState, TemplateStatus

def test_project_dataclass_minimal():
    prj = Project(
        schema_version=1,
        name="250901_Demo_UKA",
        created="2025-09-01T00:00:00+00:00",
        project_path="nextgen:/projects/250901_Demo_UKA",
    )
    assert prj.status == ProjectState.initiated
    assert prj.templates == []

def test_template_entry_defaults():
    t = TemplateEntry(id="hello")
    assert t.status == TemplateStatus.active
    assert t.params == {}
    assert t.published == {}
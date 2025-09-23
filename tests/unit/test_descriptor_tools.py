from bpm.core import store_registry as reg
from bpm.core import descriptor_loader as dl


def test_descriptor_tools_parsing(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = tmpdir / "brs"
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "config").mkdir()
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "render:\n"
        "  files: []\n"
        "tools:\n"
        "  required: [fastqc, multiqc]\n"
        "  optional: [bcl-convert]\n"
    )

    reg.add(str(src), activate=True)

    d = dl.load("hello")
    assert d.tools_required == ["fastqc", "multiqc"]
    assert d.tools_optional == ["bcl-convert"]


def test_descriptor_tools_list_as_required(tmpdir, monkeypatch):
    monkeypatch.setenv("BPM_CACHE", str(tmpdir / "cache"))

    src = tmpdir / "brs"
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "config").mkdir()
    (src / "repo.yaml").write_text(
        "id: demo-brs\nname: Demo\ndescription: d\nversion: 0.0.1\nmaintainer: T <t@e>\n"
    )
    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "render:\n"
        "  files: []\n"
        "tools: [samtools, bedtools]\n"
    )

    reg.add(str(src), activate=True)

    d = dl.load("hello")
    assert d.tools_required == ["samtools", "bedtools"]
    assert d.tools_optional == []


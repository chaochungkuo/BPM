from pathlib import Path
from bpm.core import store_registry as reg
from bpm.core import brs_loader as brs
from bpm.core import env

def test_brs_loader_reads_active_store(tmpdir, monkeypatch):
    # isolate cache
    cache = tmpdir / "cache"
    monkeypatch.setenv("BPM_CACHE", str(cache))

    # prepare minimal BRS on disk
    src = tmpdir / "brs_min"
    (src / "config").mkdir(parents=True)
    (src / "templates" / "hello").mkdir(parents=True)
    (src / "hooks").mkdir()
    (src / "resolvers").mkdir()
    (src / "workflows").mkdir()

    (src / "repo.yaml").write_text(
        "id: demo-brs\n"
        "name: Demo BRS\n"
        "description: Minimal\n"
        "version: 0.0.1\n"
        "maintainer: Test <t@e>\n"
    )
    (src / "config" / "authors.yaml").write_text(
        "authors:\n"
        "  - id: ckuo\n    name: Chao-Chung Kuo\n    email: ckuo@ukaachen.de\n"
    )
    (src / "config" / "hosts.yaml").write_text(
        "hosts:\n  nextgen:\n    aliases: [nextgen1]\n    mount_prefix: \"/mnt/nextgen/\"\n"
    )
    (src / "config" / "settings.yaml").write_text(
        "schema_version: 1\n"
        "policy:\n"
        "  project_name:\n"
        "    example: \"250901_Tumor_RNAseq_UKA\"\n"
        "    regex: '^\\d{6}_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$'\n"
        "    message: \"Use YYMMDD_Parts_Separated_By_Underscores\"\n"
    )
    (src / "templates" / "hello" / "template.config.yaml").write_text(
        "id: hello\n"
        "description: Demo\n"
        "params:\n"
        "  name: {type: str, cli: \"--name\", required: true}\n"
        "render:\n"
        "  into: \"${ctx.project.name}/${ctx.template.id}/\"\n"
        "  files:\n"
        "    - run.sh.j2 -> run.sh\n"
        "run:\n"
        "  entry: \"run.sh\"\n"
    )
    (src / "templates" / "hello" / "run.sh.j2").write_text(
        "#!/usr/bin/env bash\necho \"Hello {{ ctx.params.name }} from {{ ctx.project.name }}\""
    )

    # add & activate
    rec = reg.add(str(src), activate=True)
    assert env.load_store_index().active == "demo-brs"

    # paths & config
    root = brs.get_active_brs_path()
    assert root.exists()
    paths = brs.get_paths(root)
    assert paths.templates_dir.exists()
    assert paths.config_dir.exists()

    cfg = brs.load_config(root)
    assert cfg.repo["id"] == "demo-brs"
    assert "authors" in cfg.authors
    assert "hosts" in cfg.hosts
    assert "project_name" in cfg.settings.get("policy", {})

    # template presence
    assert brs.template_exists("hello", root)
    desc_path = brs.template_descriptor_path("hello", root)
    assert desc_path.exists()
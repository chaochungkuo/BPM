bpm/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ .gitignore
├─ bpm/                         # package root
│  ├─ __init__.py
│  │
│  ├─ models/                   # pure data models (lowest layer)
│  │  ├─ __init__.py
│  │  ├─ hostpath.py            # HostPath type (normalize/materialize)
│  │  ├─ project.py             # Project, TemplateEntry, Status enums
│  │  ├─ template_desc.py       # TemplateDescriptor schema (YAML)
│  │  ├─ workflow_desc.py       # WorkflowDescriptor schema (YAML, later)
│  │  └─ store_index.py         # StoresIndex schema (stores.yaml)
│  │
│  ├─ utils/                    # tiny helpers (no BPM imports)
│  │  ├─ __init__.py
│  │  ├─ time.py                # now_iso(), parse_iso()
│  │  ├─ table.py               # simple tty table printer
│  │  ├─ paths.py               # posix join helpers, chmod_x()
│  │  └─ errors.py              # custom exceptions
│  │
│  ├─ io/                       # IO primitives (no business logic)
│  │  ├─ __init__.py
│  │  ├─ yamlio.py              # safe_load_yaml, safe_dump_yaml
│  │  ├─ fs.py                  # mkdirs, copy_file_tree, atomic_write
│  │  └─ exec.py                # run_process (for run.sh)
│  │
│  ├─ core/                     # business logic (services)
│  │  ├─ __init__.py
│  │  ├─ env.py                 # read BPM_CACHE, resolve paths
│  │  ├─ store_registry.py      # read/write $BPM_CACHE/stores.yaml
│  │  ├─ brs_loader.py          # active BRS path, load repo.yaml + config/*
│  │  ├─ context.py             # ctx object (project, template, params, helpers)
│  │  ├─ project_io.py          # load/save project.yaml (HostPath normalize)
│  │  ├─ descriptor_loader.py   # read/validate template.config.yaml
│  │  ├─ jinja_renderer.py      # render *.j2, copy others (flat template rule)
│  │  ├─ param_resolver.py      # precedence: CLI > stored > param_refs > defaults
│  │  ├─ hooks_runner.py        # import & run hooks.<file>.main(ctx)
│  │  ├─ publish_resolver.py    # import & run resolvers.*.main(ctx)->value
│  │  ├─ template_service.py    # render/run/publish/status updates
│  │  └─ project_service.py     # init/status/info/close
│  │
│  └─ cli/                      # Typer CLI (only calls services)
│     ├─ __init__.py
│     ├─ app.py                 # root Typer app
│     ├─ resource.py            # bpm resource * (add/activate/remove/update/list/info)
│     ├─ project.py             # bpm project * (init/status/info/close)
│     └─ template.py            # bpm template * (render/run/publish)
│
└─ tests/
   ├─ conftest.py               # common fixtures (tmp cache, mini BRS, tmp project)
   ├─ unit/
   │  ├─ test_hostpath.py
   │  ├─ test_yamlio.py
   │  ├─ test_store_registry.py
   │  ├─ test_descriptor_loader.py
   │  ├─ test_param_precedence.py
   │  └─ test_context_paths.py
   ├─ cli/
   │  ├─ test_resource_cli.py
   │  ├─ test_project_init.py
   │  └─ test_template_render.py
   └─ data/
      └─ brs_min/               # minimal BRS fixture used by tests
         ├─ repo.yaml
         ├─ config/{authors.yaml,hosts.yaml,settings.yaml}
         ├─ hooks/__init__.py
         ├─ resolvers/__init__.py
         └─ templates/hello/{template.config.yaml,run.sh.j2}
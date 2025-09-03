from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import socket
from typing import Any, Dict, Optional
from bpm.utils.time import now_iso


@dataclass
class CtxProject:
    """
    Minimal project view for templates/hooks/resolvers.

    Attributes:
        name: Project name (e.g., "250901_Demo_UKA").
        project_path: Host-aware path string (e.g., "nextgen:/projects/250901_Demo_UKA").
    """
    name: str
    project_path: str


@dataclass
class CtxTemplate:
    """
    Minimal template view.

    Attributes:
        id: Template id (e.g., "hello").
        published: Already published values for this template (usually filled after run).
    """
    id: str
    published: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Ctx:
    """
    Unified context object passed into Jinja, hooks, and resolvers.

    Attributes:
        project: Project view (or None in ad-hoc mode).
        template: Template view for the current operation.
        params: Final parameter map for the current template.
        brs: Loaded BRS config {repo, authors, hosts, settings}.
        cwd: Current working directory (Path) for rendering/running.
    """
    project: Optional[CtxProject]
    template: CtxTemplate
    params: Dict[str, Any]
    brs: Dict[str, Any]
    cwd: Path

    # ------------------------- Helper methods -------------------------

    @property
    def project_dir(self) -> str:
        """
        Local filesystem base directory for this project.

        - In project mode: materializes project.project_path to a local absolute path.
        - In ad-hoc mode: falls back to ctx.cwd.
        """
        if self.project:
            return self.materialize(self.project.project_path)
        return str(self.cwd)

    def hostname(self) -> str:
        """
        Return a short hostname. Useful for host-aware defaults.
        """
        return socket.gethostname().split(".")[0]

    def materialize(self, hostpath: str) -> str:
        """
        Convert a host-aware path string into a local absolute path string.

        Day-4 simplification:
          - "host:/abs/path" -> "/abs/path" (drop host)
          - "/abs/path"      -> "/abs/path" (unchanged)

        Later (HostPath integration) this will consult config/hosts.yaml.
        """
        if ":" in hostpath:
            _, rest = hostpath.split(":", 1)
            return rest if rest.startswith("/") else f"/{rest}"
        return hostpath

    def now(self) -> str:
        """
        Return current UTC time as ISO 8601 string (no microseconds).
        """
        return now_iso()


def build(
    project: Optional[Dict[str, Any]],
    tpl_id: str,
    params: Dict[str, Any],
    brs_config: Dict[str, Any],
    cwd: Path,
) -> Ctx:
    """
    Construct a Ctx from raw dict-like inputs (what higher layers load).

    Args:
        project: Dict with at least {'name', 'project_path'} or None (ad-hoc).
        tpl_id: Current template id.
        params: Final params for this template render/run.
        brs_config: Dict holding {repo, authors, hosts, settings}.
        cwd: Working directory to consider as the render/run base.

    Returns:
        A fully-initialized Ctx object.
    """
    prj = None
    if project:
        prj = CtxProject(name=project["name"], project_path=project["project_path"])
    tpl = CtxTemplate(id=tpl_id, published={})
    return Ctx(project=prj, template=tpl, params=params, brs=brs_config, cwd=cwd)

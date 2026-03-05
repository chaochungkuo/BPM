from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from bpm.core.agent_config import AgentConfig, get_token


@dataclass(frozen=True)
class HealthResult:
    ok: bool
    status: int | None
    message: str


def healthcheck(cfg: AgentConfig) -> HealthResult:
    url = _health_url(cfg)
    headers = {"Accept": "application/json"}

    token = get_token(cfg)
    if token:
        if cfg.provider == "anthropic":
            headers["x-api-key"] = token
            headers["anthropic-version"] = "2023-06-01"
        elif cfg.provider == "azure_openai":
            headers["api-key"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url=url, headers=headers, method="GET")

    try:
        with request.urlopen(req, timeout=cfg.timeout_seconds) as resp:
            code = int(getattr(resp, "status", 200))
            # Read once to catch broken upstreams returning invalid body despite 200.
            _ = resp.read()
            return HealthResult(ok=True, status=code, message=f"Endpoint reachable ({code})")
    except error.HTTPError as e:
        msg = _extract_http_error(e)
        return HealthResult(ok=False, status=e.code, message=msg)
    except Exception as e:
        return HealthResult(ok=False, status=None, message=str(e))


def _health_url(cfg: AgentConfig) -> str:
    base = cfg.base_url.rstrip("/")
    if cfg.provider in ("openai", "openai_compatible"):
        return f"{base}/models"
    if cfg.provider == "anthropic":
        return f"{base}/v1/models"
    if cfg.provider == "azure_openai":
        return f"{base}/openai/models?api-version=2024-06-01"
    return f"{base}/models"


def _extract_http_error(exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""

    if not body:
        return f"HTTP {exc.code}"

    try:
        data = json.loads(body)
    except Exception:
        snippet = body.strip().replace("\n", " ")
        return f"HTTP {exc.code}: {snippet[:180]}"

    if isinstance(data, dict):
        if isinstance(data.get("error"), dict):
            emsg = data["error"].get("message") or data["error"].get("type")
            if emsg:
                return f"HTTP {exc.code}: {emsg}"
        if data.get("message"):
            return f"HTTP {exc.code}: {data['message']}"

    return f"HTTP {exc.code}"

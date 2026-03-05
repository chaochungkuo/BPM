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


@dataclass(frozen=True)
class ModelCheckResult:
    ok: bool
    message: str
    available_models: list[str]


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


def check_model_available(cfg: AgentConfig) -> ModelCheckResult:
    """
    Check whether the configured model is present in the provider model list.

    This is a best-effort check and depends on provider endpoint support.
    """
    try:
        models = list_models(cfg)
    except Exception as e:
        return ModelCheckResult(ok=False, message=f"Could not list models: {e}", available_models=[])

    if not models:
        return ModelCheckResult(ok=False, message="Model list is empty", available_models=[])

    if cfg.model in models:
        return ModelCheckResult(ok=True, message=f"Configured model found: {cfg.model}", available_models=models)

    # Some providers expose deployment IDs or aliases; allow case-insensitive fallback.
    lower_map = {m.lower(): m for m in models}
    if cfg.model.lower() in lower_map:
        return ModelCheckResult(
            ok=True,
            message=f"Configured model found (case-insensitive): {lower_map[cfg.model.lower()]}",
            available_models=models,
        )

    preview = ", ".join(models[:8])
    return ModelCheckResult(
        ok=False,
        message=f"Configured model '{cfg.model}' not in provider models: {preview}",
        available_models=models,
    )


def list_models(cfg: AgentConfig) -> list[str]:
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
    with request.urlopen(req, timeout=cfg.timeout_seconds) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    payload = json.loads(raw) if raw else {}
    data = payload.get("data") if isinstance(payload, dict) else None
    out: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                mid = item.get("id") or item.get("name")
                if isinstance(mid, str) and mid.strip():
                    out.append(mid.strip())
            elif isinstance(item, str):
                out.append(item.strip())
    return sorted(set(out))


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

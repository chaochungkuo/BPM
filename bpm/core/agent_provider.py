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

@dataclass(frozen=True)
class ChatResult:
    text: str


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

def chat(cfg: AgentConfig, messages: list[dict[str, str]]) -> ChatResult:
    """
    Send a chat request to the configured provider and return assistant text.
    """
    provider = cfg.provider
    if provider in ("openai", "openai_compatible", "azure_openai"):
        return _chat_openai_family(cfg, messages)
    if provider == "anthropic":
        return _chat_anthropic(cfg, messages)
    raise RuntimeError(f"Unsupported provider for chat: {provider}")


def _health_url(cfg: AgentConfig) -> str:
    base = cfg.base_url.rstrip("/")
    if cfg.provider in ("openai", "openai_compatible"):
        return f"{base}/models"
    if cfg.provider == "anthropic":
        return f"{base}/v1/models"
    if cfg.provider == "azure_openai":
        return f"{base}/openai/models?api-version=2024-06-01"
    return f"{base}/models"

def _chat_openai_family(cfg: AgentConfig, messages: list[dict[str, str]]) -> ChatResult:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token = get_token(cfg)
    if token:
        if cfg.provider == "azure_openai":
            headers["api-key"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"

    base = cfg.base_url.rstrip("/")
    if cfg.provider == "azure_openai":
        url = f"{base}/openai/deployments/{cfg.model}/chat/completions?api-version=2024-06-01"
        payload = {
            "messages": messages,
            "temperature": cfg.temperature,
            **_completion_tokens_field(cfg),
        }
    else:
        url = f"{base}/chat/completions"
        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": cfg.temperature,
            **_completion_tokens_field(cfg),
        }

    try:
        raw = _post_json(url=url, headers=headers, payload=payload, timeout=cfg.timeout_seconds)
    except RuntimeError as e:
        # Compatibility fallback for endpoints requiring max_completion_tokens.
        msg = str(e)
        if "max_tokens" in msg and "max_completion_tokens" in msg and "max_tokens" in payload:
            payload.pop("max_tokens", None)
            payload["max_completion_tokens"] = cfg.max_tokens
            raw = _post_json(url=url, headers=headers, payload=payload, timeout=cfg.timeout_seconds)
        else:
            raise
    try:
        data = json.loads(raw)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("No choices in chat response")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Empty assistant response")
        return ChatResult(text=content.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to parse chat response: {e}")

def _chat_anthropic(cfg: AgentConfig, messages: list[dict[str, str]]) -> ChatResult:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token = get_token(cfg)
    if token:
        headers["x-api-key"] = token
    headers["anthropic-version"] = "2023-06-01"

    base = cfg.base_url.rstrip("/")
    url = f"{base}/v1/messages"

    system_parts = []
    convo = []
    for m in messages:
        role = (m.get("role") or "").strip().lower()
        content = m.get("content") or ""
        if role == "system":
            system_parts.append(content)
            continue
        if role not in ("user", "assistant"):
            continue
        convo.append({"role": role, "content": content})

    payload = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "messages": convo,
    }
    if system_parts:
        payload["system"] = "\n\n".join(system_parts)

    raw = _post_json(url=url, headers=headers, payload=payload, timeout=cfg.timeout_seconds)
    try:
        data = json.loads(raw)
        content = data.get("content") or []
        if not isinstance(content, list) or not content:
            raise RuntimeError("No content in anthropic response")
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                txt = part.get("text")
                if isinstance(txt, str):
                    text_parts.append(txt)
        reply = "\n".join([t for t in text_parts if t.strip()]).strip()
        if not reply:
            raise RuntimeError("Empty assistant response")
        return ChatResult(text=reply)
    except Exception as e:
        raise RuntimeError(f"Failed to parse anthropic response: {e}")


def _completion_tokens_field(cfg: AgentConfig) -> dict[str, int]:
    # OpenAI gpt-5 family expects max_completion_tokens (not max_tokens).
    model = (cfg.model or "").strip().lower()
    if model.startswith("gpt-5"):
        return {"max_completion_tokens": cfg.max_tokens}
    return {"max_tokens": cfg.max_tokens}

def _post_json(url: str, headers: dict[str, str], payload: dict, timeout: int) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, headers=headers, data=data, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as e:
        msg = _extract_http_error(e)
        raise RuntimeError(msg)


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

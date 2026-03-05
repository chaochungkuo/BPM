from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover - py310 fallback
    import tomli as tomllib  # type: ignore

ProviderName = Literal["openai", "anthropic", "azure_openai", "openai_compatible"]
TokenSource = Literal["env", "keychain", "none"]


@dataclass(frozen=True)
class AgentConfig:
    version: int
    provider: ProviderName
    base_url: str
    model: str
    timeout_seconds: int
    max_tokens: int
    temperature: float
    token_source: TokenSource
    token_env_var: str


_DEFAULTS = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4.1"),
    "anthropic": ("https://api.anthropic.com", "ANTHROPIC_API_KEY", "claude-3-5-sonnet-latest"),
    "azure_openai": ("https://YOUR-RESOURCE.openai.azure.com", "AZURE_OPENAI_API_KEY", "gpt-4.1"),
    "openai_compatible": ("http://127.0.0.1:11434/v1", "", "llama3.1:8b"),
}


def get_agent_config_path() -> Path:
    override = os.environ.get("BPM_AGENT_CONFIG")
    if override:
        p = Path(override).expanduser().resolve()
    else:
        p = Path.home() / ".config" / "bpm" / "agent.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def defaults_for_provider(provider: ProviderName) -> tuple[str, str, str]:
    return _DEFAULTS[provider]


def config_exists() -> bool:
    return get_agent_config_path().exists()


def load_config() -> AgentConfig:
    path = get_agent_config_path()
    if not path.exists():
        raise RuntimeError(f"Agent config not found: {path}. Run `bpm agent config`.")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return _from_dict(data)


def save_config(cfg: AgentConfig) -> Path:
    path = get_agent_config_path()
    path.write_text(_to_toml(cfg), encoding="utf-8")
    return path


def validate_config(cfg: AgentConfig) -> None:
    valid_providers = set(_DEFAULTS.keys())
    if cfg.provider not in valid_providers:
        raise RuntimeError(f"Unsupported provider: {cfg.provider}")

    if not cfg.base_url.strip():
        raise RuntimeError("base_url is required")

    if not cfg.model.strip():
        raise RuntimeError("model is required")

    if cfg.timeout_seconds <= 0:
        raise RuntimeError("timeout_seconds must be > 0")

    if cfg.max_tokens <= 0:
        raise RuntimeError("max_tokens must be > 0")

    if cfg.temperature < 0 or cfg.temperature > 2:
        raise RuntimeError("temperature must be within [0, 2]")

    if cfg.token_source not in ("env", "keychain", "none"):
        raise RuntimeError(f"Unsupported token_source: {cfg.token_source}")

    if cfg.token_source == "env" and not cfg.token_env_var.strip():
        raise RuntimeError("token_env_var is required when token_source=env")


def get_token(cfg: AgentConfig) -> str | None:
    if cfg.token_source == "none":
        return None
    if cfg.token_source == "env":
        return os.environ.get(cfg.token_env_var) or None
    # keychain support can be added later
    return None


def _from_dict(raw: dict) -> AgentConfig:
    provider = raw.get("provider", "openai")
    base_default, token_default, model_default = _DEFAULTS.get(provider, _DEFAULTS["openai"])  # type: ignore[arg-type]

    cfg = AgentConfig(
        version=int(raw.get("version", 1)),
        provider=provider,
        base_url=str(raw.get("base_url", base_default)),
        model=str(raw.get("model", model_default)),
        timeout_seconds=int(raw.get("timeout_seconds", 60)),
        max_tokens=int(raw.get("max_tokens", 2000)),
        temperature=float(raw.get("temperature", 0.1)),
        token_source=raw.get("token_source", "env"),
        token_env_var=str(raw.get("token_env_var", token_default)),
    )
    validate_config(cfg)
    return cfg


def _to_toml(cfg: AgentConfig) -> str:
    return (
        f"version = {cfg.version}\n"
        f'provider = "{cfg.provider}"\n'
        f'base_url = "{cfg.base_url}"\n'
        f'model = "{cfg.model}"\n'
        f"timeout_seconds = {cfg.timeout_seconds}\n"
        f"max_tokens = {cfg.max_tokens}\n"
        f"temperature = {cfg.temperature}\n"
        f'token_source = "{cfg.token_source}"\n'
        f'token_env_var = "{cfg.token_env_var}"\n'
    )

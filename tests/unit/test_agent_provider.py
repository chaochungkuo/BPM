from bpm.core.agent_config import AgentConfig
from bpm.core import agent_provider


def _cfg(model: str) -> AgentConfig:
    return AgentConfig(
        version=1,
        provider="openai",
        base_url="https://api.openai.com/v1",
        model=model,
        timeout_seconds=60,
        max_tokens=123,
        temperature=0.1,
        token_source="none",
        token_env_var="",
    )


def test_completion_tokens_field_gpt5_uses_max_completion_tokens():
    cfg = _cfg("gpt-5-nano")
    field = agent_provider._completion_tokens_field(cfg)
    assert field == {"max_completion_tokens": 123}


def test_completion_tokens_field_non_gpt5_uses_max_tokens():
    cfg = _cfg("gpt-4.1")
    field = agent_provider._completion_tokens_field(cfg)
    assert field == {"max_tokens": 123}


def test_temperature_field_gpt5_omits_temperature():
    cfg = _cfg("gpt-5-nano")
    field = agent_provider._temperature_field(cfg)
    assert field == {}


def test_temperature_field_non_gpt5_includes_temperature():
    cfg = _cfg("gpt-4.1")
    field = agent_provider._temperature_field(cfg)
    assert field == {"temperature": 0.1}

"""Unit tests for configuration settings and named exceptions (Step 2 & Step 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from assistant_core.config import Settings, load_settings
from assistant_core.errors import (
    AssistantError,
    ConfigError,
    DataError,
    InvalidRequest,
    ProviderError,
)


def test_default_settings() -> None:
    """Settings should have sane defaults."""
    s = Settings()
    assert s.data_dir == Path("data")
    assert s.llm_provider == "stub"
    assert s.llm_api_key is None
    assert s.credit_rate_vnd == 450_000
    assert s.retake_multiplier == 1.5
    assert s.max_credits == 30
    assert s.log_level == "INFO"


def test_settings_custom_values() -> None:
    """Settings should accept valid custom values."""
    s = Settings(
        data_dir=Path("custom_data"),
        llm_provider="openai",
        llm_api_key="sk-test-key",
        credit_rate_vnd=500_000,
        retake_multiplier=2.0,
        max_credits=35,
        log_level="DEBUG",
    )
    assert s.data_dir == Path("custom_data")
    assert s.llm_provider == "openai"
    assert s.llm_api_key == "sk-test-key"
    assert s.credit_rate_vnd == 500_000
    assert s.retake_multiplier == 2.0
    assert s.max_credits == 35
    assert s.log_level == "DEBUG"


def test_api_key_hidden_in_repr() -> None:
    """API key must never be printed in repr(settings) or str(settings) (Twelve-Factor III)."""
    secret = "sk-super-secret-key-12345"
    s = Settings(llm_api_key=secret)
    assert secret not in repr(s)
    assert secret not in str(s)


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_settings without env variables should return defaults."""
    for var in [
        "ASSISTANT_DATA_DIR",
        "LLM_PROVIDER",
        "LLM_API_KEY",
        "CREDIT_RATE_VND",
        "RETAKE_MULTIPLIER",
        "MAX_CREDITS",
        "LOG_LEVEL",
    ]:
        monkeypatch.delenv(var, raising=False)

    s = load_settings(env_file=None)
    assert s.data_dir == Path("data")
    assert s.llm_provider == "stub"
    assert s.llm_api_key is None
    assert s.credit_rate_vnd == 450_000
    assert s.retake_multiplier == 1.5
    assert s.max_credits == 30
    assert s.log_level == "INFO"


def test_load_settings_from_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_settings should read configuration from environment variables."""
    monkeypatch.setenv("ASSISTANT_DATA_DIR", "custom/data/path")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.setenv("CREDIT_RATE_VND", "600000")
    monkeypatch.setenv("RETAKE_MULTIPLIER", "1.75")
    monkeypatch.setenv("MAX_CREDITS", "25")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    s = load_settings(env_file=None)
    assert s.data_dir == Path("custom/data/path")
    assert s.llm_provider == "stub"
    assert s.credit_rate_vnd == 600_000
    assert s.retake_multiplier == 1.75
    assert s.max_credits == 25
    assert s.log_level == "WARNING"


def test_load_settings_requires_api_key_when_provider_not_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When LLM_PROVIDER is not 'stub', LLM_API_KEY is strictly required."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    with pytest.raises(ConfigError, match=r"LLM_API_KEY is required when LLM_PROVIDER='openai'"):
        load_settings(env_file=None)


def test_load_settings_accepts_api_key_for_external_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When LLM_PROVIDER is not 'stub', providing LLM_API_KEY should succeed."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "sk-valid-key")

    s = load_settings(env_file=None)
    assert s.llm_provider == "openai"
    assert s.llm_api_key == "sk-valid-key"


def test_load_settings_invalid_numeric_env_raises_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid integer or float strings in env should raise ConfigError."""
    monkeypatch.setenv("MAX_CREDITS", "not-a-number")
    with pytest.raises(ConfigError, match=r"Invalid configuration numeric value"):
        load_settings(env_file=None)


def test_load_settings_from_dotenv_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_settings should read from the specified .env file."""
    for var in [
        "ASSISTANT_DATA_DIR",
        "LLM_PROVIDER",
        "LLM_API_KEY",
        "CREDIT_RATE_VND",
        "RETAKE_MULTIPLIER",
        "MAX_CREDITS",
        "LOG_LEVEL",
    ]:
        monkeypatch.delenv(var, raising=False)

    env_path = tmp_path / ".env.test"
    env_path.write_text(
        "ASSISTANT_DATA_DIR=test_data\n"
        "LLM_PROVIDER=stub\n"
        "CREDIT_RATE_VND=550000\n"
        "RETAKE_MULTIPLIER=1.8\n"
        "MAX_CREDITS=28\n"
        "LOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )

    s = load_settings(env_file=str(env_path))
    assert s.data_dir == Path("test_data")
    assert s.credit_rate_vnd == 550_000
    assert s.retake_multiplier == 1.8
    assert s.max_credits == 28
    assert s.log_level == "DEBUG"


def test_load_settings_override_false_preserves_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing shell environment variables should take precedence over .env (override=False)."""
    monkeypatch.setenv("CREDIT_RATE_VND", "999000")

    env_path = tmp_path / ".env.test"
    env_path.write_text("CREDIT_RATE_VND=111000\n", encoding="utf-8")

    s = load_settings(env_file=str(env_path))
    assert s.credit_rate_vnd == 999_000


def test_exception_hierarchy() -> None:
    """All custom exceptions must properly inherit from AssistantError."""
    assert issubclass(ConfigError, AssistantError)
    assert issubclass(DataError, AssistantError)
    assert issubclass(InvalidRequest, AssistantError)
    assert issubclass(ProviderError, AssistantError)
    assert issubclass(AssistantError, Exception)

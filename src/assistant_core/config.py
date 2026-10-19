"""Configuration settings for assistant_core."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from assistant_core.errors import ConfigError

__all__ = ["Settings", "load_settings"]


class Settings(BaseModel):
    """Runtime configuration for assistant_core."""

    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)  # never printed
    credit_rate_vnd: int = 450_000
    retake_multiplier: float = 1.5
    max_credits: int = 30
    log_level: str = "INFO"


def load_settings(env_file: str | None = ".env") -> Settings:
    """Load settings from environment variables, optionally reading an env file."""
    if env_file:
        load_dotenv(env_file, override=False)

    try:
        raw_credit_rate = os.getenv("CREDIT_RATE_VND", "450000")
        raw_retake_mult = os.getenv("RETAKE_MULTIPLIER", "1.5")
        raw_max_credits = os.getenv("MAX_CREDITS", "30")

        s = Settings(
            data_dir=Path(os.getenv("ASSISTANT_DATA_DIR", "data")),
            llm_provider=os.getenv("LLM_PROVIDER", "stub"),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            credit_rate_vnd=int(raw_credit_rate),
            retake_multiplier=float(raw_retake_mult),
            max_credits=int(raw_max_credits),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    except ValueError as exc:
        raise ConfigError(f"Invalid configuration numeric value: {exc}") from exc

    if s.llm_provider != "stub" and not s.llm_api_key:
        raise ConfigError(f"LLM_API_KEY is required when LLM_PROVIDER={s.llm_provider!r}")

    return s

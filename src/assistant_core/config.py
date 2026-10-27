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
    llm_timeout_s: float = 5.0
    credit_rate_vnd: int = 450_000
    retake_multiplier: float = 1.5
    max_credits: int = 30
    log_level: str = "INFO"
    # Lab 4 — API
    api_admin_key: str | None = Field(default=None, repr=False)
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_s: float = 3.0
    campus_lat: float = 10.7626  # University of Science, HCMC (Nguyen Van Cu campus)
    campus_lon: float = 106.6822
    rate_limit_per_min: int = 30


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
            llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S", "5")),
            credit_rate_vnd=int(raw_credit_rate),
            retake_multiplier=float(raw_retake_mult),
            max_credits=int(raw_max_credits),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_admin_key=os.getenv("API_ADMIN_KEY") or None,
            weather_url=os.getenv("WEATHER_URL", "https://api.open-meteo.com/v1/forecast"),
            weather_timeout_s=float(os.getenv("WEATHER_TIMEOUT_S", "3")),
            campus_lat=float(os.getenv("CAMPUS_LAT", "10.7626")),
            campus_lon=float(os.getenv("CAMPUS_LON", "106.6822")),
            rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "30")),
        )
    except ValueError as exc:
        raise ConfigError(f"Invalid configuration numeric value: {exc}") from exc

    if s.llm_provider != "stub" and not s.llm_api_key:
        raise ConfigError(f"LLM_API_KEY is required when LLM_PROVIDER={s.llm_provider!r}")

    return s

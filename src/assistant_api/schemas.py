"""HTTP request/response schemas — the public API contract (v1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from assistant_core.models import Intent, Source


def _validate_text(value: str, *, allow_blank: bool = False) -> str:
    """Reject null bytes and blank strings, trimming surrounding whitespace."""
    if "\x00" in value:
        raise ValueError("must not contain null bytes")
    cleaned = value.strip()
    if not allow_blank and not cleaned:
        raise ValueError("must not be blank")
    return cleaned


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, examples=["tuition for 18 credits and 2 retake"])
    session_id: str = Field(default="anonymous", min_length=1, max_length=64)

    @field_validator("message", "session_id")
    @classmethod
    def _check_non_blank_fields(cls, value: str) -> str:
        return _validate_text(value)


class ChatResponse(BaseModel):
    answer: str
    intent: Intent
    sources: list[Source] = []
    degraded: bool = False
    escalate: bool = False
    path: str = "deterministic"
    confidence: float | None = None
    request_id: str


class FeedbackIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=-1, le=1, description="-1 = thumbs down, 0 = neutral, 1 = thumbs up")
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("request_id")
    @classmethod
    def _check_request_id(cls, value: str) -> str:
        return _validate_text(value)

    @field_validator("comment")
    @classmethod
    def _check_comment(cls, value: str | None) -> str | None:
        return None if value is None else _validate_text(value, allow_blank=True)


class FeedbackOut(FeedbackIn):
    id: int
    created_at: datetime


class Weather(BaseModel):
    temperature_c: float
    wind_kmh: float
    description: str
    observed_at: str
    stale: bool = False  # True when served from cache after an upstream failure


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody

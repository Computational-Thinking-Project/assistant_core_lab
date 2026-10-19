"""Domain models for assistant_core.

Phụ trách: Thành viên 3 (Đạt)
Phạm vi: Intent, Message, Source, Response
"""

from enum import Enum
from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Supported intent categories."""

    GREETING = "greeting"
    FEE = "fee"
    OFFICE = "office"
    RULE = "rule"
    UNKNOWN = "unknown"


class Message(BaseModel):
    """User input message with validation boundary."""

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = "local"


class Source(BaseModel):
    """Knowledge reference source cited in an answer."""

    id: str
    title: str


class Response(BaseModel):
    """Public service response contract."""

    answer: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    degraded: bool = False

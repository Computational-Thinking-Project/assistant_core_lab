"""Shared pytest fixtures for assistant_core test suite.

Phụ trách: Thành viên 7 (Tâm @AI-WFox) phối hợp cùng toàn nhóm.
"""

from pathlib import Path
from typing import Any

import pytest

from assistant_core.service import AssistantService, ProviderError

# Resilient imports: support standalone module or service internal fallback
try:
    from assistant_core.config import Settings
except (ImportError, AttributeError):
    Settings = None  # type: ignore

try:
    from assistant_core.knowledge import Handbook, Office, OfficeDirectory, Rule
except (ImportError, AttributeError):
    Handbook = None  # type: ignore
    Office = None  # type: ignore
    OfficeDirectory = None  # type: ignore
    Rule = None  # type: ignore

try:
    from assistant_core.responder import StubLLMResponder, TemplateResponder
except (ImportError, AttributeError):
    StubLLMResponder = None  # type: ignore
    TemplateResponder = None  # type: ignore


class MockFailingResponder:
    """Mock responder simulating LLM provider outage with ProviderError."""

    def explain(self, question: str, rule: Any) -> str:
        raise ProviderError("Simulated LLM API failure (503 Service Unavailable)")


class MockCustomResponder:
    """Mock responder returning deterministic simulated AI response."""

    def explain(self, question: str, rule: Any) -> str:
        rule_id = getattr(rule, "id", rule.get("id", "") if isinstance(rule, dict) else "")
        return f"AI Explanation for '{question}' based on {rule_id}"


class MockSettings:
    """Mock settings matching Settings contract."""

    def __init__(
        self,
        data_dir: Path | None = None,
        llm_provider: str = "stub",
        llm_api_key: str | None = None,
        credit_rate_vnd: int = 450_000,
        retake_multiplier: float = 1.5,
        max_credits: int = 30,
        log_level: str = "INFO",
    ):
        self.data_dir = data_dir or Path("data")
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.credit_rate_vnd = credit_rate_vnd
        self.retake_multiplier = retake_multiplier
        self.max_credits = max_credits
        self.log_level = log_level


@pytest.fixture
def test_settings(tmp_path: Path):
    """Provide a deterministic test Settings instance."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    if Settings is not None:
        try:
            return Settings(
                data_dir=data_dir,
                llm_provider="stub",
                llm_api_key=None,
                credit_rate_vnd=450_000,
                retake_multiplier=1.5,
                max_credits=30,
                log_level="INFO",
            )
        except (TypeError, ValueError, AttributeError):
            pass
    return MockSettings(data_dir=data_dir)


@pytest.fixture
def failing_responder():
    """Stub responder simulating provider outage (throws ProviderError)."""
    return MockFailingResponder()


@pytest.fixture
def custom_responder():
    """Stub responder returning deterministic simulated response."""
    return MockCustomResponder()


@pytest.fixture
def service():
    """Provide an AssistantService instance configured with default characterisation data."""
    return AssistantService()

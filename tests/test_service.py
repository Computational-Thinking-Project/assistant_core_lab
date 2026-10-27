"""Integration and characterisation tests for AssistantService.

Owner: Member 7 (Tam @AI-WFox) in collaboration with Member 1 (Duy @johannguyen015).
Scope: Comprehensive integration coverage for AssistantService, characterisation tests,
       Pydantic schema boundaries, and AI provider fallback handling.
"""

import pytest
from pydantic import ValidationError

from assistant_core.service import (
    AssistantService,
    Intent,
    Message,
)


def test_greeting_intent(service):
    """Verify greeting intent with English keywords."""
    resp = service.handle(Message(text="hi"))
    assert resp.intent == Intent.GREETING
    assert resp.answer == "Hello! I can help with offices, fees and rules."
    assert resp.degraded is False
    assert resp.sources == []


def test_greeting_vietnamese(service):
    """Verify greeting intent with Vietnamese phrase 'xin chao'."""
    resp = service.handle(Message(text="xin chao"))
    assert resp.intent == Intent.GREETING
    assert "Hello!" in resp.answer
    assert resp.degraded is False


def test_fee_calculation_characterisation(service):
    """Characterisation test: 18 credits and 2 retakes MUST produce 9,450,000 VND.

    Formula: 18 * 450,000 + 2 * 450,000 * 1.5 = 8,100,000 + 1,350,000 = 9,450,000 VND.
    Matches exact behavior of the legacy monolith.
    """
    resp = service.handle(Message(text="tuition for 18 credits and 2 retake"))
    assert resp.intent == Intent.FEE
    assert "9450000" in resp.answer or "9,450,000" in resp.answer
    assert resp.degraded is False


def test_fee_zero_credits(service):
    """Fee query missing credit count prompts user for clarification."""
    resp = service.handle(Message(text="what is the tuition fee?"))
    assert resp.intent == Intent.FEE
    assert resp.answer == "How many credits?"


def test_fee_too_many_credits(service):
    """Credits exceeding MAX_CREDITS (30) returns error response."""
    resp = service.handle(Message(text="tuition for 40 credits"))
    assert resp.intent == Intent.FEE
    assert resp.answer == "too many credits"


def test_fee_custom_settings():
    """Service respects custom injected rate, multiplier, and max_credits."""

    class CustomSettings:
        credit_rate_vnd = 500_000
        retake_multiplier = 2.0
        max_credits = 25

    custom_service = AssistantService(settings=CustomSettings())
    # 10 credits * 500_000 + 1 retake * 500_000 * 2.0 = 5_000_000 + 1_000_000 = 6_000_000 VND
    resp = custom_service.handle(Message(text="tuition 10 credits and 1 retake"))
    assert "6000000" in resp.answer or "6,000,000" in resp.answer

    # Exceeding custom max_credits (25)
    resp_over = custom_service.handle(Message(text="tuition 26 credits"))
    assert resp_over.answer == "too many credits"


def test_office_lookup_library(service):
    """Verify lookup for library office returns room and hours."""
    resp = service.handle(Message(text="where is the library"))
    assert resp.intent == Intent.OFFICE
    assert "Library: room B.201, open Mon-Sat 07:00-20:00" in resp.answer
    assert len(resp.sources) == 1
    assert "library" in resp.sources[0].id.lower()
    assert resp.degraded is False


def test_office_lookup_training_office(service):
    """Verify lookup for training office."""
    resp = service.handle(Message(text="find the training office"))
    assert resp.intent == Intent.OFFICE
    assert "Training Office: room I.101" in resp.answer


def test_rule_lookup_success(service):
    """Rule query matching handbook keyword returns answer with source."""
    resp = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.intent == Intent.RULE
    assert len(resp.sources) >= 1
    assert resp.sources[0].id == "H26-5.3"
    assert resp.degraded is False


def test_rule_fallback_on_provider_error(service, failing_responder):
    """Critical QA gate: When provider fails with ProviderError, service gracefully falls back to template."""
    service.responder = failing_responder
    resp = service.handle(Message(text="can I register my thesis with 118 credits"))

    assert resp.intent == Intent.RULE
    assert resp.degraded is True
    assert len(resp.sources) == 1
    assert resp.sources[0].id == "H26-5.3"
    # Fallback should provide handbook rule text
    assert "120 accumulated credits" in resp.answer


def test_rule_custom_responder(service, custom_responder):
    """Custom injected responder is called during normal operation."""
    service.responder = custom_responder
    resp = service.handle(Message(text="what is the credit load rule?"))
    assert resp.intent == Intent.RULE
    assert "AI Explanation" in resp.answer
    assert resp.degraded is False


def test_unknown_query(service):
    """Irrelevant or unsupported query falls back to UNKNOWN intent."""
    resp = service.handle(Message(text="can you make me a pizza"))
    assert resp.intent == Intent.UNKNOWN
    assert resp.answer == "Sorry I dont know"
    assert resp.degraded is False


def test_empty_message_handling(service):
    """Blank whitespace string is safely handled."""
    resp = service.handle(Message(text="   "))
    assert resp.answer == "empty"
    assert resp.intent == Intent.UNKNOWN


def test_message_pydantic_boundary_validation():
    """Verify Pydantic Message model rejects empty string at schema level."""
    with pytest.raises(ValidationError):
        Message(text="")


def test_message_pydantic_max_length_validation():
    """Verify Pydantic Message model rejects string exceeding 2000 chars."""
    with pytest.raises(ValidationError):
        Message(text="x" * 2001)


def test_session_id_propagation(service, caplog):
    """Session ID is preserved across handling and recorded in structured logs."""
    import logging

    with caplog.at_level(logging.INFO):
        msg = Message(text="hello", session_id="user-session-42")
        resp = service.handle(msg)
        assert resp.intent == Intent.GREETING
        assert any(
            getattr(record, "session", None) == "user-session-42" or "user-session-42" in record.getMessage()
            for record in caplog.records
        )

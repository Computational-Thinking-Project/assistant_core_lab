"""Unit and integration tests for AssistantService.

Phụ trách: Thành viên 1 (Duy @johannguyen015) phối hợp cùng Thành viên 7 (Tâm @benalexx007)
"""

from typing import Any

from assistant_core.service import AssistantService, Intent, Message, ProviderError


class MockFailingResponder:
    """Mock responder simulating LLM provider outage."""

    def explain(self, question: str, rule: Any) -> str:
        raise ProviderError("Simulated LLM API failure (503 Service Unavailable)")


class MockCustomResponder:
    """Mock responder returning deterministic simulated AI response."""

    def explain(self, question: str, rule: Any) -> str:
        rule_id = getattr(rule, "id", rule.get("id", ""))
        return f"AI Explanation for '{question}' based on {rule_id}"


def test_greeting_intent():
    service = AssistantService()
    resp = service.handle(Message(text="hi"))
    assert resp.intent == Intent.GREETING
    assert resp.answer == "Hello! I can help with offices, fees and rules."
    assert resp.degraded is False


def test_greeting_vietnamese():
    service = AssistantService()
    resp = service.handle(Message(text="xin chao"))
    assert resp.intent == Intent.GREETING
    assert "Hello!" in resp.answer


def test_fee_calculation_with_retake():
    service = AssistantService()
    resp = service.handle(Message(text="tuition for 18 credits and 2 retake"))
    assert resp.intent == Intent.FEE
    assert resp.answer == "Your tuition is 9450000 VND"
    assert resp.degraded is False


def test_fee_zero_credits():
    service = AssistantService()
    resp = service.handle(Message(text="what is the tuition fee?"))
    assert resp.intent == Intent.FEE
    assert resp.answer == "How many credits?"


def test_fee_too_many_credits():
    service = AssistantService()
    resp = service.handle(Message(text="tuition for 40 credits"))
    assert resp.intent == Intent.FEE
    assert resp.answer == "too many credits"


def test_office_lookup_library():
    service = AssistantService()
    resp = service.handle(Message(text="where is the library"))
    assert resp.intent == Intent.OFFICE
    assert "Library: room B.201, open Mon-Sat 07:00-20:00" in resp.answer
    assert len(resp.sources) == 1
    assert "library" in resp.sources[0].id.lower()


def test_rule_lookup_success():
    service = AssistantService()
    resp = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.intent == Intent.RULE
    assert len(resp.sources) >= 1
    assert resp.sources[0].id == "H26-5.3"
    assert resp.degraded is False


def test_rule_fallback_on_provider_error():
    """Verify that when primary responder throws ProviderError, fallback is used and degraded=True."""
    failing_responder = MockFailingResponder()
    service = AssistantService(responder=failing_responder)

    resp = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.intent == Intent.RULE
    assert resp.degraded is True
    assert len(resp.sources) == 1
    assert resp.sources[0].id == "H26-5.3"
    # Fallback should provide handbook rule text
    assert "120 accumulated credits" in resp.answer


def test_unknown_query():
    service = AssistantService()
    resp = service.handle(Message(text="can you make me a pizza"))
    assert resp.intent == Intent.UNKNOWN
    assert resp.answer == "Sorry I dont know"


def test_empty_message():
    service = AssistantService()
    resp = service.handle(Message(text="   "))
    assert resp.answer == "empty"
    assert resp.intent == Intent.UNKNOWN


def test_custom_injected_settings():
    class CustomSettings:
        credit_rate_vnd = 500_000
        retake_multiplier = 2.0
        max_credits = 25

    service = AssistantService(settings=CustomSettings())
    # 10 credits * 500_000 + 1 retake * 500_000 * 2.0 = 5_000_000 + 1_000_000 = 6_000_000 VND
    resp = service.handle(Message(text="tuition 10 credits and 1 retake"))
    assert resp.answer == "Your tuition is 6000000 VND"

    # Exceeding custom max_credits (25)
    resp_over = service.handle(Message(text="tuition 26 credits"))
    assert resp_over.answer == "too many credits"


def test_custom_injected_responder():
    custom_responder = MockCustomResponder()
    service = AssistantService(responder=custom_responder)
    resp = service.handle(Message(text="what is the credit load rule?"))
    assert resp.intent == Intent.RULE
    assert "AI Explanation" in resp.answer
    assert resp.degraded is False


def test_session_id_propagation():
    service = AssistantService()
    msg = Message(text="hello", session_id="user-session-42")
    resp = service.handle(msg)
    assert resp.intent == Intent.GREETING

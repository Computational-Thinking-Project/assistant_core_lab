"""H1 help feature: routing boundaries, service metadata and CLI output."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from assistant_core.models import Intent, Message
from assistant_core.router import HELP_COMMANDS, route
from assistant_core.service import AssistantService, _default_route


@pytest.mark.parametrize("text", ["help", " HELP ", "Help!", "help?", "?", "-h", "--help", "guide", "GUIDE!"])
def test_help_route(text: str) -> None:
    assert "-h" in HELP_COMMANDS and "--help" in HELP_COMMANDS
    assert route(text, {"it helpdesk"}) is Intent.HELP


def test_help_does_not_capture_other_questions() -> None:
    assert route("where is the it helpdesk", {"it helpdesk"}) is Intent.OFFICE
    assert route("help me with tuition", set()) is Intent.FEE
    assert route("help with thesis registration", set()) is Intent.RULE
    assert route("guide to thesis registration", set()) is Intent.RULE


def test_help_response_works_without_provider_or_knowledge() -> None:
    class NeverResponder:
        def explain(self, question: str, rule: object) -> str:
            pytest.fail("Help must not call a responder")

    service = AssistantService(responder=NeverResponder())
    response = service.handle(Message(text="help"))
    assert response.intent is Intent.HELP
    assert response.sources == [] and response.degraded is False
    for example in ("hi", "tuition for 18 credits and 2 retake", "where is the library", "thesis"):
        assert example in response.answer


def test_help_fallback_router_matches_public_router() -> None:
    for text in ("help", "HELP?!", "?", "-h", "--help", "guide", "help me with tuition", "where is the it helpdesk"):
        assert _default_route(text, {"it helpdesk"}) is route(text, {"it helpdesk"})


def test_help_serialization_and_private_logging(caplog: pytest.LogCaptureFixture) -> None:
    raw_text = "  HELP?!  "
    with caplog.at_level("INFO", logger="assistant_core.service"):
        response = AssistantService().handle(Message(text=raw_text))
    payload = response.model_dump(mode="json")
    assert payload["intent"] == "help"
    assert payload["sources"] == [] and payload["degraded"] is False
    assert raw_text not in caplog.text
    assert caplog.records[-1].intent == "help"


@pytest.mark.parametrize("flag", ["help", "-h", "--help", "?"])
def test_cli_help_preserves_stdout_and_metadata_logs(flag: str) -> None:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "assistant_core", flag],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "I can help with:" in result.stdout
    assert '"intent": "help"' in result.stderr
    assert "Traceback" not in result.stderr

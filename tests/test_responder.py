"""Tests for responders and structured logging.

Phụ trách: Thành viên 6
"""

import json
import logging

import pytest

from assistant_core.logging_setup import JsonFormatter, setup_logging


@pytest.fixture
def rule():
    # Import here so logging tests can run before the knowledge module is ready.
    from assistant_core.knowledge import Rule

    return Rule(id="registration", title="Registration", text="Register before the deadline.")


@pytest.fixture
def package_logger():
    """Keep tests from changing the application's existing logger settings."""
    logger = logging.getLogger("assistant_core")
    old_handlers = logger.handlers[:]
    old_level = logger.level
    old_propagate = logger.propagate
    old_disabled = logger.disabled
    logger.handlers = []
    logger.disabled = False
    try:
        yield logger
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.handlers = old_handlers
        logger.setLevel(old_level)
        logger.propagate = old_propagate
        logger.disabled = old_disabled


def test_template_responder(rule):
    from assistant_core.responder import TemplateResponder

    assert TemplateResponder().explain("When should I register?", rule) == (
        "Registration: Register before the deadline."
    )


def test_stub_responder_is_deterministic(rule):
    from assistant_core.responder import StubLLMResponder

    responder = StubLLMResponder()
    expected = "Based on 'Registration': Register before the deadline."
    assert responder.explain("When should I register?", rule) == expected
    assert responder.explain("When should I register?", rule) == expected


def test_stub_failure_has_safe_message(rule, capsys):
    from assistant_core.errors import ProviderError
    from assistant_core.responder import StubLLMResponder

    question = "PRIVATE_USER_QUESTION"
    with pytest.raises(ProviderError) as error:
        StubLLMResponder(fail=True).explain(question, rule)

    assert str(error.value) == "stub provider unavailable"
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert question not in str(error.value)


def test_json_formatter_basic_fields():
    record = logging.LogRecord("assistant_core", logging.INFO, __file__, 1, "handled %s", ("request",), None)

    assert json.loads(JsonFormatter().format(record)) == {
        "level": "INFO",
        "logger": "assistant_core",
        "msg": "handled request",
    }


def test_json_formatter_context_fields():
    record = logging.LogRecord("assistant_core", logging.WARNING, __file__, 1, "fallback", (), None)
    record.intent = "rule"
    record.latency_ms = 0.1
    record.session = "local"
    record.degraded = True

    assert json.loads(JsonFormatter().format(record)) == {
        "level": "WARNING",
        "logger": "assistant_core",
        "msg": "fallback",
        "intent": "rule",
        "latency_ms": 0.1,
        "session": "local",
        "degraded": True,
    }


def test_logging_excludes_unapproved_extras(package_logger, capsys):
    setup_logging()
    package_logger.info("handled", extra={"api_key": "TEST_SECRET", "question": "PRIVATE_USER_QUESTION"})

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {"level": "INFO", "logger": "assistant_core", "msg": "handled"}


def test_setup_logging_uses_stderr(package_logger, capsys):
    setup_logging()
    logging.getLogger("assistant_core.service").info("handled")
    print("Answer")

    captured = capsys.readouterr()
    assert captured.out == "Answer\n"
    assert json.loads(captured.err)["logger"] == "assistant_core.service"


def test_setup_logging_does_not_duplicate_messages(package_logger, capsys):
    setup_logging()
    setup_logging()
    package_logger.info("handled")

    lines = capsys.readouterr().err.splitlines()
    assert len(package_logger.handlers) == 1
    assert len(lines) == 1
    assert json.loads(lines[0])["msg"] == "handled"


def test_setup_logging_respects_level(package_logger, capsys):
    setup_logging("WARNING")
    package_logger.info("hidden")
    package_logger.warning("provider failed; using template fallback")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["level"] == "WARNING"
    assert "hidden" not in captured.err

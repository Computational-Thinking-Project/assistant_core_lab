"""Structured JSON logging setup.

Phụ trách: Thành viên 6
Phạm vi: JsonFormatter, setup_logging()
"""

import json
import logging
from typing import TextIO


class JsonFormatter(logging.Formatter):
    """Include only the message and explicitly allowed context fields.

    Callers must use safe event messages, never API keys or raw user questions.
    """

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("intent", "latency_ms", "session", "degraded"):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str = "INFO", stream: TextIO | None = None) -> None:
    """Emit JSON to the supplied stream (stderr by default), without duplicates."""
    logger = logging.getLogger("assistant_core")
    logger.setLevel(level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False

"""assistant_core: A maintainable Python service for student assistance."""

from assistant_core.service import AssistantService, Intent, Message, Response, Source, build_service

__version__ = "0.3.0"

__all__ = [
    "AssistantService",
    "Intent",
    "Message",
    "Response",
    "Source",
    "build_service",
    "__version__",
]

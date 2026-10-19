"""CLI entry point for assistant_core.

Phụ trách: Thành viên 1 (Duy @johannguyen015)
Phạm vi: CLI argument parsing, interactive REPL, and execution
"""

from __future__ import annotations

import logging
import sys

from assistant_core.service import AssistantService, Message


def setup_cli_logging() -> None:
    """Configure structured or basic logging to stderr so stdout remains clean for CLI responses."""
    try:
        from assistant_core.logging_setup import setup_logging

        setup_logging(stream=sys.stderr)
    except (ImportError, AttributeError):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stderr,
        )


def run_test_suite(service: AssistantService) -> None:
    """Run characterisation test inputs from monolith to verify backwards compatibility."""
    queries = [
        "hi",
        "tuition for 18 credits and 2 retake",
        "where is the library",
        "can I register my thesis with 118 credits",
        "tuition 40 credits",
        "",
    ]
    for q in queries:
        resp = service.handle(Message(text=q) if q.strip() else q)
        print(resp.answer)


def run_interactive_repl(service: AssistantService) -> None:
    """Run interactive REPL loop matching original monolith CLI."""
    print("assistant ready")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line == "quit":
            break
        if not line:
            print("empty")
            continue
        resp = service.handle(Message(text=line))
        print(resp.answer)


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]
    setup_cli_logging()
    service = AssistantService()

    if "--test" in args:
        run_test_suite(service)
        return

    if args:
        query = " ".join(args)
        resp = service.handle(Message(text=query))
        print(resp.answer)
        return

    run_interactive_repl(service)


if __name__ == "__main__":
    main()

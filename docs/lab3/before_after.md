# Lab 3 — Before / after maintainability comparison

Fill in for the monolith (before) and your refactored package (after).

| Question | Before | After |
|---|---|---|
| Where would you change the credit rate? How many places? | 1 constant in code (`RATE` in `assistant_monolith.py`) | 1 variable in `.env` (`CREDIT_RATE_VND`) |
| Can you run the tests without internet or an API key? | No (simulated LLM, flaky random failures) | Yes (deterministic tests with `StubLLMResponder` and unit tests) |
| What happens if `handbook.json` is missing? | Prints error and continues silently (`None` returned) | Raises explicit `DataError` at startup/load |
| Is any secret printed or logged? | Yes (`API_KEY` printed in debug output) | No (`repr=False` on `llm_api_key`, never logged) |
| How long does it take a new teammate to find the fee logic? | Needs to inspect monolith's 65-line `handle()` function | Directly in `src/assistant_core/tools.py` |
| Number of global variables | 9 (3 mutable: `history`, `offices`, `handbook`) | 0 (encapsulated in classes and injected dependencies) |
| Number of bare `except:` blocks | 3 (`load()`, `main()`, etc.) | 0 (all use specific exception classes or built-ins) |
| Lines in the longest function | ~65 (`handle()`) | ~15-20 |
| `ruff check` issues | Many | 0 clean |
| Can you swap the LLM without touching the service? | No (hardcoded in monolith) | Yes (via `Responder` protocol / dependency injection) |

**Three sentences:** what improved most, what got more complex, and what you would still change.
- **What improved most:** The architecture achieves high cohesion and loose coupling; business rules (fees, knowledge lookup, routing) are now pure, deterministic, and independently testable without global state or mock network calls.
- **What got more complex:** The project introduces multiple files, type models (Pydantic), and dependency injection, which requires understanding the module layout and contracts.
- **What you would still change:** In future iterations (e.g., Lab 4/Week 4), integrate real LLM providers asynchronously and add persistent database storage for conversation history.

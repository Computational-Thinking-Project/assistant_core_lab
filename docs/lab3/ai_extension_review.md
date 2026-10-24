# Lab 3 — AI extension review

**Student:** Truong Thanh Dat (MSSV: 25127035, GitHub: `@Thanhdat3010`)  
**Feature:** Help command listing assistant capabilities (`help` / `?` / `-h` / `--help`)  
**Issue:** [#18](https://github.com/Computational-Thinking-Project/assistant_core_lab/issues/18)  
**PR:** [#19](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/19)  

---

### 1. Feature Selected
Extend `assistant_core` with a deterministic `help` intent that lists available capabilities (greetings, tuition calculations, office lookup, and handbook rules) without making external API calls or introducing new dependencies.

### 2. Prompt Used
```text
"Extend assistant_core with a deterministic help command listing existing capabilities (greetings, tuition calculation, office lookups, and handbook rules), adhering strictly to the Message -> route -> AssistantService -> Response interface without external API dependencies."
```

### 3. Review of Generated Code & Three Personal Improvements

| # | What the AI generated | Problem you found | What you changed | Why |
|---|---|---|---|---|
| 1 | AI only matched exact literal strings `"help"` and `"?"` in the public router, ignoring standard CLI conventions. | Users expecting standard command-line flags (`-h`, `--help`, `guide`) or uppercase variants received `Intent.UNKNOWN` or fell into rule lookup. Furthermore, the internal fallback router `_default_route` lacked parity. | Defined `HELP_COMMANDS = frozenset({"help", "?", "-h", "--help", "guide"})` in `router.py`, applied matching across both public and fallback routers, and preserved specialized queries like `"guide to thesis"` for rule handlers. | Conforms to UNIX CLI conventions and guarantees deterministic, consistent routing across all execution paths. |
| 2 | Initial test mutated the resolved `responder.explain` method directly on the service instance. | Modifying a live responder instance in tests violates black-box testing and risks state pollution across test runs. | Refactored the test suite to use constructor dependency injection with a mock `NeverResponder` that raises an error if invoked. | Verifies conclusively that help responses are 100% deterministic, offline, and never leak calls to an LLM provider. |
| 3 | AI implementation did not verify serialized response structure, CLI invocation flags, or check log privacy. | Without strict schema assertions and log auditing, responses could drift from the API contract or inadvertently log user message contents to stderr. | Added explicit JSON assertions (`degraded=False`, `sources=[]`), parameterized CLI test runs (`"-h"`, `"--help"`), and inspected `JsonFormatter` stderr output to ensure only operational metadata (`intent`, `latency_ms`, `session`) is logged without echoing raw user text. | Enforces strict API contract compliance and adheres to the course privacy rules regarding student data. |

---

### Checklist
- [x] Interfaces respected (`Message -> route -> AssistantService -> Response`)
- [x] No new external dependencies introduced
- [x] No API keys, secrets, or personal user data exposed
- [x] Logging records only structured metadata to stderr, leaving stdout clean
- [x] Comprehensive unit tests added (104 passing tests)
- [x] Recorded in `docs/ai-use-log.md`

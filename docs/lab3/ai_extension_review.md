# Lab 3 — AI extension review

**Student:** Truong Thanh Dat (MSSV: 25127035, GitHub: `@Thanhdat3010`)  
**Feature:** Help command listing assistant capabilities (`help` / `?`)  
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
| 1 | AI only added exact string match `"help"` and `"?"` in the public `route()` function. | The internal fallback router `_default_route()` did not recognise `help`, creating inconsistent routing between primary and fallback routes. Additionally, queries like `"help?"` or `"help me with tuition"` risked ambiguous matching. | Added equivalent help handling to `_default_route()`, stripped trailing punctuation in normalization, and ensured specialized queries (e.g. tuition help) remain routed to their dedicated handlers. | Ensures uniform behavior across all service entry routes and avoids misrouting complex student inquiries. |
| 2 | Initial test mutated the resolved `responder.explain` method directly on the service instance. | Modifying a live responder instance in tests violates black-box testing and risks state pollution across test runs. | Refactored the test suite to use constructor dependency injection with a mock `NeverResponder` that raises an error if invoked. | Verifies conclusively that help responses are 100% deterministic, offline, and never leak calls to an LLM provider. |
| 3 | AI implementation did not verify serialized response structure or check log privacy. | Without strict schema assertions and log auditing, responses could drift from the API contract or inadvertently log user message contents to stderr. | Added explicit JSON assertions (`degraded=False`, `sources=[]`) and inspected `JsonFormatter` stderr output to ensure only operational metadata (`intent`, `latency_ms`, `session`) is logged without echoing raw user text. | Enforces strict API contract compliance and adheres to the course privacy rules regarding student data. |

---

### Checklist
- [x] Interfaces respected (`Message -> route -> AssistantService -> Response`)
- [x] No new external dependencies introduced
- [x] No API keys, secrets, or personal user data exposed
- [x] Logging records only structured metadata to stderr, leaving stdout clean
- [x] Comprehensive unit tests added (100% passing)
- [x] Recorded in `docs/ai-use-log.md`

# Lab03 H3 — Reading Notes and Architectural Reflection

**Student:** Truong Thanh Dat (MSSV: 25127035, GitHub: `@Thanhdat3010`)  
**Context:** Lab 03 Refactoring Monolith to Maintainable Service Architecture  

---

## 1. Required Reading Summary

| Source | Core Concept | Application in `assistant_core` |
|---|---|---|
| [I - Codebase](https://12factor.net/codebase) | One codebase tracked in revision control, many deploys. | Code is organized in a single repository with feature branching (`feat/`, `fix/`), clear commit history, and automated CI quality checks. |
| [II - Dependencies](https://12factor.net/dependencies) | Explicitly declare and isolate dependencies. | All dependencies are explicitly declared in `pyproject.toml` with pinned versions in `requirements.txt`. Development occurs within an isolated `.venv` without relying on implicit system tools. |
| [III - Config](https://12factor.net/config) | Store configuration in the environment, separated from code. | Hard-coded constants (such as rates, multipliers, and keys) were extracted into `.env`, validated via `Settings` (Pydantic), and documented in `.env.example`. |
| [XI - Logs](https://12factor.net/logs) | Treat logs as event streams emitted to output streams. | Replaced arbitrary `print()` statements with structured JSON logging directed to `stderr`, leaving `stdout` dedicated strictly to user responses. |
| [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/) | Use standardized project metadata and package layout. | Structured under `src/assistant_core/` with `pyproject.toml` and setuptools build backend, allowing clean editable installation (`pip install -e .`). |

---

## 2. Personal Architectural Reflection

### Which factor did the monolith violate most severely?
In my evaluation of `assistant_monolith.py`, the most critical violation was **Factor III: Config (Store config in the environment)**.

In the original monolith script:
1. Business rates (`RATE = 450000`, `RETAKE_MULTIPLIER = 1.5`), system parameters (`MAX_CREDITS = 30`), and sensitive credentials (`API_KEY = "sk-test-..."`) were hard-coded directly into the source file.
2. Whenever a tuition rate changed or a credential needed rotation, developers were forced to edit and re-commit the core application code.
3. This tight coupling created credential leakage risks and prevented running automated, reproducible tests across distinct deployment environments.

### How we addressed Factor III in `assistant_core` and current limitations:
1. **Separation of Config:** We created `config.py` using Pydantic `BaseModel` to strictly validate environment configurations loaded via `python-dotenv`.
2. **Secret Masking Nuance:** Fields like `llm_api_key` are marked with `repr=False`. This hides the key when inspecting or printing the `Settings` object (e.g. in `print(settings)`), reducing the risk of accidental exposure in generic dumps. However, `repr=False` does not guarantee that secrets can never appear in logs or error traces (for example, if code explicitly logs `settings.llm_api_key` or if an unhandled exception prints local variables). Disciplined logging hygiene is still required.
3. **Environment Templates:** We committed `.env.example` as a template for developers and deployment environments, while ensuring `.env` is ignored by `.gitignore`.
4. **Current Architectural Limitation:** While the configuration schema exists, the current CLI entry point (`__main__.py`) initializes `AssistantService()` directly, relying on internal fallback defaults rather than explicitly injecting `load_settings()`. Complete end-to-end configuration wiring remains a separate integration task owned by the teammate responsible for the configuration module.

### Secondary Violation: Factor XI (Logs)
The monolith interspersed `print("[debug] ...")` with actual functional output, polluting standard output and rendering programmatic piping unusable. We resolved this by routing structured JSON operational logs (`intent`, `latency_ms`, `degraded`) strictly to `stderr`, ensuring `stdout` outputs clean user-facing responses.

---

## 3. Self-Check Verification
- [x] Read all five referenced materials and compared against repository layout.
- [x] Analyzed trade-offs between monolithic and modular architectures.
- [x] Formulated reflection in my own words based on actual refactoring experience and noted real code limitations.
- [x] Verified full test pass (`pytest -q`: 104 passed) and clean Ruff checks.

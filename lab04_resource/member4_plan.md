# EXECUTION PLAN FOR MEMBER 4 (BACKEND DEV 3)
**Name:** Pham Khanh Tam  
**Role:** Member 4 (TV4) — Backend Dev 3 (External Weather & Resilience)  
**Project:** Study Assistant (`assistant_core` / `assistant_api`)  
**Issue:** `#20` (`api: implement GET /v1/weather endpoint with failure resilience (#20)`)  
**Branch:** `feat/04-weather-resilience`  
**Target Grade:** 10/10 official + 1 bonus point = **11/10**

---

## 1. Primary Objectives and Responsibilities

Member 4 (Tam) is responsible for integrating the external weather service with fault tolerance and resilience mechanisms:
1. **Implementation Deliverables (Task T4 - Section D.6)**:
   - Implement the `GET /v1/weather` endpoint connected to `WeatherClient`.
   - Catch `ExternalServiceError` and translate it into a clean HTTP 503 Service Unavailable status code.
   - Strictly adhere to the `Weather` and `ErrorResponse` schemas.
2. **Resilience Analysis Deliverables (Exercise Page 16)**:
   - Analyze and answer the Page 16 exercise question regarding how mock network failures are simulated in `test_weather_down_returns_503`.
   - Document the three resilience habits of `WeatherClient`: Timeout (3s), Retry (exponential / immediate retry on failure), and Backup Plan (stale in-memory cache marked `stale=True`).
3. **Testing and PR Evidence**:
   - Run automated pytest suite: achieve 100% pass on weather-related tests (`test_weather_ok`, `test_weather_down_returns_503`, `test_weather_stale_cache_when_upstream_fails`).
   - Capture required Swagger UI (`/docs`) screenshot when invoking `/v1/chat`.
   - Provide the 5-line Reflection (H2) and log AI usage in `docs/ai-use-log.md`.
   - Open individual Pull Request following the project template.

---

## 2. Step-by-Step Execution Plan

```
[Phase 1: Issue #20 & Branch Creation] ──> [Phase 2: Implement Task T4] ──> [Phase 3: Resilience Analysis (P16)]
                                                                                             │
[Phase 6: Peer Review & Handoff] <───── [Phase 5: Open Individual PR] <──── [Phase 4: Pytest & Swagger UI]
```

---

### Phase 1: Issue #20 and Branch Creation

1. **Create Issue on GitHub:**
   - **Title:** `api: implement GET /v1/weather endpoint with failure resilience (#20)`
   - **Labels:** `feat`, `backend`, `external`, `M4`
   - **Assignee:** `@AI-WFox`
   - **Body:**
     ```markdown
     ## Goal
     Provide campus weather information for Nguyen Van Cu campus via GET /v1/weather with graceful external service failure resilience.

     ## Acceptance criteria
     - [x] Query WeatherClient for current weather with 3s timeout, retry loop, and stale cache fallback.
     - [x] Catch ExternalServiceError and return clean HTTP 503 Service Unavailable.
     - [x] Pass mock network failure unit test `test_weather_down_returns_503`.
     ```
2. **Create Working Branch:**
   - Branch created off `origin/docs/lab04-guide`:
     ```bash
     git checkout -b feat/04-weather-resilience origin/docs/lab04-guide
     ```

---

### Phase 2: Implement Task T4 (Section D.6)

1. **File Location:** `lab04_resource/starter/src/assistant_api/main.py`
2. **Implementation:**
   Replace `raise NotImplementedError("T4")` inside `campus_weather()` with resilient error handling:
   ```python
   @app.get("/v1/weather", response_model=Weather, tags=["external"], responses={503: {"model": ErrorResponse}})
   def campus_weather() -> Weather:
       try:
           return weather.current()
       except ExternalServiceError:
           raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Weather service unavailable") from None
   ```
3. **Technical Architecture Explanation:**
   - `weather.current()`: Queries Open-Meteo API using campus coordinates (`campus_lat`, `campus_lon`).
   - `except ExternalServiceError:`: When upstream services encounter persistent timeouts or HTTP 5xx errors across all retries, the client raises `ExternalServiceError`.
   - `raise HTTPException(...) from None`: Translates the internal exception to standard HTTP 503 while suppressing internal tracebacks via `from None`.

---

### Phase 3: Resilience Analysis (Exercise Page 16)

1. **Exercise Question (Tutorial Page 16):**
   * *Open `tests/test_api.py` and read `test_weather_down_returns_503`. In one sentence, explain how it pretends the weather site is down.*
2. **Standard Answer:**
   > *"The test uses the `weather_with(...)` fixture with an `httpx.MockTransport` handler that intercepts outgoing network requests and raises `httpx.ConnectTimeout` (or HTTP 500) directly, verifying that `/v1/weather` catches the resulting `ExternalServiceError` and translates it into an HTTP 503 response with error code `weather_service_unavailable`."*
3. **Three Resilience Habits Applied:**
   - **Timeout (Wait at most 3 seconds):** Configures `httpx.Client(timeout=3)` to avoid blocking the server event loop on slow upstream responses.
   - **Retry (If it fails, try once more):** Employs a retry loop to recover from transient network glitches.
   - **Backup Plan (Serve stale cache when down):** Retains last-known weather data in memory and returns it with `stale=True` when upstream is completely unreachable.

---

### Phase 4: Verification with Pytest and Swagger UI

1. **Automated Pytest Execution:**
   ```bash
   pytest lab04_resource/starter/tests/test_api.py -k "weather" -v
   ```
   *Expected Result:* All 3 test cases pass (**PASSED**):
   - `test_weather_ok`: Verifies standard HTTP 200 response with `overcast` condition.
   - `test_weather_down_returns_503`: Verifies HTTP 503 response when upstream service times out.
   - `test_weather_stale_cache_when_upstream_fails`: Verifies fallback to cached data marked with `stale=True`.

2. **Swagger UI (`/docs`) Verification:**
   - Launch application server:
     ```bash
     cd lab04_resource/starter
     uvicorn assistant_api.main:create_app --factory --reload
     ```
   - Navigate to `http://127.0.0.1:8000/docs`.
   - Test `POST /v1/chat` -> **Try it out** -> Send message -> **Execute**.
   - Capture screenshot showing HTTP 200 response and generated `request_id`.

---

### Phase 5: Individual Pull Request

1. **Commit and Push Changes:**
   ```bash
   git add lab04_resource/starter/src/assistant_api/main.py lab04_resource/member4_plan.md docs/ai-use-log.md
   git commit -m "feat(weather): implement GET /v1/weather endpoint with failure resilience (#20)"
   git push -u origin feat/04-weather-resilience
   ```
2. **PR Content:**
   - **What:** Implement `GET /v1/weather` endpoint connected to `WeatherClient` with graceful failure handling.
   - **Why:** Closes #20. Completes Task T4 according to CSC10014 Lab 4 specifications.
   - **Reflection H2 (5 lines):**
     > *"In Lab 3, calling `service.handle()` was an in-process function call, requiring both client and server to be written in Python and executed on the same machine. In Lab 4, wrapping the service behind an HTTP REST API (`POST /v1/chat`) completely decouples the client from the backend implementation. This allows diverse frontends—such as web browsers, mobile applications, or external services—to exchange data seamlessly via JSON without language or platform dependency. For team collaboration, this architecture establishes clear separation of concerns, enabling frontend and backend teams to develop independently against an agreed API contract without conflicting changes to each other's codebases."*
   - **AI Use:**
     - Tool: Google Antigravity IDE (Gemini).
     - Task: Generate Task T4 implementation wrapping `weather.current()` with `ExternalServiceError` handling to HTTP 503.
     - Verification: Passed all 3 weather unit tests, confirmed clean Ruff linting.

---

### Phase 6: Peer Review and Handoff to Tech Lead

- Assign peer reviewers per team rotation.
- Ensure all CI checks are green on the PR.
- Handoff branch to Tech Lead (Duy) for squash-merging into `main` during API integration.

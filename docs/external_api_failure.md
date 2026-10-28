# Lab 4 homework — design for an external service that goes down

Owner: Nhat Quynh (Member 7).
Tracking issue: [#31](https://github.com/Computational-Thinking-Project/assistant_core_lab/issues/31).

Service chosen: **weather (Open-Meteo)**. Default Base URL:
`https://api.open-meteo.com/v1/forecast`, configurable through `WEATHER_URL`.
Campus coordinates default to latitude `10.7626`, longitude `106.6822`.
Integrated reference: [weather implementation](https://github.com/Computational-Thinking-Project/assistant_core_lab/blob/b98fd4c300379d54aecb1ece5e2a351c1b97a315/src/assistant_api/weather.py),
[T4 route](https://github.com/Computational-Thinking-Project/assistant_core_lab/blob/b98fd4c300379d54aecb1ece5e2a351c1b97a315/src/assistant_api/main.py)
and [existing API tests](https://github.com/Computational-Thinking-Project/assistant_core_lab/blob/b98fd4c300379d54aecb1ece5e2a351c1b97a315/tests/test_api.py),
verified on **2026-10-27** at `b98fd4c300379d54aecb1ece5e2a351c1b97a315`.

The response column below describes the verified repository-root API. The older
starter reference at `3adb5fdc45a559fc207b2406f00a950e1e9f91f6` informed the
original worksheet. The early PR #28 snapshot lacked T4; that integration gap
is resolved in the current revision. Historical results remain below.
The user-facing messages below are UI proposals, not an implemented frontend.

| Failure | How you simulate it | What your API returns | What the user sees |
|---|---|---|---|
| Timeout | An `httpx.MockTransport` handler raises `httpx.ConnectTimeout` on each attempt. | With no cache: 503, `error.code = weather_service_unavailable`. With expired cache: 200 and cached weather with `stale: true`. | Temporarily unavailable weather, or clearly labelled old weather with its observation time. |
| 500 from upstream | MockTransport returns HTTP 500; `raise_for_status()` raises an HTTP error. | Same no-cache 503 / expired-cache 200 behaviour after retry. The upstream 500 is not forwarded directly. | A friendly weather problem or stale weather; other API features remain available. |
| Malformed/incomplete JSON | MockTransport returns HTTP 200 with `{}`. Access to `current` raises `KeyError`; invalid JSON text instead raises `ValueError`. | Same no-cache 503 / expired-cache 200 behaviour for these handled errors. | No fabricated weather values; show unavailability or explicitly stale values. |
| Rate limited (429) | MockTransport returns HTTP 429; `raise_for_status()` raises an HTTP error. | Same no-cache 503 / expired-cache 200 behaviour. This upstream 429 does not become the chat endpoint's 429. | Weather unavailable or stale; do not tell the user that their chat quota was exceeded. |

## Timeout, retries and cache

- **Timeout: 3 seconds by default**, configured with `WEATHER_TIMEOUT_S`. This
  limits HTTP operations through HTTPX; it is not a guaranteed three-second
  deadline for the whole endpoint. A short timeout prevents a slow weather
  provider from blocking the user indefinitely.
- **Retries: 1**, in addition to the first attempt, for at most two HTTP calls.
  The reference sleeps 0.2 seconds after the first failure and 0.4 seconds after
  the second. A short retry can recover from a transient failure without an
  unlimited wait. The code does not implement exponential backoff or honour an
  upstream Retry-After header.
- **Cache TTL: 600 seconds** in the integrated WeatherClient. Fresh cache is
  returned immediately without contacting upstream. An expired cache triggers a
  refresh; failed refresh returns the old value with `stale: true`. Ten-minute
  freshness reduces repeated upstream calls while keeping campus weather useful
  for a general assistant; the observation time must remain visible to users.
- Cache is process-local and in memory. Restarting loses it; instances do not
  share cached data. The fallback has no maximum stale age in this implementation.
- This is resilient handling for the documented cases, not a promise that all
  possible JSON structures are caught. A disposable check with
  `{"current": null}` returned HTTP 500 in both the earlier reference and the
  integrated check because `TypeError` is not caught. This additional limitation
  is recorded in the QA report; no fix or message to the weather owner is claimed
  as part of this documentation task.

## Tests added (file + names)

**No permanent Python tests added by Member 7.** Existing root tests in
`tests/test_api.py` are preserved; their starter counterparts were used in the
earlier reference checks:

- `test_weather_ok`: successful API response.
- `test_weather_down_returns_503`: ConnectTimeout with no cache maps to 503 and
  the application error code.
- `test_weather_stale_cache_when_upstream_fails`: a successful first result,
  forced cache expiry and upstream 500 result in stale cached data at the client
  level.

## Verification results

### Historical reference check — 2026-10-26

The three existing weather tests were rerun on 2026-10-26 from an unchanged
temporary copy of the pinned reference starter:

```text
python -m pytest -q -p no:cacheprovider tests/test_api.py -k weather
3 passed, 6 deselected
```

Disposable QA checks were run on 2026-10-26 against an unmodified temporary copy
of reference revision `3adb5fdc45a559fc207b2406f00a950e1e9f91f6`.
The failure/cache combinations matched the results below.

### Integrated check — 2026-10-27

The root suite at `b98fd4c300379d54aecb1ece5e2a351c1b97a315` reported
**98 passed, no skips**, including the three existing weather tests. A separate
live HTTP curl run returned weather 200. Disposable checks reran every matrix
combination against the actual root modules, injecting MockTransport into
WeatherClient and calling `/v1/weather` through FastAPI TestClient. The matrix
did not use the internet. Retry sleeps were patched out; attempt counts, not
real timeout duration, were checked.

| Failure injected | No cache | Expired cache | Result |
|---|---|---|---|
| ConnectTimeout | 503, `weather_service_unavailable`, 2 attempts | 200, `stale: true`, original `observed_at` retained | Pass |
| Upstream 500 | 503, `weather_service_unavailable`, 2 attempts | 200, `stale: true`, original `observed_at` retained | Pass |
| HTTP 200 with `{}` | 503, `weather_service_unavailable`, 2 attempts | 200, `stale: true`, original `observed_at` retained | Pass |
| Upstream 429 | 503, `weather_service_unavailable`, 2 attempts | 200, `stale: true`, original `observed_at` retained | Pass |

For each expired-cache check, one successful upstream call seeded the cache,
then two failed refresh attempts occurred (three calls total). Cache expiry was
forced by setting the test client's TTL to zero. A separate fresh-cache check
made two reads with only one upstream call; both returned `stale: false` (Pass).

Summary: eight failure/cache combinations and one fresh-cache check passed.
The additional `current: null` check exposed the HTTP 500 limitation above; it
does not count as a successful graceful-failure check. Invalid JSON text was
reviewed in code but was not separately exercised by this matrix, which used
the worksheet's `{}` case.

These were temporary verification checks, not new committed Python tests.
The required four failure rows and cache behaviour **passed on the integrated
root API**; they are no longer blocked on T4. The additional `current: null`
probe remains a known limitation, not a passing graceful-failure case. Exact
commands, source context and log locations are in the
[QA report](lab04_qa_report.md).

### Reproducing the failure/cache matrix

1. Use the pinned integrated repository-root API with its dependencies and course
   data; confirm imports resolve to root `src`. Inject a WeatherClient backed by MockTransport into
   `create_app`; do not modify the production route or contact Open-Meteo.
2. For each table row, create a new client with no cache and the failing handler.
   Assert two upstream attempts, HTTP 503 and the application error code.
3. For the expired-cache variant, first return a successful weather payload to
   seed the cache. Force expiry with `cache_ttl_s = 0`, then fail both refresh
   attempts. Assert HTTP 200, `stale: true` and the original observation time.
4. Separately keep the normal TTL, read twice after a successful response and
   assert only one upstream call. Both reads must have `stale: false`.

These injected checks verify the HTTP mapping, retry count and cache behaviour.
They do not measure real timeout duration, provider uptime or concurrency.

## Exercise explanation

`test_weather_down_returns_503` injects a MockTransport handler that raises
ConnectTimeout instead of accessing the internet, then asserts that the API
translates the failure into HTTP 503 with `weather_service_unavailable`.

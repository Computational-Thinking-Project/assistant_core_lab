# Lab04 QA report

Owner: Nhat Quynh (Member 7). Tracking issue:
[#31](https://github.com/Computational-Thinking-Project/assistant_core_lab/issues/31).
Integrated verification date: **2026-10-27** (Asia/Saigon).
Working branch: `docs/07-qa-docs-evidence`.
Integrated revision: `b98fd4c300379d54aecb1ece5e2a351c1b97a315`.
Historical checks below retain their original source revisions and results.

## Test context

Current acceptance targets the **repository-root API** at the integrated
revision above, with the TV7 curl script identified by the SHA-256 below. Imports were checked to
resolve to this repository's root `src/assistant_api/main.py` and
`src/assistant_core/service.py`, not a temporary starter snapshot or another
installed package. TV7 changes do not modify application logic or Python tests.

All six members' task PRs are merged: chat #26, admin #28, offices #23,
weather #34, rate limiting #33 and feedback #30. This report verifies the pinned
integrated code; it does not create a release tag or claim future revisions pass.

### Current integrated acceptance

| Check | Actual result | Status |
|---|---|---|
| Root pytest suite | 98 passed, no failures or skips; one deprecation warning | Pass |
| Root curl with `--offices --bonus` | 14 passed, 0 failed; exit 0 | Pass |
| Live weather in that curl run | HTTP 200 with valid response fields | Pass |
| Four injected weather failures with/without expired cache | Eight combinations matched expected 503/stale-200 responses | Pass |
| Fresh weather cache | Two reads, one upstream call, `stale: false` | Pass |
| Bash syntax | Exit 0 | Pass |
| Verification isolation | Own test server stopped; six deliverables and Git state unchanged by the run | Pass |

The tested curl script is `api-tests/curl_tests.sh`, SHA-256:
`196D7C825708E7508B843DC78E39EDE32707F0485C555611C4B5E292C1C156CA`.

The additional `current: null` weather probe still returned 500. It is a known
robustness limitation outside the four required failure cases, not a successful
graceful-failure test or a change made by TV7.

### Historical snapshot context

| Snapshot | Source revision | API location in its source repository |
|---|---|---|
| Reference / weather | `origin/docs/lab04-guide` — `3adb5fdc45a559fc207b2406f00a950e1e9f91f6` | `lab04_resource/starter` |
| Chat / [PR #26](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/26) | `origin/feat/02-chat-endpoint` — `ff6d756dca3ba562effcdbd8a8bc22ea46ebd3f6` | `lab04_resource/starter` |
| Offices / [PR #23](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/23) | `origin/feat/22-offices` — `f6a8c65bd3921858af48e671be443479aaeefae1` | `lab04_resource/starter` |
| Root API / [PR #28](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/28) | `origin/feat/01-feedback-admin` — `33820e361daa84e4e9b0255b786a067025172adb` | Repository root |

Historical checks used temporary exports of these earlier snapshots. Their
failures document partial implementations at those revisions and must not be
treated as the current integrated result.

Status meanings:

- **Pass**: an executed check matched its stated expectation.
- **Fail**: an executed check differed from its expected result; the scope is
  identified as current acceptance, historical verification or an additional probe.
- **Blocked**: a required implementation, integration or input is missing.
- **Not run**: no completed execution or visual review is claimed.

## Setup and execution

Environment: Windows, Git Bash, Python 3.12.10, and an isolated temporary virtual
environment. Dependencies included Pydantic 2.9.2, FastAPI 0.115.0, HTTPX 0.27.2,
Uvicorn 0.30.6 and pytest 8.3.3, as pinned by the reference requirements.
The historical Lab03 regression used the repository's existing virtual environment.

Local evidence is retained under:
`C:/Users/nminh/AppData/Local/Temp/lab04-tv7-20261026`.
Its `guide`, `chat`, `offices` and `admin` directories contain the corresponding
snapshot roots, each with a `SOURCE.txt` recording provenance. Logs and the
disposable `verify.py` helper are local evidence, not committed deliverables.
Another machine must recreate the snapshots and checks; these temporary files
are not assumed to exist there.

The completed integrated run is retained separately at:
`C:/Users/nminh/AppData/Local/Temp/lab04-tv7-20261026/integrated-b98fd4c-20261027-a23f5b57`.
Its `context.txt`, `pytest.log`, `curl.log`, `uvicorn.log`, `weather-matrix.log`
and `result.txt` record the actual root API verification. The API used an
automatically selected free port, `http://127.0.0.1:53916`, with quota 8 and an
ephemeral admin key that was not logged. The test server has been stopped.

The pytest command executed from the repository root was:

```text
python -m pytest -q -p no:cacheprovider tests --tb=short --basetemp=<run-directory>/pytest-temp
98 passed, 1 warning in 2.41s
```

The Starlette/AnyIO deprecation warning did not cause a test failure.

### Running the curl checks

Use the integrated repository-root API, its course data and a Python environment
containing the root requirements. The following reproduction commands are for
**Git Bash**, not PowerShell. Replace the Python/key placeholders. The example
port 8002 must be free; set BASE to the same port if using another one.

Terminal 1, from the repository root:

```bash
export PYTHON='<Python executable for the selected runtime>'
export PYTHONPATH=src
export ASSISTANT_DATA_DIR=data
export LLM_PROVIDER=stub
export CREDIT_RATE_VND=450000
export RETAKE_MULTIPLIER=1.5
export MAX_CREDITS=30
export WEATHER_URL=https://api.open-meteo.com/v1/forecast
export WEATHER_TIMEOUT_S=3
export CAMPUS_LAT=10.7626
export CAMPUS_LON=106.6822
export API_ADMIN_KEY='<local-test-key>'
export RATE_LIMIT_PER_MIN=8
"$PYTHON" -m uvicorn assistant_api.main:create_app --factory --app-dir src --host 127.0.0.1 --port 8002
```

Terminal 2, using the same Python executable and local test key:

```bash
export PYTHON='<same Python executable>'
export API_ADMIN_KEY='<same local-test-key>'
export BASE=http://127.0.0.1:8002
export RATE_LIMIT_PER_MIN=8
bash api-tests/curl_tests.sh --offices --bonus
```

Without options, the script runs 12 core checks. `--offices` adds one H1 check;
`--bonus` adds one rate-limit check. Selected groups must pass; absent endpoints
are not silently skipped. For bonus checks, use one worker, the actual server
quota, and a fresh quota without concurrent chat traffic. Use a quota of at
least two so both core chat success checks can run. The bonus group counts
previous accepted chats, requires HTTP 200 through request N and HTTP 429 on
request N+1, matching the limiter inside the validated chat handler. The check
must finish inside one 60-second window; expiry produces a diagnostic and a
nonzero result instead of a misleading pass. A nonzero exit code
indicates a failed check or setup error. An incomplete API is expected to fail.

The script uses the reference course data and tuition settings. It checks JSON
response content as well as status codes. It checks authenticated GET feedback
even if POST feedback is unfinished. Every returned feedback object must have a
valid ID, request ID, integer rating, nullable comment and UTC creation time.
A successful POST enables full readback comparison, including the timestamp,
and requires the created ID to appear exactly once. Equivalent UTC timestamp
spellings are accepted. If creation failed, roundtrip remains unverified.

The integrated HTTP run used the default Open-Meteo forecast URL and a 3-second
weather timeout. Its weather response was HTTP 200 on that run only; this is not
a provider-uptime guarantee. Quota 8 was a local test override; the application's
default remains 30. No real credentials are included in this report.

The root curl script has the same content hash as the script used for the
18 runner regression scenarios below. The integrated curl run independently
verified that script against the current root API.

## Historical automated test results

The full snapshot suites were run from each snapshot's project root using
`python -m pytest -q tests --tb=short --basetemp=<temporary-directory>`.
The different totals reflect different source trees, not a fixed 24-test target.
These are the earlier snapshot results; current acceptance is 98 passed above.

| Suite | Actual result | Status | Evidence / explanation |
|---|---|---|---|
| Reference starter | 21 passed, 2 failed, 1 skipped | Fail | `guide-pytest.log`: T1 and T2 unimplemented; bonus skipped. |
| Chat starter | 20 passed, 3 failed, 1 skipped | Fail | `chat-pytest.log`: T2 and T4 unimplemented; bonus skipped. |
| Offices starter | 21 passed, 4 failed, 1 skipped | Fail | `offices-pytest.log`: T1/T2/T4 unimplemented; bonus skipped. The two added offices tests pass. |
| PR #28 root API | 92 passed, 3 failed, 1 skipped | Fail | `admin-pytest.log`: feedback roundtrip and two weather API tests fail due to T2/T4; bonus skipped. |
| Existing Lab03 suite at `7c3fa7c` | 87 passed | Pass | `lab03-regression.log`; independent of unfinished Lab04 handlers. |
| Reference weather tests only | 3 passed, 6 deselected | Pass | Rerun with `python -m pytest -q -p no:cacheprovider tests/test_api.py -k weather`. |

The snapshot suites also emitted a Starlette/AnyIO deprecation warning; it did
not cause these failures. Existing assertions and skip markers were preserved.

## Integrated HTTP cases — 2026-10-27

The current root script ran once against a fresh local server at the pinned
integrated revision, with `--offices --bonus` and quota 8.
Evidence: `curl.log` and `uvicorn.log` in the integrated run directory.

| ID | Input / action | Expected result | Actual result | Status |
|---|---|---|---|---|
| H01 | GET `/health` | 200 with `status: ok` and string version | 200; status/version assertions passed | Pass |
| C01 | Fee query for 18 credits and 2 retakes | 200; tuition 9,450,000 VND, fee intent, 12-hex request ID | 200; expected tuition and response fields verified | Pass |
| C02 | Thesis query with 118 credits | 200; rule answer with nonempty sources | 200; rule intent and source fields verified | Pass |
| C03 | Empty chat message | 422, `invalid_request` | 422; expected error envelope verified | Pass |
| C04 | Numeric chat message | 422, `invalid_request` | 422; expected error envelope verified | Pass |
| F01 | Create feedback using C01 request ID | 201; matching submitted fields, positive ID, UTC creation time | 201; request ID/rating/comment, ID and UTC timestamp verified | Pass |
| F02 | Feedback rating 7 | 422, `invalid_request` | 422; expected error envelope verified | Pass |
| F03 | Read feedback without key | 401, `missing_or_invalid_api_key` | 401; expected error envelope verified | Pass |
| F04 | Read feedback with wrong key | 401, `missing_or_invalid_api_key` | 401; expected error envelope verified | Pass |
| F05 | Read feedback with valid key | 200; valid array containing F01 exactly once with all fields unchanged | 200; schema and full readback comparison passed | Pass |
| W01 | GET `/v1/weather` with live upstream | Valid 200 weather, or clean 503 with `weather_service_unavailable` | 200; weather field assertions passed | Pass |
| U01 | GET `/v1/nope` | 404 with framework detail or application error object | 404; framework JSON body verified | Pass |
| O01 | GET `/v1/offices` | 200; string fields, Library present, names sorted | 200; field, Library and ordering assertions passed | Pass |
| R01 | Exhaust configured chat quota | Quota 8: valid requests 1–8 return 200; request 9 returns 429 with `too_many_requests` | Requests through quota 8 accepted; request 9 returned the expected 429 error | Pass |

Summary: **14 passed, 0 failed**, exit code **0**. F05 includes the full
feedback roundtrip assertion; it is not a fifteenth case.

## Historical HTTP cases on PR #28

The TV7 script was run against a temporary Uvicorn server from the pinned root
API snapshot, with `--offices` and without `--bonus`.
Result: **10 passed, 3 failed**, exit code **1**.
Evidence: `curl-actual-admin.log` and `admin-uvicorn.log` in the local evidence
directory. This is a partial implementation result, not release acceptance.

| ID | Input / action | Expected | Actual | Status |
|---|---|---|---|---|
| H01 | GET `/health` | 200, status/version | 200, valid body | Pass |
| C01 | Chat tuition for 18 credits and 2 retakes | 200, fee answer, 12-hex request ID | 200; 9,450,000 VND and valid fields | Pass |
| C02 | Chat thesis registration with 118 credits | 200, rule answer with sources | 200, valid source fields | Pass |
| C03 | Chat with empty message | 422, `invalid_request` | Expected status and error body | Pass |
| C04 | Chat with numeric message | 422, `invalid_request` | Expected status and error body | Pass |
| F01 | Create feedback using C01 request ID | 201, created item with UTC time | 500 from unfinished T2 | Fail |
| F02 | Submit feedback with rating 7 | 422, `invalid_request` | Expected status and error body | Pass |
| F03 | Read feedback without key | 401, application error body | Expected status and body | Pass |
| F04 | Read feedback with wrong key | 401, application error body | Expected status and body | Pass |
| F05 | Read feedback with valid key | 200, feedback array | 200, valid array | Pass |
| F06 | Confirm created feedback is returned | Created item present | Cannot establish roundtrip after F01 failed | Blocked |
| W01 | GET `/v1/weather` | 200 weather or clean 503 | 500 from unfinished T4 | Fail |
| O01 | GET `/v1/offices` with course data | 200, Library and sorted valid entries | 404; route absent in root API | Fail |
| U01 | GET `/v1/nope` | 404, structured JSON | 404, `{"detail":"Not Found"}` | Pass |
| R01 | Exceed configured chat quota | 429, `too_many_requests` | Production check not run; limiter is not called in this revision | Blocked |

F06 is a separate dependency record, not an extra counted curl case. R01 was not
selected in this root-API run. The script's 13 counted cases are H01, C01–C04,
F01–F05, W01, O01 and U01.

Supplemental disposable TestClient checks also passed for missing/overlong chat
messages, overlong session IDs, and the offices branch's fields, Library,
ordering and injected empty directory. These are branch-local console results,
not permanent tests. Root offices is independently verified by current O01.

## Weather failure/cache matrix

The matrix was first exercised on the reference snapshot and rerun on the
integrated root API at `b98fd4c300379d54aecb1ece5e2a351c1b97a315`.
The integrated checks confirmed imports point to current root `src`, injected
MockTransport into WeatherClient and called the API with TestClient.
No internet access was used for the matrix. Retry sleeps were patched out;
actual timeout duration was not measured.

| Injected upstream failure | No cache | Expired cache | Status |
|---|---|---|---|
| ConnectTimeout | 503, `weather_service_unavailable`, two attempts | 200, stale weather, original observation time | Pass |
| HTTP 500 | Same clean 503 and two attempts | Same stale fallback | Pass |
| HTTP 200 with `{}` | Same clean 503 and two attempts | Same stale fallback | Pass |
| HTTP 429 | Same clean 503 and two attempts | Same stale fallback | Pass |

All **eight** failure/cache combinations passed. Expired-cache cases used one
successful call to seed the cache and two failing refresh attempts. A separate
fresh-cache check passed: two reads, one upstream call, both `stale: false`.
Current evidence: `weather-matrix.log` inside the integrated run directory;
the earlier reference log remains at the parent evidence directory.
Reproduction steps are in the
[external API failure worksheet](../lab04_resource/worksheets/external_api_failure.md#reproducing-the-failurecache-matrix).

An additional malformed-type probe with `{"current": null}` returned 500 because
TypeError is not handled. This is a recorded robustness defect, not another
passing graceful-failure case. Invalid JSON text was reviewed in code but was
not separately injected; the documented matrix used `{}`.

## Curl runner verification

Controlled local HTTP fixtures check the **runner's ability to detect results**.
They do not substitute for the members' actual endpoints. The disposable fixture
code and servers remain outside the repository deliverables.

Self-review exposed two false positives in the previous runner: an early quota
rejection and a GET feedback object containing only an ID both produced
`14 passed`. The quota boundary and full feedback readback checks were corrected.
The updated runner completed **18 fixture scenarios** with the expected outcomes
below, including intentional API failures that must produce a nonzero exit.

| Scenario | Actual script result | Expected runner behaviour | Status |
|---|---|---|---|
| All fixture endpoints conform | 14 passed, 0 failed; exit 0 | Accept correct status and bodies | Pass |
| Weather fixture returns clean 503 | 14 passed, 0 failed; exit 0 | Accept graceful unavailability | Pass |
| Expected quota 8, actual quota 2 | 13 passed, 1 failed; exit 1 | Reject early throttling at valid request 3 | Pass |
| Expected quota 8, actual quota 9 | 13 passed, 1 failed; exit 1 | Reject missing 429 at valid request 9 | Pass |
| Expected and actual quota both 2 | 14 passed, 0 failed; exit 0 | Count the two core chats before the first bonus request | Pass |
| GET feedback returns ID-only objects | 13 passed, 1 failed; exit 1 | Reject missing feedback fields | Pass |
| GET changes request ID, rating, comment or creation time | Each: 13 passed, 1 failed; exit 1 | Four separate scenarios reject data differing from POST | Pass |
| GET uses equivalent UTC timestamp spelling | 14 passed, 0 failed; exit 0 | Accept the same instant written with Z or +00:00 | Pass |
| GET duplicates the created feedback ID | 13 passed, 1 failed; exit 1 | Reject ambiguous readback | Pass |
| GET uses boolean rating instead of integer | 13 passed, 1 failed; exit 1 | Enforce the response field type | Pass |
| POST response omits comment | 13 passed, 1 failed; exit 1 | Reject incomplete creation responses | Pass |
| Chat fixture returns invalid request IDs | 10 passed, 4 failed; exit 1 | Reject incorrect bodies, including bonus greetings | Pass |
| Valid feedback POST fails, GET remains available | 13 passed, 1 failed; exit 1 | Fail creation, still check authenticated GET | Pass |
| Offices fixture route absent | 13 passed, 1 failed; exit 1 | Fail selected H1 group | Pass |
| Fixture limiter disabled | 13 passed, 1 failed; exit 1 | Fail selected bonus group | Pass |
| Server unreachable | 0 passed, 12 failed; exit 1 | Report connection failures and return nonzero | Pass |
| `--help` / unknown argument | Exit 0 / exit 2 | Handle CLI correctly | Pass |
| Bash syntax and whitespace | Checks passed | Valid shell syntax and no whitespace errors | Pass |

Evidence: `curl-fixture-*.log`, `curl-unreachable.log`, the disposable
`regressions.py` helper and completed CLI/syntax checks. The 18 scenarios count
the four changed-field cases separately; connection and CLI checks are
additional. Fixture logs were checked for the local admin-key value; it was not
printed. No production handler was altered to make a fixture pass.

## Defects and dependencies

| ID | Finding / reproduction | Owner or dependency | Status / next action |
|---|---|---|---|
| D01 | Historical PR #28 snapshot returned 500 from unfinished T2. | Hung (Member 3), Duy | Pass; resolved by #30 integration, verified by F01/F05 and the root suite. |
| D02 | Historical PR #28 snapshot returned 500 from unfinished T4. | Tam (Member 4), Duy | Pass; resolved by #34 integration, verified by live W01 and the failure/cache matrix. |
| D03 | Historical root API lacked offices. | Trung Anh (Member 5), Duy | Pass; #23 integrated H1 at root, verified by O01 and the root suite. |
| D04 | Historical root chat did not call the limiter; bonus was skipped. | Boi Anh (Member 6), Duy | Pass; #33 integrated the limiter and enabled tests, verified by R01 and the root suite with no skips. |
| D05 | Upstream 200 with `current: null` returns 500 in the reference and integrated API. | Tam (Member 4) | Fail; additional robustness probe outside the four required cases, retained as a known limitation. |
| D06 | The integrated revision/runtime was previously unconfirmed. | Duy / group | Pass; integrated execution verified b98fd4c and imports from repository-root modules. |
| D07 | Runner accepted HTTP 429 before the configured quota. | Nhat Quynh (Member 7) | Pass; fixed locally, early/late/exact-boundary regression scenarios matched expectations. |
| D08 | Runner accepted incomplete or changed feedback readback. | Nhat Quynh (Member 7) | Pass; fixed locally, schema/content/duplicate regressions reject incorrect data. |

The historical D01–D04 integration gaps are resolved at b98fd4c. D07/D08 are
resolved runner defects. The remaining failure is D05, an additional upstream
payload probe outside the required four-case matrix; it is not an unresolved
TV7 runner defect. Member 7 has not changed production handlers.

### Open limitation D05

- Reproduce with a new WeatherClient without cache, using MockTransport to
  return HTTP 200 with `{"current": null}`. Inject it into `create_app` and
  call `GET /v1/weather` with TestClient and `raise_server_exceptions=False`.
- Expected robustness behaviour: reject the invalid upstream structure and
  return a clean 503 when no cache is available.
- Actual result: HTTP 500 because indexing the null `current` value raises
  an uncaught TypeError. Evidence: the additional observation in
  `weather-matrix.log` for the pinned integrated run.
- Owner: Tam (weather). Status: Fail / open. A backend fix and retest are still
  needed to close this limitation; the QA report does not claim it is fixed.

## Swagger evidence checklist

Evidence status updated on **2026-10-27**. The user confirmed that all six other
members' screenshots are valid. The table records that confirmation alongside
the assistant's earlier visual inspections; it does not claim a new independent
inspection of every image in the evidence-check step. Current integrated and
historical test results are separated above.

Required evidence is an actual POST `/v1/chat` execution through Swagger `/docs`,
showing HTTP 200 and a populated `request_id`. A documented response schema or
JSON pasted as text alone is insufficient.

### Personal evidence

[Nhat Quynh's Swagger screenshot](evidence/nhatquynh1107-swagger-chat.png) was
visually checked and meets the requirement: endpoint, request, actual HTTP 200,
tuition answer of 9,450,000 VND and a generated request ID are visible.
The actual request used `session_id: "anonymous"`, which is valid under the
schema. It ran on port 8001 against the temporary PR #28 snapshot at
`33820e361daa84e4e9b0255b786a067025172adb`; it is personal execution evidence,
not a claim that this screenshot covers all later integrated endpoints.

| Contributor | Task PR | Evidence review | Evidence / verification source |
|---|---|---|---|
| Nhat Quynh (Member 7) | Issue [#31](https://github.com/Computational-Thinking-Project/assistant_core_lab/issues/31) | Pass | Personal screenshot above; assistant visually verified the actual response. |
| Duy (Member 1) | [#28](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/28) | Pass | [Chat response image](https://github.com/user-attachments/assets/118e66f2-dfe2-48ef-baf5-dde1b580597c); assistant visually checked chat 200 and request ID; user confirmed validity. |
| Dat (Member 2) | [#26](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/26) | Pass | [Chat image](https://raw.githubusercontent.com/Computational-Thinking-Project/assistant_core_lab/b98fd4c300379d54aecb1ece5e2a351c1b97a315/docs/evidence/docs_chat_evidence.png); assistant visually checked the repository image; user confirmed validity. |
| Hung (Member 3) | [#30](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/30) | Pass | [Chat image in the merged revision](https://raw.githubusercontent.com/Computational-Thinking-Project/assistant_core_lab/b98fd4c300379d54aecb1ece5e2a351c1b97a315/docs/evidence/hung-swagger-chat.png); image content accepted based on the user's confirmation. |
| Tam (Member 4) | [#34](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/34); evidence in [#21](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/21) | Pass | [Chat response image](https://github.com/user-attachments/assets/caa94b53-12fa-4050-8427-8f40e0042d6e); assistant visually checked chat 200 and request ID; user confirmed validity. |
| Trung Anh (Member 5) | [#23](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/23) | Pass | [Chat image](https://raw.githubusercontent.com/Computational-Thinking-Project/assistant_core_lab/b98fd4c300379d54aecb1ece5e2a351c1b97a315/docs/evidence/philip-kkk-swagger-chat.jpg); assistant visually checked chat 200 and request ID; user confirmed validity. |
| Boi Anh (Member 6) | [#33](https://github.com/Computational-Thinking-Project/assistant_core_lab/pull/33) | Pass | [Chat image](https://raw.githubusercontent.com/Computational-Thinking-Project/assistant_core_lab/b98fd4c300379d54aecb1ece5e2a351c1b97a315/docs/evidence/docs_chat_evidence.png); assistant visually checked chat 200 and request ID; user confirmed validity. |

Earlier branch-based image URLs sometimes returned 404 after merge. This table
uses attachment URLs or immutable merged-revision links and records the user's
subsequent confirmation; it does not claim every old URL was retested here.

## Final verification

| Item | Status | Verification |
|---|---|---|
| API contract worksheet | Pass | Updated against integrated root schemas and executed API results at b98fd4c. |
| External API failure worksheet | Pass | Updated with integrated failure/cache checks and the explicitly retained D05 limitation. |
| Curl runner | Pass | Same verified runner logic, now at root; integrated run reported 14 passed, 0 failed. |
| Personal Swagger screenshot | Pass | Actual chat response visually verified; source revision recorded above. |
| Six members' screenshot checks | Pass | User confirmed all six images are valid; evidence and verification sources recorded above. |
| Integrated suite and curl acceptance | Pass | At b98fd4c: 98 pytest passed without skips, 14 curl passed, eight weather failure/cache checks and fresh-cache check passed. |

The required TV7 acceptance checks passed at the pinned integrated revision.
D05 remains a known weather robustness limitation outside the required matrix.
These results cover the documented cases and do not establish that every
possible API input or future revision is correct.

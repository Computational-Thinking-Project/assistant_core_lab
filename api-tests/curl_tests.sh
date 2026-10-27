#!/usr/bin/env bash
# Run from any directory against an already running Lab04 API.
# Requires Bash, curl and Python 3. No Postman or jq dependency.
# Tracking issue: #31. A passing fixture run validates this script, not the release.
set -u
set -o pipefail

usage() {
    cat <<'HELP'
Usage: bash curl_tests.sh [--offices] [--bonus]

Core checks run by default. Optional groups must pass when selected.
Environment:
  BASE                API base URL (default http://127.0.0.1:8000)
  API_ADMIN_KEY       Local test admin key (default change-me)
  PYTHON              Python 3 executable (default python)
  REQUEST_TIMEOUT     Per-request curl timeout in seconds (default 15)
  RATE_LIMIT_PER_MIN  Actual server quota for --bonus (default 30, range 1..300)

Use the reference dataset and tuition defaults. Run against a single local
worker with quota at least 2 for both core chat success cases. Before --bonus,
restart your own test server or wait over 60 seconds without other chat traffic.
The check assumes a fresh quota and counts valid chat requests only, matching
the Lab04 limiter inside the chat handler. The full check must finish within
one 60-second window; use a smaller test quota if your machine is too slow.
HELP
}

offices=0
bonus=0
for arg in "$@"; do
    case "$arg" in
        --offices) offices=1 ;;
        --bonus) bonus=1 ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
done

BASE="${BASE:-http://127.0.0.1:8000}"
BASE="${BASE%/}"
ADMIN="${API_ADMIN_KEY:-change-me}"
PYTHON="${PYTHON:-python}"
REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-15}"
QUOTA="${RATE_LIMIT_PER_MIN:-30}"
for program in curl "$PYTHON"; do
    if ! command -v "$program" >/dev/null 2>&1; then
        printf 'Missing executable: %s\n' "$program" >&2
        exit 2
    fi
done
if ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    printf 'PYTHON must point to Python 3.10 or newer.\n' >&2
    exit 2
fi
if [[ ! "$REQUEST_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
    printf 'REQUEST_TIMEOUT must be a positive integer.\n' >&2
    exit 2
fi
if (( bonus )) && { [[ ! "$QUOTA" =~ ^[1-9][0-9]{0,2}$ ]] || (( QUOTA > 300 )); }; then
    printf 'RATE_LIMIT_PER_MIN must match the server and be in 1..300.\n' >&2
    exit 2
fi

body_file=$(mktemp) || exit 2
trap 'rm -f -- "$body_file"' EXIT
passed=0
failed=0
status=000
chat_accepted=0

request() {
    local method="$1" path="$2" payload="$3" auth="$4"
    local -a args=(--silent --show-error --connect-timeout 3 --max-time "$REQUEST_TIMEOUT"
        --output "$body_file" --write-out '%{http_code}' --request "$method")
    : > "$body_file"
    if [[ -n "$payload" ]]; then
        args+=(--header 'Content-Type: application/json' --data "$payload")
    fi
    case "$auth" in
        valid) args+=(--header "X-API-Key: $ADMIN") ;;
        invalid) args+=(--header "X-API-Key: ${ADMIN}-invalid") ;;
    esac
    if ! status=$(curl "${args[@]}" "$BASE$path"); then
        status=000
        return 1
    fi
    if [[ "$method" == POST && "$path" == /v1/chat && "$status" == 200 ]]; then
        chat_accepted=$((chat_accepted + 1))
    fi
}

validate() {
    "$PYTHON" - "$body_file" "$1" "$status" "${2:-}" <<'PY'
import json
import re
import sys
from datetime import datetime

path, kind, status, expected = sys.argv[1:]
try:
    with open(path, encoding="utf-8") as stream:
        data = json.load(stream)
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def error(code):
        require(isinstance(data, dict), "expected error object")
        item = data.get("error")
        require(isinstance(item, dict), "missing error envelope")
        require(item.get("code") == code, "unexpected error.code")
        require(isinstance(item.get("message"), str) and bool(item["message"]), "missing error message")
    def feedback(item):
        require(isinstance(item, dict), "feedback item must be an object")
        require(type(item.get("id")) is int and item["id"] > 0, "invalid feedback id")
        require(isinstance(item.get("request_id"), str) and 1 <= len(item["request_id"]) <= 64, "invalid feedback request_id")
        require(type(item.get("rating")) is int and item["rating"] in (-1, 0, 1), "invalid feedback rating")
        require("comment" in item and (item["comment"] is None or isinstance(item["comment"], str) and len(item["comment"]) <= 500), "invalid or missing feedback comment")
        require(isinstance(item.get("created_at"), str), "invalid feedback created_at")
        stamp = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        require(stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0, "created_at must be UTC")
        return stamp
    if kind == "health":
        require(data.get("status") == "ok" and isinstance(data.get("version"), str), "invalid health response")
    elif kind in ("fee", "rule", "greeting"):
        require(isinstance(data.get("answer"), str) and bool(data["answer"]), "missing answer")
        require(data.get("intent") == kind, "unexpected intent")
        require(re.fullmatch(r"[0-9a-f]{12}", data.get("request_id", "")) is not None, "invalid request_id")
        require(isinstance(data.get("degraded"), bool), "missing degraded flag")
        sources = data.get("sources")
        require(isinstance(sources, list), "sources must be an array")
        if kind == "fee":
            require("9,450,000" in data["answer"], "unexpected tuition under reference defaults")
        elif kind == "rule":
            require(bool(sources), "rule answer must cite a source")
            require(all(isinstance(s, dict) and isinstance(s.get("id"), str) and isinstance(s.get("title"), str) for s in sources), "invalid source")
    elif kind == "feedback":
        feedback(data)
        require(data.get("request_id") == expected and data.get("rating") == 1, "feedback differs from request")
        require(data["comment"] == "clear answer", "feedback comment differs from request")
    elif kind == "feedback_list":
        require(isinstance(data, list), "feedback must be an array")
        for item in data:
            feedback(item)
        if expected:
            created = json.loads(expected)
            created_at = feedback(created)
            matches = [item for item in data if item["id"] == created["id"]]
            require(len(matches) == 1, "created feedback must be returned exactly once")
            require(all(matches[0][key] == created[key] for key in ("id", "request_id", "rating", "comment")), "returned feedback differs from POST response")
            require(feedback(matches[0]) == created_at, "returned creation time differs from POST response")
    elif kind == "offices":
        require(isinstance(data, list), "offices must be an array")
        require(all(isinstance(item, dict) and all(isinstance(item.get(key), str) for key in ("name", "room", "hours")) for item in data), "invalid office fields")
        names = [item["name"] for item in data]
        require("Library" in names, "reference dataset must contain Library")
        require(names == sorted(names), "offices must be sorted by name")
    elif kind == "weather":
        if status == "503":
            error("weather_service_unavailable")
        else:
            require(type(data.get("temperature_c")) in (int, float), "invalid temperature")
            require(type(data.get("wind_kmh")) in (int, float), "invalid wind speed")
            require(isinstance(data.get("description"), str) and bool(data["description"]), "missing description")
            require(isinstance(data.get("observed_at"), str) and bool(data["observed_at"]), "missing observation time")
            require(isinstance(data.get("stale"), bool), "missing stale flag")
    elif kind == "not_found":
        require(isinstance(data, dict) and ("detail" in data or "error" in data), "invalid 404 body")
    else:
        error(kind)
except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
    print(f"Response validation failed: {exc}", file=sys.stderr)
    sys.exit(1)
PY
}

check() {
    local label="$1" method="$2" path="$3" codes="$4" kind="$5"
    local payload="${6:-}" auth="${7:-}" expected="${8:-}"
    if ! request "$method" "$path" "$payload" "$auth"; then
        printf 'FAIL %s: connection/timeout failure\n' "$label"
        failed=$((failed + 1))
        return 1
    fi
    if [[ " $codes " != *" $status "* ]]; then
        printf 'FAIL %s: expected HTTP %s, got %s\n' "$label" "$codes" "$status"
        failed=$((failed + 1))
        return 1
    fi
    if ! validate "$kind" "$expected"; then
        printf 'FAIL %s: HTTP %s, invalid response body\n' "$label" "$status"
        failed=$((failed + 1))
        return 1
    fi
    printf 'PASS %s [HTTP %s]\n' "$label" "$status"
    passed=$((passed + 1))
}

field() {
    "$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]])' "$body_file" "$1"
}

check 'health' GET /health 200 health || :
trace=''
chat_started=$SECONDS
if check 'chat fee' POST /v1/chat 200 fee '{"message":"tuition for 18 credits and 2 retake","session_id":"demo"}'; then
    trace=$(field request_id)
fi
check 'chat rule with source' POST /v1/chat 200 rule '{"message":"can I register my thesis with 118 credits"}' || :
check 'chat empty' POST /v1/chat 422 invalid_request '{"message":""}' || :
check 'chat wrong type' POST /v1/chat 422 invalid_request '{"message":123}' || :
created_feedback=''
if [[ -n "$trace" ]]; then
    if check 'feedback create' POST /v1/feedback 201 feedback "{\"request_id\":\"$trace\",\"rating\":1,\"comment\":\"clear answer\"}" '' "$trace"; then
        created_feedback=$(<"$body_file")
    fi
else
    printf 'FAIL feedback create: successful chat request_id unavailable\n'
    failed=$((failed + 1))
fi
check 'feedback bad rating' POST /v1/feedback 422 invalid_request '{"request_id":"abc123","rating":7}' || :
check 'list feedback without key' GET /v1/feedback 401 missing_or_invalid_api_key || :
check 'list feedback with wrong key' GET /v1/feedback 401 missing_or_invalid_api_key '' invalid || :
if [[ -z "$created_feedback" ]]; then
    printf 'NOTE feedback roundtrip not verified: no feedback was created\n'
fi
# Check T3 independently even when T2 is not implemented. A successful T2 also
# enables the created-item assertion; a failed T2 already counts as a failure.
check 'list feedback with key' GET /v1/feedback 200 feedback_list '' valid "$created_feedback" || :
check 'weather (live availability or graceful failure)' GET /v1/weather '200 503' weather || :
check 'unknown route' GET /v1/nope 404 not_found || :
if (( offices )); then
    check 'offices listing' GET /v1/offices 200 offices || :
fi
if (( bonus )); then
    # Pydantic rejects invalid bodies before the handler's limiter. Count prior
    # HTTP 200 chats, require the remaining quota, then reject exactly N+1.
    limited=0
    for ((attempt=chat_accepted + 1; attempt<=QUOTA + 1; attempt++)); do
        if (( SECONDS - chat_started >= 60 )); then
            printf 'NOTE chat quota window elapsed; rerun with a smaller server quota\n'
            break
        fi
        if ! request POST /v1/chat '{"message":"hi"}' ''; then
            break
        fi
        if (( SECONDS - chat_started >= 60 )); then
            printf 'NOTE chat quota window elapsed during the request; rerun the check\n'
            break
        fi
        if (( attempt <= QUOTA )); then
            if [[ "$status" != 200 ]] || ! validate greeting; then
                printf 'NOTE expected HTTP 200 for valid chat request %s of %s, got %s\n' "$attempt" "$QUOTA" "$status"
                break
            fi
        else
            if [[ "$status" == 429 ]] && validate too_many_requests; then limited=1; fi
        fi
    done
    if (( limited )); then
        printf 'PASS chat rate limit [HTTP 429]\n'
        passed=$((passed + 1))
    else
        printf 'FAIL chat rate limit: expected %s accepted requests, then HTTP 429\n' "$QUOTA"
        failed=$((failed + 1))
    fi
fi
printf '\nSummary: %s passed, %s failed\n' "$passed" "$failed"
(( failed == 0 ))

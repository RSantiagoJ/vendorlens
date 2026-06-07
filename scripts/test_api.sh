#!/usr/bin/env bash
# Live validation script — uses minimal test vendor docs to keep LLM cost low (~$0.05–0.10).
# Run from repo root: bash scripts/test_api.sh
#
# What this verifies:
#   1. GET /health returns {"status":"ok"}
#   2. POST /analyze returns a job_id
#   3. GET /stream/{job_id} emits: extracting → risk → scoring → memo → done
#   4. "done" event: status=done, 2 proposals, all scores present, all scores 0–10
#   5. GET /jobs/{job_id} returns persisted result with correct job_id
#
# Assumptions: API is already running at $API (default http://localhost:8000).
# Does NOT start/stop the server — run docker compose up -d before this.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DOCS="$REPO_ROOT/backend/data/vendor_proposals/test"
API="${API:-http://localhost:8000}"
PASS=0
FAIL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

assert_contains() {
  local label="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    pass "$label"
  else
    fail "$label (expected to find: $needle)"
    echo "         got: $(echo "$haystack" | head -c 200)"
  fi
}

assert_not_contains() {
  local label="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    fail "$label (should NOT contain: $needle)"
    echo "         got: $(echo "$haystack" | head -c 200)"
  else
    pass "$label"
  fi
}

extract_field() {
  # Pull a JSON string field from a line: "field":"value"
  echo "$1" | grep -o "\"$2\":\"[^\"]*\"" | head -1 | cut -d'"' -f4
}

extract_number() {
  # Pull a JSON number field: "field":3.7
  echo "$1" | grep -o "\"$2\":[0-9]*\\.\\?[0-9]*" | head -1 | cut -d: -f2
}

wait_for_server() {
  echo "Waiting for server at $API (up to 60s)..."
  for i in $(seq 1 30); do
    if curl -sf "$API/health" > /dev/null 2>&1; then
      echo "Server is up."
      return 0
    fi
    sleep 2
  done
  echo "ERROR: server did not respond after 60s"
  exit 1
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

if [ ! -f "$TEST_DOCS/alpha_lms.txt" ] || [ ! -f "$TEST_DOCS/beta_lms.txt" ]; then
  echo "ERROR: test vendor docs not found in $TEST_DOCS"
  echo "Expected: alpha_lms.txt and beta_lms.txt"
  exit 1
fi

wait_for_server

echo ""
echo "=== VendorLens live validation ==="
echo "Using: $TEST_DOCS/{alpha_lms.txt, beta_lms.txt}"
echo ""

# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

echo "[1/5] GET /health"
HEALTH=$(curl -sf "$API/health")
assert_contains "health status=ok" "$HEALTH" '"status":"ok"'
echo ""

# ---------------------------------------------------------------------------
# 2. POST /analyze
# ---------------------------------------------------------------------------

echo "[2/5] POST /analyze"
ANALYZE=$(curl -sf -X POST "$API/analyze" \
  -F "files=@$TEST_DOCS/alpha_lms.txt" \
  -F "files=@$TEST_DOCS/beta_lms.txt" \
  -F "bundle=lms")

JOB_ID=$(extract_field "$ANALYZE" "job_id")

if [ -n "$JOB_ID" ]; then
  pass "job_id present ($JOB_ID)"
else
  fail "job_id missing from /analyze response"
  echo "Response: $ANALYZE"
  exit 1
fi
echo ""

# ---------------------------------------------------------------------------
# 3. Stream — collect all events (pipeline takes 2–5 min with real LLM calls)
# ---------------------------------------------------------------------------

echo "[3/5] GET /stream/$JOB_ID  (waiting for pipeline to complete...)"
STREAM=$(curl -sN "$API/stream/$JOB_ID")

assert_contains "SSE: extracting event" "$STREAM" 'event: extracting'
assert_contains "SSE: risk event"       "$STREAM" 'event: risk'
assert_contains "SSE: scoring event"    "$STREAM" 'event: scoring'
assert_contains "SSE: memo event"       "$STREAM" 'event: memo'
assert_contains "SSE: done event"       "$STREAM" 'event: done'
assert_not_contains "SSE: no error event" "$STREAM" 'event: error'
echo ""

# ---------------------------------------------------------------------------
# 4. Validate "done" event payload
# ---------------------------------------------------------------------------

echo "[4/5] Validating done event payload"

DONE_LINE=$(echo "$STREAM" | grep '^data:' | tail -1)
DONE_DATA="${DONE_LINE#data: }"

assert_contains "done.status=done"       "$DONE_DATA" '"status":"done"'
assert_contains "done.job_id present"    "$DONE_DATA" "\"job_id\":\"$JOB_ID\""
assert_contains "done.memo present"      "$DONE_DATA" '"memo":"'

# Two proposals (one per vendor file)
PROPOSAL_COUNT=$(echo "$DONE_DATA" | grep -o '"filename":' | wc -l | tr -d ' ')
if [ "$PROPOSAL_COUNT" -eq 2 ]; then
  pass "done.proposals count=2"
else
  fail "done.proposals count expected 2, got $PROPOSAL_COUNT"
fi

# Scores are present and within 0–10
SCORES=$(echo "$DONE_DATA" | grep -o '"overall":[0-9]*\.\?[0-9]*')
SCORE_COUNT=$(echo "$SCORES" | wc -l | tr -d ' ')
if [ "$SCORE_COUNT" -ge 2 ]; then
  pass "done.scores present (${SCORE_COUNT} overall scores found)"
else
  fail "done.scores missing (expected >=2 overall scores)"
fi

SCORES_OUT_OF_RANGE=$(echo "$SCORES" | awk -F: '$2+0 > 10 || $2+0 < 0 {print}')
if [ -z "$SCORES_OUT_OF_RANGE" ]; then
  pass "done.scores all in 0–10 range"
else
  fail "done.scores out of range: $SCORES_OUT_OF_RANGE"
fi
echo ""

# ---------------------------------------------------------------------------
# 5. GET /jobs/{job_id} — persistence check
# ---------------------------------------------------------------------------

echo "[5/5] GET /jobs/$JOB_ID"
PERSISTED=$(curl -sf "$API/jobs/$JOB_ID")

assert_contains "jobs.job_id matches"  "$PERSISTED" "\"job_id\":\"$JOB_ID\""
assert_contains "jobs.status=done"     "$PERSISTED" '"status":"done"'
assert_contains "jobs.memo present"    "$PERSISTED" '"memo":"'
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

TOTAL=$((PASS + FAIL))
echo "=== Results: $PASS/$TOTAL passed ==="
if [ "$FAIL" -gt 0 ]; then
  echo "FAILED ($FAIL assertion(s) failed)"
  exit 1
else
  echo "All checks passed."
  exit 0
fi

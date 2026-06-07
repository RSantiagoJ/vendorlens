#!/usr/bin/env bash
# preflight.sh — Pre-demo validation. Run this before every live presentation.
#
# Checks every layer of the system without making API calls or hitting the UI:
#   1. Environment variables
#   2. Context bundle files (rubric, criteria, policy)
#   3. Vendor proposal files (ChromaDB source data)
#   4. Mock test suite (77 tests, all layers)
#
# Usage:
#   cd /path/to/vendorlens
#   ./scripts/preflight.sh
#
# Exit code 0 = GO. Exit code 1 = one or more checks failed.

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

green()  { printf "\033[0;32m✓\033[0m %s\n" "$*"; }
red()    { printf "\033[0;31m✗\033[0m %s\n" "$*"; }
header() { printf "\n\033[1m%s\033[0m\n" "$*"; }

check() {
    local label="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        green "$label"
        PASS=$((PASS + 1))
    else
        red "$label — $result"
        FAIL=$((FAIL + 1))
    fi
}

# ---------------------------------------------------------------------------
printf "\n\033[1mVendorLens Pre-Demo Validation\033[0m\n"
printf "%.0s─" {1..40}; printf "\n"
# ---------------------------------------------------------------------------

header "1. Environment"

if [ -f "$BACKEND_DIR/.env" ]; then
    check ".env file exists" "ok"
else
    check ".env file exists" "not found at backend/.env"
fi

if grep -q "ANTHROPIC_API_KEY" "$BACKEND_DIR/.env" 2>/dev/null && \
   ! grep -q "ANTHROPIC_API_KEY=$" "$BACKEND_DIR/.env" && \
   ! grep -q "ANTHROPIC_API_KEY=\"\"" "$BACKEND_DIR/.env"; then
    check "ANTHROPIC_API_KEY set" "ok"
else
    check "ANTHROPIC_API_KEY set" "not set or empty in backend/.env"
fi

# ---------------------------------------------------------------------------
header "2. Context Bundle Files (LMS)"

BUNDLE="$BACKEND_DIR/data/context_bundles/lms"
for f in policy.txt rfp_criteria_lms.txt scoring_rubric_lms.txt; do
    if [ -f "$BUNDLE/$f" ]; then
        check "lms/$f" "ok"
    else
        check "lms/$f" "MISSING — pipeline will crash without this"
    fi
done

# ---------------------------------------------------------------------------
header "3. Vendor Proposal Files"

PROPOSALS="$BACKEND_DIR/data/vendor_proposals/lms"
for f in blackboard.txt canvas.txt brightspace.txt; do
    if [ -f "$PROPOSALS/$f" ]; then
        check "vendor_proposals/lms/$f" "ok"
    else
        check "vendor_proposals/lms/$f" "MISSING — run scripts/ingest.py after adding"
    fi
done

# ---------------------------------------------------------------------------
header "4. ChromaDB Index"

CHROMA="$BACKEND_DIR/data/chroma_db"
if [ -d "$CHROMA" ] && [ "$(ls -A "$CHROMA" 2>/dev/null)" ]; then
    check "ChromaDB directory has data" "ok"
else
    check "ChromaDB directory has data" "empty or missing — run: docker compose run --rm backend python scripts/ingest.py"
fi

# ---------------------------------------------------------------------------
header "5. Mock Test Suite (no API calls)"

printf "\nRunning 77 offline tests...\n"
if sg docker -c "docker compose -f '$ROOT_DIR/docker-compose.yml' run --rm backend \
    python -m pytest tests/test_boundaries.py tests/test_mock_pipeline.py \
    tests/test_persistence.py tests/test_reliability.py -q --tb=short 2>&1"; then
    PASS=$((PASS + 1))
    green "All mock tests passed"
else
    FAIL=$((FAIL + 1))
    red "Mock tests FAILED — do not present until all tests pass"
fi

# ---------------------------------------------------------------------------
printf "\n"
printf "%.0s─" {1..40}; printf "\n"

TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    printf "\033[0;32m\033[1mGO\033[0m  — %d/%d checks passed. System ready.\n\n" "$PASS" "$TOTAL"
    exit 0
else
    printf "\033[0;31m\033[1mNO-GO\033[0m — %d/%d checks failed. Fix before presenting.\n\n" "$FAIL" "$TOTAL"
    exit 1
fi

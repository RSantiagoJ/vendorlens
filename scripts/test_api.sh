#!/usr/bin/env bash
# Day 5 checkpoint: start the API server, run health + analyze + stream.
# Run from the repo root: bash scripts/test_api.sh
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_DIR="$REPO_ROOT/backend/data/dummy_docs"
API="http://localhost:8000"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

extract_job_id() {
  # Pure bash JSON extraction — no jq or python required.
  echo "$1" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4
}

wait_for_server() {
  echo "==> Waiting for server (up to 60s)..."
  for i in $(seq 1 30); do
    if curl -sf "$API/health" > /dev/null 2>&1; then
      echo "    Ready."
      return 0
    fi
    sleep 2
  done
  echo "ERROR: Server did not respond after 60s."
  exit 1
}

# ---------------------------------------------------------------------------
# Start server in background, kill on exit
# ---------------------------------------------------------------------------

echo "==> Starting API server inside Docker..."
sudo docker compose -f "$REPO_ROOT/docker-compose.yml" run \
  --rm -p 8000:8000 backend \
  uvicorn api.main:app --host 0.0.0.0 --port 8000 &

SERVER_PID=$!

cleanup() {
  echo ""
  echo "==> Stopping server (PID $SERVER_PID)..."
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait_for_server

# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

echo ""
echo "--- [1/3] GET /health ---"
curl -s "$API/health"
echo ""

# ---------------------------------------------------------------------------
# 2. POST /analyze
# ---------------------------------------------------------------------------

echo ""
echo "--- [2/3] POST /analyze (submitting 3 vendor docs) ---"
RESPONSE=$(curl -s -X POST "$API/analyze" \
  -F "files=@$DOCS_DIR/vendor_a_blackboard.txt" \
  -F "files=@$DOCS_DIR/vendor_b_canvas.txt" \
  -F "files=@$DOCS_DIR/vendor_c_brightspace.txt")

echo "$RESPONSE"
JOB_ID=$(extract_job_id "$RESPONSE")

if [ -z "$JOB_ID" ]; then
  echo "ERROR: No job_id in response. Check the server log above."
  exit 1
fi

echo ""
echo "    job_id: $JOB_ID"

# ---------------------------------------------------------------------------
# 3. Stream progress + result
# ---------------------------------------------------------------------------

echo ""
echo "--- [3/3] GET /stream/$JOB_ID ---"
echo "    Pipeline takes ~5 min. Watch for: extracting → risk → scoring → memo → done"
echo ""

curl -N "$API/stream/$JOB_ID"

echo ""
echo "==> Day 5 checkpoint complete."

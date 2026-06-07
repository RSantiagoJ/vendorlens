#!/usr/bin/env bash
# Day 1 smoke test — Ubuntu/Linux equivalent of smoke_day1.ps1
# Usage:
#   ./backend/smoke_day1.sh              # build + reindex + test
#   ./backend/smoke_day1.sh --skip-build # skip image build
#   ./backend/smoke_day1.sh --skip-reindex # skip vector index rebuild

set -euo pipefail

SKIP_BUILD=0
SKIP_REINDEX=0

for arg in "$@"; do
  case $arg in
    --skip-build)    SKIP_BUILD=1 ;;
    --skip-reindex)  SKIP_REINDEX=1 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

run_step() {
  local label="$1"; shift
  echo "==> $label"
  "$@"
}

if [ "$SKIP_BUILD" -eq 0 ]; then
  run_step "Building backend image" docker compose build backend
fi

if [ "$SKIP_REINDEX" -eq 0 ]; then
  run_step "Rebuilding vector index" docker compose run --rm backend python ingest.py --force
fi

run_step "Running Day 1 RAG checkpoint" docker compose run --rm backend python test_rag.py

echo ""
echo "Day 1 smoke check passed."

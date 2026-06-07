#!/usr/bin/env bash
# First-time setup for VendorLens.
# Run once from the repo root after cloning: bash scripts/setup.sh
#
# What it does:
#   1. Builds the Docker image
#   2. Ingests all vendor proposals into ChromaDB
#   3. Starts the API (detached, port 8000)
#   4. Installs frontend deps and starts Next.js (port 3000)
#
# Prerequisites: Docker, Node.js/npm, and backend/.env populated with API keys.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

echo "==> [1/4] Building Docker image..."
docker compose -f "$REPO_ROOT/docker-compose.yml" build

echo ""
echo "==> [2/4] Ingesting vendor proposals into ChromaDB..."
docker compose -f "$REPO_ROOT/docker-compose.yml" run --rm backend \
  python scripts/ingest.py --force

echo ""
echo "==> [3/4] Starting API server (detached, port 8000)..."
docker compose -f "$REPO_ROOT/docker-compose.yml" up api -d

echo ""
echo "==> [4/4] Starting Next.js frontend (port 3000)..."
cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
  echo "    Installing frontend dependencies..."
  npm install
fi
npm run dev

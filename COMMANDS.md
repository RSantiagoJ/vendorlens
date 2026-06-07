# VendorLens — Command Reference

All commands run from the **repository root** unless noted.
All Python runs inside Docker — never `python3` on the host directly.
All `docker` commands require the docker group — prefix with `sg docker -c "..."` if you get a permission error:
```bash
sg docker -c "docker compose up api db -d"
```

---

## Before Every Demo

```bash
./scripts/preflight.sh
```

Checks API key, all data files, ChromaDB, and runs the offline test suite.
**GO = ready. NO-GO = tells you exactly what to fix.**

---

## First-Time Setup

```bash
# 1. Build the Docker image
sg docker -c "docker compose build"

# 2. Populate backend/.env (ANTHROPIC_API_KEY is required)

# 3. Ingest vendor proposals into ChromaDB
sg docker -c "docker compose run --rm backend python scripts/ingest.py --force"

# 4. Start the app
sg docker -c "docker compose up api db -d"
cd frontend && npm run dev
```

Or run all four steps at once:
```bash
bash scripts/setup.sh
```

---

## Start / Stop

| What | Command |
|------|---------|
| Start API + DB (background) | `sg docker -c "docker compose up api db -d"` |
| Start frontend | `cd frontend && npm run dev` |
| Stop everything | `sg docker -c "docker compose stop"` |
| Stop and remove containers | `sg docker -c "docker compose down"` |
| Check what's running | `sg docker -c "docker compose ps"` |

---

## Restart After Changes

| Change made | Command |
|-------------|---------|
| Any `.py` file | `sg docker -c "docker compose restart api"` |
| `requirements.txt` or `Dockerfile` | `sg docker -c "docker compose up --build api db -d"` |
| `.env` file | `sg docker -c "docker compose down && docker compose up api db -d"` |
| Frontend (`.tsx`, `.ts`, CSS) | No restart — Next.js hot-reloads |
| Something broken, no idea why | `sg docker -c "docker compose down && docker compose up --build api db -d"` |

---

## Logs

```bash
sg docker -c "docker compose logs api -f"    # live API logs
sg docker -c "docker compose logs db -f"     # Postgres logs
sg docker -c "docker compose logs -f"        # everything
```

---

## Tests

### Offline — no API calls, runs in ~5s

```bash
sg docker -c "docker compose run --rm backend python -m pytest tests/ -q"
```

`tests/live/` is excluded automatically via `pytest.ini` (`norecursedirs`).

### Individual test files

| What it tests | Command |
|---------------|---------|
| Data contracts at every pipeline boundary (B0–B8) | `... pytest tests/test_boundaries.py -v` |
| Full pipeline happy/failure paths (mocked) | `... pytest tests/test_mock_pipeline.py -v` |
| NegotiationAgent unit tests + model shape | `... pytest tests/test_negotiation_agent.py -v` |
| Persistence layer — DB write, GET /jobs, /progress | `... pytest tests/test_persistence.py -v` |
| Concurrency, ingest dedup, output structure | `... pytest tests/test_reliability.py -v` |
| Full HTTP flow: upload → poll → result (E2E) | `... pytest tests/test_e2e.py -v` |

### Live tests — require `ANTHROPIC_API_KEY` + ingested ChromaDB

These are in `tests/live/` and excluded from the default run. Use minimal test files only.

```bash
# RAG retrieval (no LLM calls — just ChromaDB)
sg docker -c "docker compose run --rm backend python -m pytest tests/live/test_rag.py -v"

# Extraction + risk + scoring (~$0.05 — uses alpha_lms.txt, beta_lms.txt only)
sg docker -c "docker compose run --rm backend python -m pytest tests/live/test_agents.py -v"

# Full pipeline smoke test (~$0.05)
sg docker -c "docker compose run --rm backend python -m pytest tests/live/test_smoke.py -v"
```

**Always use `backend/data/vendor_proposals/test/` files (`alpha_lms.txt`, `beta_lms.txt`) for live tests — not the full LMS/ERP/Payroll corpus.**

---

## Scripts

| Task | Command |
|------|---------|
| Ingest / re-ingest proposals into ChromaDB | `sg docker -c "docker compose run --rm backend python scripts/ingest.py --force"` |
| Pre-demo validation | `./scripts/preflight.sh` |
| Open a shell inside the container | `sg docker -c "docker compose run --rm backend bash"` |
| Connect to Postgres | `sg docker -c "docker compose exec db psql -U vendorlens vendorlens"` |

**Re-run ingest when:**
- You add, rename, or edit a proposal file
- Extraction returns null for every field (stale index symptom)
- After a full Docker rebuild

---

## API Endpoints (local)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `http://localhost:8000/health` | Health check |
| `GET` | `http://localhost:8000/bundles` | List RFP bundles |
| `POST` | `http://localhost:8000/analyze` | Upload proposals → returns `job_id` |
| `GET` | `http://localhost:8000/jobs/{job_id}/progress` | Poll current stage (pending → extracting → risk → scoring → memo → done) |
| `GET` | `http://localhost:8000/jobs/{job_id}` | Fetch persisted result from Postgres |
| `GET` | `http://localhost:8000/stream/{job_id}` | SSE stream (legacy — prefer `/progress` polling) |
| `POST` | `http://localhost:8000/reload` | Clear pipeline cache (after ingest without restart) |

---

## Production — URLs

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://vendorlens-beryl.vercel.app |
| Backend (AWS App Runner) | https://brpste4mu9.us-east-1.awsapprunner.com |
| Health check | https://brpste4mu9.us-east-1.awsapprunner.com/health |
| ECR repo | `438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend` |
| S3 uploads bucket | `vendorlens-uploads-438920434591` |

---

## Deploy Backend (App Runner via ECR)

```bash
bash scripts/deploy_backend.sh
```

Manual steps if needed:

```bash
# 1. Authenticate with ECR
~/.local/bin/aws ecr get-login-password --region us-east-1 \
  | sg docker -c "docker login --username AWS --password-stdin \
    438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend"

# 2. Build for linux/amd64 (required for App Runner)
sg docker -c "docker build --platform linux/amd64 -t vendorlens-backend backend/"

# 3. Tag and push
sg docker -c "docker tag vendorlens-backend:latest \
  438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest"
sg docker -c "docker push \
  438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest"

# 4. Trigger App Runner deployment
~/.local/bin/aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:438920434591:service/vendorlens/696cbbb5a5b74503b0819ec443fff652 \
  --region us-east-1
```

---

## Deploy Frontend (Vercel)

Vercel deploys automatically on every push to `main`.

```bash
git push origin main    # triggers Vercel deploy automatically
```

---

## Tear Down AWS (stops all charges)

```bash
cd terraform && terraform destroy
```

---

## Live Validation

```bash
# Run against local backend
./scripts/test_api.sh

# Run against production backend
API=https://brpste4mu9.us-east-1.awsapprunner.com ./scripts/test_api.sh
```

Uses `backend/data/vendor_proposals/test/{alpha_lms.txt, beta_lms.txt}` — minimal docs, low cost.

---

## Useful One-Liners

```bash
# Check API is alive
curl http://localhost:8000/health

# Check production API is alive
curl https://brpste4mu9.us-east-1.awsapprunner.com/health

# View all ChromaDB collections
sg docker -c "docker compose run --rm backend python -c \
  \"import chromadb; c = chromadb.PersistentClient('data/chroma_db'); print(c.list_collections())\""

# Count indexed chunks per vendor
sg docker -c "docker compose run --rm backend python -c \"
import chromadb
c = chromadb.PersistentClient('data/chroma_db')
col = c.get_collection('vendor_proposals')
for vendor in ['blackboard.txt', 'canvas.txt', 'brightspace.txt']:
    r = col.get(where={'file_name': vendor}, include=[])
    print(f'{vendor}: {len(r[\"ids\"])} chunks')
\""
```

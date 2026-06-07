# VendorLens — Command Reference

All commands run from the **repository root** unless noted.
All Python runs inside Docker — never `python3` on the host directly.

---

## Before Every Demo

```bash
./scripts/preflight.sh
```

Checks API key, all data files, ChromaDB, and runs 77 offline tests.
**GO = ready. NO-GO = tells you exactly what to fix.**

---

## First-Time Setup

```bash
# 1. Build the Docker image
docker compose build

# 2. Populate backend/.env (ANTHROPIC_API_KEY is required)

# 3. Ingest vendor proposals into ChromaDB
docker compose run --rm backend python scripts/ingest.py --force

# 4. Start the app
docker compose up api db -d
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
| Start API + DB (background) | `docker compose up api db -d` |
| Start frontend | `cd frontend && npm run dev` |
| Stop everything | `docker compose stop` |
| Stop and remove containers | `docker compose down` |
| Check what's running | `docker compose ps` |

---

## Restart After Changes

| Change made | Command |
|-------------|---------|
| Any `.py` file | `docker compose restart api` |
| `requirements.txt` or `Dockerfile` | `docker compose up --build api db -d` |
| `.env` file | `docker compose down && docker compose up api db -d` |
| Frontend (`.tsx`, `.ts`, CSS) | No restart — Next.js hot-reloads |
| Something broken, no idea why | `docker compose down && docker compose up --build api db -d` |

---

## Logs

```bash
docker compose logs api -f          # live API logs
docker compose logs db -f           # Postgres logs
docker compose logs -f              # everything
```

---

## Tests

### Offline — no API calls, runs in ~5s

```bash
docker compose run --rm backend python -m pytest \
  tests/test_boundaries.py \
  tests/test_mock_pipeline.py \
  tests/test_persistence.py \
  tests/test_reliability.py \
  -v
```

### Individual test files

| What it tests | Command |
|---------------|---------|
| Data contracts at every pipeline boundary | `... pytest tests/test_boundaries.py -v` |
| Full pipeline happy/failure paths (mocked) | `... pytest tests/test_mock_pipeline.py -v` |
| Persistence layer — DB write, GET /jobs | `... pytest tests/test_persistence.py -v` |
| Concurrency, ingest dedup, output structure | `... pytest tests/test_reliability.py -v` |

### Integration — requires `ANTHROPIC_API_KEY` + ingested ChromaDB

```bash
# RAG retrieval (no LLM calls — just ChromaDB)
docker compose run --rm backend python tests/test_rag.py

# Extraction + risk + scoring (uses real LLM — ~$0.05)
docker compose run --rm backend python tests/test_agents.py

# Full pipeline, one vendor (real LLM — ~$0.05)
docker compose run --rm backend python tests/test_smoke.py --vendor canvas.txt

# Full pipeline, dry-run (no LLM — just agent init)
docker compose run --rm backend python tests/test_smoke.py --dry-run
```

---

## Scripts

| Task | Command |
|------|---------|
| Ingest / re-ingest proposals into ChromaDB | `docker compose run --rm backend python scripts/ingest.py --force` |
| Pre-demo validation | `./scripts/preflight.sh` |
| Open a shell inside the container | `docker compose run --rm backend bash` |
| Connect to Postgres | `docker compose exec db psql -U vendorlens vendorlens` |

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
| `GET` | `http://localhost:8000/stream/{job_id}` | SSE live progress stream |
| `GET` | `http://localhost:8000/jobs/{job_id}` | Fetch persisted result from Postgres |
| `POST` | `http://localhost:8000/reload` | Clear pipeline cache (after ingest without restart) |

---

## Production — URLs

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://vendorlens-beryl.vercel.app |
| Backend (AWS App Runner) | https://brpste4mu9.us-east-1.awsapprunner.com |
| Health check | https://brpste4mu9.us-east-1.awsapprunner.com/health |

---

## Deploy Backend to AWS (App Runner via ECR)

```bash
# 1. Authenticate with ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend

# 2. Build for linux/amd64 (required for App Runner)
docker build --platform linux/amd64 -t vendorlens-backend backend/

# 3. Tag and push
docker tag vendorlens-backend:latest \
  438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest

docker push \
  438920434591.dkr.ecr.us-east-1.amazonaws.com/vendorlens-backend:latest

# App Runner auto-deploys on push (auto_deployments_enabled = true)
```

---

## Deploy Frontend to Vercel

Vercel deploys automatically on every push to `main`.

```bash
git push origin main        # triggers Vercel deploy automatically
```

To deploy manually or preview a branch:
```bash
npx vercel                  # preview deploy (from frontend/ directory)
npx vercel --prod           # production deploy
```

Check deploy status: https://vercel.com/dashboard

---

## Tear Down AWS (stops all charges)

```bash
cd terraform && terraform destroy
```

---

## Useful One-Liners

```bash
# Check API is alive
curl http://localhost:8000/health

# Check production API is alive
curl https://brpste4mu9.us-east-1.awsapprunner.com/health

# View all ChromaDB collections
docker compose run --rm backend python -c \
  "import chromadb; c = chromadb.PersistentClient('data/chroma_db'); print(c.list_collections())"

# Count indexed chunks per vendor
docker compose run --rm backend python -c "
import chromadb
c = chromadb.PersistentClient('data/chroma_db')
col = c.get_collection('vendor_proposals')
for vendor in ['blackboard.txt', 'canvas.txt', 'brightspace.txt']:
    r = col.get(where={'file_name': vendor}, include=[])
    print(f'{vendor}: {len(r[\"ids\"])} chunks')
"
```

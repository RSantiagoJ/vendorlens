# VendorLens — Backend & Run Guide

All Python runs inside Docker. Never run `python3` directly on the host.

---

## Start the full application (one command)

From the repository root:

```bash
docker compose up api -d && cd frontend && npm run dev
```

- `api` starts the FastAPI backend on port 8000 (detached)
- `npm run dev` starts the Next.js frontend on port 3000
- Open http://localhost:3000

---

## First-time setup (do these once, in order)

### Step 1 — Build the Docker image

```bash
docker compose build
```

Do this once after cloning. Re-run if `requirements.txt` or the `Dockerfile` changes.

### Step 2 — Populate API keys

Edit `backend/.env` and fill in:

```
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
LANGCHAIN_API_KEY=...         # optional — enables LangSmith tracing
LANGCHAIN_TRACING_V2=true     # optional
```

`GOOGLE_API_KEY` is required (used for embeddings and Gemini extraction/scoring).
`ANTHROPIC_API_KEY` is required (used for the memo agent).

### Step 3 — Ingest vendor proposals into ChromaDB

```bash
docker compose run --rm backend python scripts/ingest.py --force
```

This reads every `.txt` file under `data/vendor_proposals/`, generates embeddings via Google's
API, and stores them in ChromaDB. **The pipeline cannot run without this step.**

After rebuilding, the script automatically signals the API to reload its index cache via
`POST /reload`. If the API isn't running yet, the fresh index loads on next startup — no
manual restart needed.

**Re-run this command whenever:**
- You add a new proposal file to `vendor_proposals/`
- You rename or delete a proposal file
- You edit the content of an existing proposal file
- Extraction returns null fields or "Not Available" for everything (symptoms of a stale index)

Without `--force`, the script skips ingestion if a collection already exists. Use `--force`
to wipe and rebuild from scratch — always safe to run.

**Signs of a stale index:**
- Extraction phase completes almost instantly (under 2 seconds)
- All fields show "Not Available" or "null" in the memo
- The memo says a file "returned null on all extraction fields"

If you see any of these, run ingest `--force` and wait for the "API cache reloaded" confirmation.

### Step 4 — Start the app

```bash
docker compose up api -d && cd frontend && npm run dev
```

---

## Vendor proposals

Sample proposals live in `backend/data/vendor_proposals/` organized by bundle:

```
vendor_proposals/
  lms/        blackboard.txt   canvas.txt      brightspace.txt
  payroll/    adp.txt          ceridian.txt    paylocity.txt
  erp/        workday.txt      oracle_cloud.txt  unit4.txt
```

Upload any of these files (or real `.txt` / `.pdf` proposals) via the frontend.
The filename you upload is the key used to look up that document in ChromaDB —
it must match exactly what was ingested.

---

## RFP bundles

Each bundle has its own procurement policy, scoring criteria, and rubric.
Select the bundle in the UI before uploading proposals.

| Bundle ID | Label                     | Use case                              |
|-----------|---------------------------|---------------------------------------|
| `lms`     | LMS Platform RFP          | Learning management system evaluation |
| `payroll` | Payroll Processing RFP    | Full-service payroll processor         |
| `erp`     | Finance & HR Platform RFP | Enterprise ERP (finance + HR)          |

Bundle context files live in `backend/data/context_bundle_<id>/`.

---

## Common tasks and when to run each command

| Situation | Command |
|-----------|---------|
| First time setup | `docker compose build` then ingest (Step 3 above) |
| Added or renamed a proposal file | `docker compose run --rm backend python scripts/ingest.py --force` (auto-reloads API) |
| Starting the app for a demo | `docker compose up api -d && cd frontend && npm run dev` |
| API is running but frontend won't connect | Check that `api` container is up: `docker compose ps` |
| Want to test the pipeline without the UI | `docker compose run --rm backend python tests/test_pipeline.py` |
| Debugging extraction or scoring | `docker compose run --rm backend python tests/test_agents.py` |
| Checking RAG retrieval is working | `docker compose run --rm backend python tests/test_rag.py` |
| Opening a shell inside the container | `docker compose run --rm backend bash` |

---

## API endpoints

| Method | Path               | Description                                              |
|--------|--------------------|----------------------------------------------------------|
| GET    | `/health`          | Health check → `{"status": "ok"}`                        |
| GET    | `/bundles`         | List available RFP bundles                               |
| POST   | `/analyze`         | Upload proposals + bundle; returns `job_id`              |
| GET    | `/stream/{job_id}` | SSE stream: `extracting → risk → scoring → memo → done`  |

---

## Notes

- `requirements.lock.txt` is used during image build for reproducible installs.
- `requirements.txt` is the editable source dependency list.
- LangSmith tracing is automatic when `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set.

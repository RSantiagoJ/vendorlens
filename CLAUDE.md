# VendorLens — Claude Code Instructions

Read this entire file before doing anything. These rules exist because real bugs
were introduced by skipping them. Follow them exactly.

---

## Environment

- **All Python runs inside Docker.** Never run `python3` or `pytest` directly on
  the host. Always use:
  ```
  docker compose run --rm backend <command>
  ```
- The `backend` service mounts `./backend` at `/app`. Edit files locally;
  run them in the container.
- Use `sg docker -c "docker compose ..."` if the host shell lacks the docker group.

---

## Test-First Rule — Non-Negotiable

**Before modifying any of the following, write a failing test that proves the
current behavior:**

- Any agent (`extraction_agent`, `risk_agent`, `scoring_agent`, `memo_agent`)
- Any pipeline node or graph structure (`graph/pipeline.py`)
- Any state or data model (`graph/state.py`, `api/models.py`)
- Any shared utility (`tools/llm_factory.py`, `tools/chroma.py`)

The sequence is always:
1. Write the test. Run it. Confirm it fails for the right reason.
2. Make the change.
3. Run the test again. Confirm it passes.
4. Run the full suite to confirm nothing else broke.

**Never skip step 1.** This is what caused bugs to accumulate undetected across
multiple sessions — an LLM fixed a symptom (e.g. the score display) at one
layer without knowing it broke a contract at another.

---

## Where Tests Live

| File | What it covers |
|------|---------------|
| `backend/tests/test_boundaries.py` | Data shape at every inter-layer handoff (B1–B7). Update this when any data contract changes. |
| `backend/tests/test_mock_pipeline.py` | Full pipeline happy path + failure paths. Update this when pipeline structure or output changes. |
| `backend/tests/test_persistence.py` | Postgres persistence layer — `AnalysisRun` model, `_persist_run()`, `GET /jobs/{job_id}` endpoint (15 tests). |

All tests must work **without API keys**. Use `unittest.mock.patch` to stub
`invoke_llm_cached`, `make_claude_llm`, `make_haiku_llm`, and any file I/O.
The `conftest.py` autouse fixture handles LLM construction mocking automatically.

Run the full suite before and after every change:
```
docker compose run --rm backend python -m pytest tests/test_boundaries.py tests/test_mock_pipeline.py -v
```

---

## Pipeline Architecture

The pipeline is a LangGraph graph with this data flow:

```
START → warm_caches → [Send per vendor] → vendor_subgraph → memo_node → END

vendor_subgraph:
  extract_node → risk_node → score_node
  (each node writes to VendorSubgraphState as plain dicts)
  score_node always emits {"proposals": [ProposalState.model_dump()]}
```

**Critical contracts at each boundary:**

| From | To | Data shape |
|------|----|-----------|
| `extract_node` | `risk_node` | `{"extracted": ProposalData.model_dump()}` |
| `risk_node` | `score_node` | `{"risks": [RiskFlag.model_dump(), ...]}` |
| `score_node` | `memo_node` (via fan-in) | `{"proposals": [ProposalState.model_dump()]}` |
| `memo_node` | API result | `memo: str` (never list) |

When you change a node's output shape, update `test_boundaries.py` first.

---

## Scoring Scale

Dimension scores are **0–10**. The overall score is the **weighted sum of
dimension scores**, which also produces a value in **0–10**. The rubric file
(`rfp_criteria_lms.txt`) documents this and the LLM is instructed accordingly.

Do not multiply by 10. Do not normalize to 0–100. The `* 10` bug was introduced
by an LLM "fixing" the UI display without checking the backend contract —
`test_boundaries.py::TestB7ScoringScale` will catch this regression.

---

## LLM Response Handling

LLM calls go through `invoke_llm_cached` in `tools/llm_factory.py`. Its return
value is `llm.invoke(...).content`, which is normally `str` but can be a
**list of content block dicts** from Anthropic's API.

- `parse_llm_json` handles both — use it for all structured (JSON) responses.
- For unstructured responses (e.g. memo markdown), normalize manually:
  ```python
  if isinstance(result, list):
      result = "".join(part["text"] if isinstance(part, dict) else str(part) for part in result)
  ```
- Never return a raw `invoke_llm_cached` result from a public method without
  normalizing it to `str` first.

---

## Why Errors Can Be Vendor-Specific

The same code can fail for one vendor and pass for another because LLM output
format depends on document content. A document with unusual structure can cause
the LLM to add preamble text, change a field type (e.g. `deliverables` as a
string instead of a list), or format JSON differently. Tests must cover these
edge cases — not just the happy path with clean data.

This is why `test_boundaries.py` tests cases like:
- JSON array with preamble text
- `deliverables` as a string instead of a list
- Invalid `severity` literals in risk flags

---

## Persistence Layer

VendorLens uses Postgres to persist completed pipeline runs so results survive API restarts.

### Package layout

```
backend/db/
  __init__.py   — re-exports Session, Base
  session.py    — SQLAlchemy engine + SessionLocal factory (reads DATABASE_URL from env)
  models.py     — AnalysisRun table (job_id PK, bundle, status, result JSON, timestamps)
```

### Environment variable

`DATABASE_URL` must be set in `.env` (or docker-compose environment):
```
DATABASE_URL=postgresql://vendorlens:vendorlens@db:5432/vendorlens
```

The `db` service is defined in `docker-compose.yml` (postgres:16-alpine). The `api` service
depends on it. Tables are created automatically on startup via `Base.metadata.create_all()`.

### How persistence works

1. `POST /analyze` creates an `AnalysisRun` row with `status="pending"` before the pipeline starts.
2. `_persist_run()` in `api/main.py` upserts the row at `status="done"` or `status="error"`.
3. `GET /jobs/{job_id}` returns the persisted result directly from Postgres — useful for polling
   after a restart or when the SSE stream was not consumed.

### Test coverage

`backend/tests/test_persistence.py` — 15 tests covering model creation, upsert idempotency,
missing-job 404, and error-result persistence. Uses an in-memory SQLite database (no Docker needed).

---

## Before Touching the UI

UI changes that affect how scores, statuses, or risk data are displayed must be
checked against the backend types in `graph/state.py` and `api/models.py`.
Do not "fix" a display issue by changing a number at the source (e.g. adding
a multiplier) without first checking what range that value is supposed to be in
and whether a test documents that range.

---

## Committing

- Commit message format: `type: short description` (fix, feat, refactor, test, docs, chore)
- Include what broke and why in the body for bug fixes, not just what changed.
- Always run the full test suite before committing.

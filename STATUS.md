# VendorLens — Current Status

> This file is the single-source-of-truth for current project state.
> Updated by Claude at the end of every session and by the daily audit.
> A fresh Claude session should read this before doing anything else.

---

## System State (as of 2026-06-07)

**Working end-to-end:** Yes. Full pipeline runs locally via Docker.
**Tests:** 109 passing, 0 failing. All offline (no API keys needed).
**Deployment:** Frontend on Vercel. Backend on AWS App Runner.

### Services
| Service | Status | Notes |
|---------|--------|-------|
| FastAPI backend | ✓ Running | Port 8000 via Docker |
| Postgres DB | ✓ Running | Port 5432 via Docker, `analysis_runs` table |
| ChromaDB | ✓ Populated | 3 LMS vendors ingested |
| Next.js frontend | ✓ Running | Port 3000 |

---

## Settled Decisions — Do Not Re-Open

These have been evaluated and closed. Do not suggest alternatives.

| Decision | Reason |
|----------|--------|
| Scoring scale: 0–10 (not 0–100) | Rubric explicitly states max 10.0. The ×10 multiplier was a bug introduced by an LLM. |
| Drizzle ORM: not applicable | TypeScript-only ORM. Backend is Python. Not usable here. |
| Risk + scoring as separate nodes | Merging saves 3 LLM calls but adds complexity. Deferred — not worth it at current scale. |
| Fan-out per vendor (parallel) | Settled architecture. Vendors are isolated, failures don't cascade. |
| Claude + FastEmbed only | Switched from Google/Gemini in day8. No Google API key needed. |
| Per-stage specialization over single-pass | Single mega-prompt produces worse structured output. Specialization wins. |
| Pydantic v2 for all state models | Strict validation, nested model coercion, clean model_dump(). |

---

## Architecture Snapshot

```
POST /analyze
  → ingest files to ChromaDB (deduplicated)
  → _run_pipeline (ThreadPoolExecutor)
      → warm_caches (3 LLM calls, non-fatal on failure)
      → fan-out: vendor_subgraph per vendor (parallel)
          → extract_node  (Sonnet — RAG + structured extraction)
          → risk_node     (Sonnet — policy lookup + risk flags)
          → score_node    (Haiku — rubric scoring, 0–10 scale)
      → fan-in → memo_node (Sonnet — recommendation memo)
  → _persist_run → analysis_runs table (Postgres)
  → _schedule_eviction (TTL: 10 min from _jobs)

GET /stream/{job_id}  → SSE live progress
GET /jobs/{job_id}    → persisted result (survives restarts)
```

**LLM calls per 3-vendor run: 13**
- 3 warm-up (amortized via prompt caching)
- 3 extract + 3 risk + 3 score
- 1 memo

**Token flow (distillation funnel):**
Raw doc → ProposalData JSON → RiskFlags → ScoreCard → Memo (each stage shrinks input)

---

## Test Coverage

| File | Tests | What it covers |
|------|-------|---------------|
| `test_boundaries.py` | 47 | Data shape at every inter-layer handoff (B0–B7) |
| `test_mock_pipeline.py` | 17 | Full pipeline happy path + all failure modes |
| `test_persistence.py` | 33 | DB write, GET endpoint, error persistence, TTL, rfp_name, /progress endpoint |
| `test_reliability.py` | 8 | Concurrency, ingest dedup, output structure |
| `test_e2e.py` | 15 | Full HTTP flow: POST /analyze → poll /progress → GET /jobs |
| `scoring.test.ts` | 25 | Frontend scoring utilities + `countFailedProposals` |
| **Total** | **134** | **All offline — no API keys needed** |

---

## What's Next (prioritized)

| # | Task | Blocking anything? |
|---|------|--------------------|
| 1 | ~~**Replace SSE with pure polling** (day12)~~ | Done — `/jobs/{job_id}/progress` endpoint + frontend polls every 2s; SSE removed |
| 2 | ~~Show "scoring failed" state on partial proposal cards~~ | Done — Alert shown on card when `scores === null`; displays `proposal.error` if present |
| 3 | ~~Surface `status: "partial"` at the top level~~ | Done — yellow banner above results showing how many of N vendors failed |
| 4 | ~~Verify frontend handles 0–10 scores correctly~~ | Done |
| 5 | Vercel + Terraform integration | After polling fix lands |
| 6 | Production Postgres (AWS RDS) for persistence | Required for Terraform deploy |
| 7 | DB migration: `rfp_name` column on production DB | Before first production run |

---

## Known Issues / Improvement Backlog

Items noticed but not yet acted on. Each needs a failing test before any fix.

| Priority | Item | Confidence |
|----------|------|-----------|
| LOW | `test_pipeline.py` is a manual script, not picked up by pytest | HIGH |
| LOW | `_jobs` TTL timer is daemon — won't fire if process exits abnormally | HIGH |
| LOW | `analysis_runs` table has no index on `created_at` — slow for range queries at scale | MEDIUM |
| LOW | `warm_caches_node` warms all 3 agents even if only 1 vendor is being processed | LOW |

---

## Daily Audit Log

### 2026-06-07 — End-to-end tests (offline, no API key)
- `test_e2e.py` added: 15 tests covering POST /analyze → poll /progress → GET /jobs full flow
- Mocking strategy: `_run_pipeline` stubbed with instant result; `_persist_run` patched to no-op
- Red/green confirmed: without mock, real pipeline stays pending for 2s+ (timeout); with mock, instant
- Core suite: 109 passing

### 2026-06-07 — Doc cleanup + live/mock test separation
- `tests/live/` created — 5 live-key test files moved there, excluded via `pytest.ini norecursedirs`
- `pytest tests/` now runs only 94 offline tests, zero failures
- COMMANDS.md rewritten: correct test count, live test paths, updated endpoint table, sg docker throughout
- RESTART.md deleted (fully subsumed by COMMANDS.md); CLAUDE.md updated to reference COMMANDS.md
- DECISIONS.md: SSE/polling section updated to reflect day12 pure-polling approach
- project_overview.md: tech stack corrected (removed Gemini, LangSmith, Railway; added App Runner, FastEmbed, Mantine)
- todo.md + debugging_notes.md deleted (historical notes, no operational value)
- preflight.sh: test count 77→94, simplified to `pytest tests/`
- CLAUDE.md: live API call ban + minimal test file rule added

### 2026-06-07 — SSE replaced with pure polling (day12)
- Added `GET /jobs/{job_id}/progress` endpoint — returns current stage, vendors, total_risks, and result when done
- Frontend EventSource removed; replaced with `setInterval` polling every 2s against `/progress`
- 7 new P11 tests for the progress endpoint (all offline, no API keys needed)
- Core test count: 94 passing
- CLAUDE.md updated: live API call ban + minimal test file rule added
- Frontend build: clean (TypeScript passes)

### 2026-06-07 — Production deployment + SSE stabilisation
- SSE compact JSON fix deployed (separators=(',',':'))
- Agent logging added (extraction chunk count, risk flag count, scoring dim_scores + overall)
- Frontend `/100` suffix bug fixed → `/10` in KPI bar
- SSE polling fallback implemented: when onerror fires, frontend polls /jobs/{job_id} every 5s
- SSE error handler fixed: guards added for connection-level closes (no `.data`) and post-done race
- Root cause analysis: day10 onerror had zero recovery; explained all three reported failure modes
- App Runner 120s hard timeout confirmed — cannot be changed. SSE is a workaround; polling is the fix (day12).
- AWS CLI installed at ~/.local/bin/aws. deploy_backend.sh script created.
- COMMANDS.md updated: live validation command, manual deploy trigger, sg docker note added.
- `ProposalResult.error` field added to frontend types.ts
- Branch day11 not yet merged to main — Vercel is watching main.


### 2026-06-07 — Partial result UX (day13)
- `countFailedProposals(proposals)` added to `scoring.ts` — counts proposals with `scores === null`
- 4 new tests in `scoring.test.ts` (red confirmed before implementation); total frontend tests: 25
- `ProposalCard`: shows a red Alert ("Scoring unavailable") when `scores === null`, surfaces `proposal.error` if present
- `page.tsx`: yellow "Partial results" banner shown when `result.status === "partial"`, reports N of M vendors failed
- TypeScript clean; all 25 frontend tests pass

<!-- The daily audit appends findings here. Most recent first. -->
<!-- Format: ### YYYY-MM-DD\n Findings or "No issues found." -->

### 2026-06-06 — Frontend scoring fix + test suite added
- Frontend updated to 0–10 scale (thresholds, labels, ring fill, bar width) in WinnerHero, ProposalCard, VendorComparisonTable
- Scoring display logic extracted to `frontend/lib/scoring.ts` (single source of truth)
- 21 Vitest tests added in `frontend/lib/scoring.test.ts` — written POST-implementation (fix preceded tests)
- CLAUDE.md updated: frontend numeric display logic now listed under "What Requires a Failing Test First"
- DECISIONS.md updated: full two-session history of the scoring scale bug documented

### 2026-06-06 — Initial STATUS.md created
Session summary: Day11 pipeline audit complete.
- 7 bugs fixed (parse_llm_json, memo type, scoring scale, score clamping, warm-up crash, error persistence, TTL eviction)
- Persistence layer added (Postgres, SQLAlchemy, 26 tests)
- Reliability hardening (pipeline lock, ingest dedup, 8 tests)
- COMMANDS.md created, CLAUDE.md written, preflight.sh created
- 87 tests passing

No issues found by audit. System is clean.

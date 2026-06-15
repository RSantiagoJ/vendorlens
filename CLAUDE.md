# VendorLens — Claude Code Instructions

Read STATUS.md first, then this file. STATUS.md tells you where the project is.
This file tells you how to work in it. Follow both exactly.

---

## Session Start Protocol

Do this before responding to anything the user asks:

1. **Read STATUS.md** — current state, settled decisions, open issues
2. **Read DECISIONS.md** — why things were built the way they were (prevents re-debating closed questions)
3. **Check COMMANDS.md** — production URLs, deploy commands, test commands (check here before asking about deployment config)
4. **Read `./memory/MEMORY.md`** — index of retained context from prior sessions (user profile, feedback, project state)
4. **Check tests** — if any tests are failing, fix them before touching what the user asked
5. **Check for drift** — does anything in this file contradict what you can see in the code?
   If yes: update this file to match reality, not the other way around

---

## Running Commands — Ricardo Runs, Claude Instructs

**Never use the Bash tool to run commands.** Instead, print the exact command for Ricardo to run.
This applies to all shell commands: tests, docker, git, curl, scripts — everything.
File edits (Read/Edit/Write tools) are fine to do directly.

---

## Environment

- **All Python runs inside Docker.** Never run `python3` or `pytest` on the host.
  ```
  docker compose run --rm backend <command>
  ```
- The `backend` service mounts `./backend` at `/app`. Edit files locally; run in container.
- Use `sg docker -c "docker compose ..."` if the shell lacks the docker group.

---

## Live API Calls — Banned Unless Explicitly Approved

**Never make live LLM or pipeline calls during a session** unless Ricardo explicitly asks for a live test.

- All tests must mock LLM calls (`unittest.mock.patch`, `conftest.py` autouse fixture handles construction).
- If a live smoke test is truly needed, use only the minimal vendor docs in `backend/data/vendor_proposals/test/` (`alpha_lms.txt`, `beta_lms.txt`). Never use the full LMS/ERP/Payroll corpus for live testing — it burns too many tokens.
- Live tests live in `tests/live/` and are excluded from `pytest tests/` via `norecursedirs` in `pytest.ini`. Do not run them during normal session work.
- The core suite (`test_boundaries.py`, `test_mock_pipeline.py`, `test_persistence.py`, `test_reliability.py`) must pass without any API keys. Run it with `pytest tests/`.

---

## Test-First Rule — Non-Negotiable

Before modifying any agent, pipeline node, state model, or utility:

1. Write the test. Run it. **Confirm it fails — for the right reason.**
2. Make the change.
3. Run the test. Confirm it passes.
4. Run the full suite. Confirm nothing else broke.

**A test that was never red proves nothing.** If you write a test and it passes immediately,
the test is wrong — it doesn't verify the behavior you think it does.

**Change surface minimization:** make the failing test pass with the minimum lines possible.
Every additional line changed is unverified. If you want to clean up nearby code — ask first.

**Scope boundary:** if asked to fix X, only touch files directly involved in X.
Do not rename, refactor, or clean up adjacent code. Out-of-scope changes need a separate ask.

---

## What Requires a Failing Test First

- Any agent (`extraction_agent`, `risk_agent`, `scoring_agent`, `memo_agent`)
- Any pipeline node or graph structure (`graph/pipeline.py`)
- Any state or data model (`graph/state.py`, `api/models.py`)
- Any shared utility (`tools/llm_factory.py`, `tools/chroma.py`)
- Any DB model or persistence function (`db/`, `api/main._persist_run`)
- Any frontend component that transforms or compares a numeric value for display
  (thresholds, labels, ring fills, progress bar widths, color tiers)
  → Extract logic to `frontend/lib/scoring.ts`. Run: `cd frontend && npm test`.

---

## Doc Sync — Required After Every Completed Change

After any change lands (tests green, feature working), immediately check and update:

| Doc | Update when |
|-----|-------------|
| `STATUS.md` | Any task completed, test count changes, new decisions made |
| `COMMANDS.md` | New endpoint, new test path, new script, changed command |
| `DECISIONS.md` | Architecture decision made or reversed |
| `project_overview.md` | Tech stack changes, deployment changes |
| `CLAUDE.md` | New rule learned, settled decision, something to avoid |

**This is not optional cleanup — it is part of completing the task.** A change is not done until the docs reflect it. Do not wait for a separate doc-cleanup session.

Do not update docs that are not affected by the change. One targeted update beats a broad sweep.

---

## The "What Breaks Without This?" Gate

Before making any change, answer: *what currently fails if I don't make this change?*

If the answer is "nothing fails — it's just cleaner/better/nicer":
- That is a refactor, not a fix
- It needs explicit user approval
- It needs its own failing test first
- Do not fold it into an unrelated fix

---

## Where Tests Live

| File | What it covers |
|------|---------------|
| `test_boundaries.py` | Data shape at every inter-layer handoff (B0–B7) |
| `test_mock_pipeline.py` | Full pipeline happy path + all failure modes |
| `test_persistence.py` | DB write, GET endpoint, error persistence, TTL, rfp_name |
| `test_reliability.py` | Concurrency, ingest dedup, output structure |

All tests must work **without API keys**. Stub LLM calls with `unittest.mock.patch`.
The `conftest.py` autouse fixture handles LLM construction mocking automatically.

Run the full suite before and after every change:
```
docker compose run --rm backend python -m pytest tests/ -q
```

---

## Session End Protocol

Before closing any session:

1. Run the full test suite — all must pass
2. If a significant decision was made this session — add it to DECISIONS.md
3. Update STATUS.md:
   - Mark completed items done
   - Add new settled decisions if any were made
   - Add new items to the improvement backlog if you noticed anything
   - Append a dated entry to the Daily Audit Log
4. If you explained something this session that a future Claude should already know — add it here
5. If a bug occurred that a rule could have prevented — add the prevention rule here, not just the fix
6. **Save memory** — update `./memory/` in the project root (committed to git, syncs across machines):
   - Update `project_current_state.md` with where things stand (what's done, what's next, any blockers)
   - Add a `feedback_*.md` for any new guidance Ricardo gave about how to work
   - Update `MEMORY.md` index if new files were added
   - Ricardo closes windows to get fresh context — this is how the next session picks up
7. Commit and push with a clear message

---

## Proactive Discovery — Ask These Periodically

Run these checks when relevant — not every session, but any time you have reason to:

**Architecture drift:**
- Does the pipeline diagram in STATUS.md still match `graph/pipeline.py`?
- Does the test count in STATUS.md match what pytest reports?
- Are there functions with no test coverage at all?

**Code health:**
- Is any function doing more than one thing?
- Are there any hardcoded values that should be named constants?
- Are there TODO/FIXME comments that should be tracked issues?

**Documentation drift:**
- Does README.md reflect what's actually required to run this?
- Are there env vars referenced in code that aren't in the README?
- Does COMMANDS.md cover every script in `scripts/`?
- Do the rules in this file reference files or functions that still exist?

**Test quality:**
- Were any tests in this session written after the implementation? (If yes — record in STATUS.md)
- Does `test_boundaries.py` cover every handoff in the current pipeline?
- Is there any code path only tested by the happy path?

---

## Settled Decisions — Do Not Re-Open

These have been evaluated and closed. Record them here when decisions are made.

| Decision | Reason closed |
|----------|--------------|
| Scoring scale: 0–10 (not 0–100) | Rubric states max 10.0. ×10 was a bug — `TestB7ScoringScale` guards it. |
| Drizzle ORM: not applicable | TypeScript-only ORM. Backend is Python. |
| Risk + scoring as separate nodes | Merging saves 3 LLM calls but adds complexity. Deferred. |
| Fan-out per vendor (parallel) | Settled architecture. Vendor isolation prevents failure cascade. |
| Claude + FastEmbed only | No Google API key needed. Switched in day8. |
| Per-stage specialization | Single mega-prompt produces worse structured output. |

---

## Do Not Suggest

These were proposed and rejected. Don't bring them up again.

- Drizzle ORM (TypeScript ORM, backend is Python)
- Rewriting agents with a single combined prompt
- GOOGLE_API_KEY (removed — no Google dependency)
- Merging risk+scoring into one node (valid but deferred)
- Multiplying overall score by 10 (was a bug, now fixed and tested)

---

## About Ricardo

- New to AI programming — frame new concepts using analogies to things already in the codebase.
- Prefers short, direct answers. No trailing summaries of what was just done.
- Responds well to honest tradeoff analysis. Will push back if something feels wrong.
- Test-first discipline is intentional — don't skip it, even for "obvious" fixes.
- Presentations matter — treat demo stability as a first-class concern.

---

## Pipeline Architecture

```
POST /analyze
  → ingest (deduplicated per filename)
  → warm_caches (3 calls, non-fatal on failure)
  → fan-out: vendor_subgraph × N (parallel)
      extract_node → risk_node → score_node
  → fan-in → memo_node
  → _persist_run (Postgres) + _schedule_eviction (10 min TTL)

GET /stream/{job_id}  SSE live progress
GET /jobs/{job_id}    persisted result
```

**Data contracts at each boundary:**

| From | To | Shape |
|------|----|-------|
| `extract_node` | `risk_node` | `{"extracted": ProposalData.model_dump()}` |
| `risk_node` | `score_node` | `{"risks": [RiskFlag.model_dump()]}` |
| `score_node` | `memo_node` | `{"proposals": [ProposalState.model_dump()]}` |
| `memo_node` | API | `memo: str` (never list) |

When changing a node's output shape — update `test_boundaries.py` first.

---

## Scoring Scale

Dimension scores: **0–10**. Overall: weighted sum, also **0–10**.
Do not multiply by 10. Do not normalize to 0–100.
`TestB7ScoringScale` will catch this regression.

---

## LLM Response Handling

`invoke_llm_cached` returns `str` normally but can return `list` (Anthropic content blocks).
- For JSON responses: always use `parse_llm_json` — it handles both
- For prose responses (memo): normalize manually before returning
  ```python
  if isinstance(result, list):
      result = "".join(part["text"] if isinstance(part, dict) else str(part) for part in result)
  ```

---

## Persistence Layer

`DATABASE_URL` → Postgres via `db/session.py`. Optional — API works without it.
Tables created on startup via `Base.metadata.create_all()`.
`_persist_run()` called on both success AND error paths.
`_schedule_eviction()` removes job from `_jobs` after 10 min TTL.

Schema change note: `create_all()` does not add columns to existing tables.
New columns require `ALTER TABLE` or a volume reset (`docker compose down -v`).

---

## Daily Audit Protocol (automated, read-only)

The daily audit runs on a schedule. It:
- Reads all files — never writes code
- Checks for documentation drift, missing tests, stale rules
- Appends findings to STATUS.md Daily Audit Log
- Commits only STATUS.md

**The audit never changes code.** Findings sit in STATUS.md until Ricardo approves them
in a user-initiated session, which then follows the test-first rule.

---

## When to Update This File

- A session reveals a gap that a rule could close → add the rule before closing
- A bug occurred that a rule could have prevented → add the prevention, not just the fix
- A decision is made and settled → add it to the Settled Decisions table
- Something was proposed and rejected → add it to Do Not Suggest

**CLAUDE.md compounds. It should be slightly more capable after every session.**
A CLAUDE.md that never changes learned nothing.

---

## Committing

Format: `type: short description` (fix, feat, refactor, test, docs, chore)
Body: what broke and why (for bugs), not just what changed.
Always run the full test suite before committing.

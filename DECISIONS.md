# VendorLens — Decision Log

Captures WHY decisions were made. The code shows WHAT. This shows WHY.
A future Claude session — or you in six months — cannot reconstruct this from git history.

Add an entry whenever a significant decision is made or a proposal is rejected.
Format: decision, why, what was considered and ruled out.

---

## Pipeline Architecture

### Fan-out per vendor, not stage-barrier
Each vendor runs all three stages (extract → risk → score) independently and in parallel.
The alternative — extract all vendors, then risk all, then score all — adds global sync points.
With fan-out, a slow vendor 1 doesn't delay vendor 2 starting risk analysis.
Failure isolation is also better: one vendor crashing doesn't block the others.

### Three specialized agents, not single-pass
We considered one LLM call per vendor that extracts, identifies risks, and scores simultaneously.
Quality was worse. A combined prompt is too broad — the model optimizes for none of the tasks well.
Focused system prompts with specific rubrics and policy context outperform a general "do everything" prompt.
Cost tradeoff: 3 calls vs 1, but cache hits on vendors 2+ bring the marginal cost down significantly.

### Risk failure is non-fatal
If risk analysis fails (policy file missing, API error), scoring proceeds with empty risks.
The alternative — fail the whole vendor on any stage error — was rejected because extraction data
is the most valuable output. Losing scores over a policy lookup failure would be wrong.
Risk errors are surfaced in the proposal's `error` field so the UI can show them.

### Risk + scoring kept as separate nodes
They share the same input (ProposalData) but merging them into one call was evaluated and deferred.
The key reason to keep them separate: non-fatal risk failure. If risk and scoring were one call,
a risk portion failure would take down scoring too. Separation preserves the resilience model.
Saves 3 LLM calls to merge — not worth the complexity at current scale.

---

## LLM Choices

### Haiku for scoring, Sonnet for everything else
Scoring is a mechanical numerical task: read the rubric, read the data, output 9 numbers.
It doesn't require Sonnet's reasoning quality. Haiku is 4x faster and ~5x cheaper.
Extraction, risk, and memo require nuanced prose and policy reasoning — Sonnet stays there.

### Prompt caching on all agents
System prompts (policy context, rubric, scoring criteria) are large and identical across vendors.
Anthropic's prompt caching reduces cost ~90% on the cached portion after the first call.
The warm_caches_node pre-warms the cache before fan-out so vendor 1 also gets cache hits.
Without warm-up, vendor 1 pays full price; vendors 2+ get cache hits naturally.

### Distillation funnel — each stage sends less to the next
Raw doc → ProposalData JSON → RiskFlags list → ScoreCard numbers → Memo (scores + HIGH risks only).
Each downstream agent sees a progressively smaller and more structured input.
Memo agent never sees the raw document — it only needs scores and high-severity flags.
This minimizes token costs at every stage and keeps each agent focused on its actual task.

---

## Embeddings and RAG

### FastEmbed locally, not Google or OpenAI embeddings
We started with Google embeddings (GoogleGenAIEmbedding). Switched to FastEmbed + BAAI/bge-small-en-v1.5.
Reason: eliminate the Google API dependency. FastEmbed runs on ONNX locally — no API key, no cost, no latency.
Quality is sufficient for our document sizes and retrieval patterns.

### Three parallel RAG queries per vendor, not full-document pass
ExtractionAgent runs 3 targeted queries in parallel, covering all 30 ProposalData fields in groups.
Alternative: pass the full document text directly to the LLM.
For our small demo documents this would work, but real vendor proposals are 40–100 pages.
RAG scales; full-document pass does not. We kept RAG to preserve production-readiness.

---

## Data and Types

### Pydantic v2 for all state models
Every boundary in the pipeline is enforced by a Pydantic model.
LLM JSON → `parse_llm_json` → `ProposalData.model_validate()` — strict validation at the entry point.
This catches LLM schema violations (wrong field type, missing required field) early
rather than propagating bad data silently through the pipeline.
`test_boundaries.py` exists specifically to prove these contracts hold.

### Scoring scale 0–10 (not 0–100)
The rubric injected into the LLM's system prompt explicitly states: "Maximum possible overall score is 10.0."
The LLM scores each dimension 0–10. `_compute_overall` is a simple weighted sum — no multiplier.

**How the bug actually happened — two sessions, one broken contract:**
- bc72a29 (June 4): a Claude session added `* 10` to `_compute_overall` AND simultaneously updated
  the frontend to match: `>= 70/40` thresholds, `/ 100` labels, ring offset `/ 100`. Backend and
  frontend were deliberately in sync at 0–100. The commit message documented this explicitly.
- d5f51d4 (day11): the `* 10` was removed because the rubric says max 10.0, backend tests were
  written, but the frontend was never touched. One end of a coordinated contract was changed
  without updating the other.
- Fixed in day11 session 2: all four frontend spots updated to 0–10 scale.

**Rule this adds:** When you change a numeric scale at the backend (multiplier, normalization),
search the frontend immediately for every place that value is displayed or compared.
The commit message may tell you this was a coordinated change — read it before removing anything.

---

## Persistence

### In-memory SSE + Postgres persistence (not SSE from DB)
SSE streaming uses an in-memory `_jobs` dict for speed — appending events is microsecond-fast.
Results are persisted to Postgres only on completion (success or error).
`GET /jobs/{job_id}` checks memory first, then DB — so page refreshes after streaming also work.
Alternative (stream from DB via polling) would add DB reads to every SSE tick — unnecessary overhead.

### Jobs evicted from memory after 10 minutes
`_jobs` used to grow forever. After persistence, we can safely evict completed jobs.
10 minutes is enough time for any client to finish consuming the SSE stream and fetch the result.
Eviction is via a daemon `threading.Timer` — fires and forgets, doesn't block shutdown.

---

## What Was Proposed and Rejected

| Proposal | Rejected Because |
|----------|-----------------|
| Drizzle ORM | TypeScript-only ORM. Backend is Python. |
| Single mega-prompt per vendor | Quality worse than three specialized agents. |
| Merging risk + scoring | Breaks non-fatal risk failure model. Deferred. |
| Stage-barrier pattern (all extract → all risk → all score) | Adds global sync points. Fan-out is faster and more resilient. |
| Google API for embeddings | External dependency removed. FastEmbed is sufficient locally. |
| Scoring scale 0–100 | Rubric states max 10.0. The ×10 multiplier was a bug. |
| Scheduled remote audit | Costs credits. Static Python script on SessionStart hook is free. |

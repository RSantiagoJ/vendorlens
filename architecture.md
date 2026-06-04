# Architecture

## Background

VendorLens is a multi-agent AI system built by Ricardo Santiago at UMPO.
Ricardo is an experienced full-stack developer building his first agentic
AI application. The architecture is intentionally straightforward — one
pipeline, four agents, clear handoffs — buildable in a sprint while
demonstrating production-grade patterns.

The agents are grounded in real UMPO policy. See context/ folder (local
only, not in repo) for the policy notes and LMS RFP criteria that inform
agent prompts. If context/ is not present, refer to agent_prompts.md
which contains the distilled rules.

If you see improvements that don't blow up the timeline, flag them.

---

## Project structure

vendorlens/
docker-compose.yml         <- backend + api services
backend/
agents/
extraction_agent.py
risk_agent.py
scoring_agent.py
memo_agent.py
api/
main.py
models.py
data/
vendor_proposals/          <- proposal text files, organized by bundle
lms/                   <- blackboard.txt, canvas.txt, brightspace.txt
payroll/               <- adp.txt, ceridian.txt, paylocity.txt
erp/                   <- workday.txt, oracle_cloud.txt, unit4.txt
chroma_db/             <- auto-created by scripts/ingest.py
context_bundles/           <- swappable per-RFP context (no code changes)
lms/
policy.txt
rfp_criteria_lms.txt
scoring_rubric_lms.txt
payroll/
policy.txt
rfp_criteria_payroll.txt
scoring_rubric_payroll.txt
erp/
policy.txt
rfp_criteria_erp.txt
scoring_rubric_erp.txt
graph/
pipeline.py            <- LangGraph graph + PipelineState
state.py               <- ProposalData, RiskFlag, ScoreCard, ProposalState, VendorLensState
tools/
context_loader.py      <- BUNDLES registry, load_context_bundle(), get_policy_path()
llm_factory.py         <- make_llm(), make_claude_llm(), load_prompt(), parse_llm_json()
mcp_server.py          <- make_policy_lookup() keyword search tool
scripts/
ingest.py              <- ChromaDB ingestion (run once, or --force to rebuild)
tests/
test_agents.py
test_extraction.py
test_pipeline.py
test_rag.py
prompts.yaml           <- all agent system prompts
.env                   <- API keys, never commit
requirements.txt
frontend/              <- Next.js 15 + TypeScript + Mantine UI
app/
page.tsx           <- main page, SSE wiring, state machine
layout.tsx
globals.css
components/
AgentProgressBar.tsx
MemoPanel.tsx
ProposalCard.tsx
ThinkingLog.tsx
UploadZone.tsx
lib/
fixtures.ts        <- DEMO_RESULT for /?demo mode
types.ts           <- mirrors backend Pydantic models exactly
theme.ts           <- Mantine custom color palette
logo/

---

## Request lifecycle

1. User uploads PDFs via Next.js frontend
2. Frontend POSTs files to FastAPI /analyze endpoint
3. FastAPI saves files temporarily, invokes LangGraph pipeline
4. LangGraph runs four agents sequentially, passing shared state
5. Each agent retrieves relevant chunks via LlamaIndex before LLM call
6. Final state returned as JSON (proposals + risks + scores + memo)
7. FastAPI streams progress via Server-Sent Events
8. Next.js renders comparison cards and memo
9. User downloads memo as .md file

---

## LangGraph state

Two state types live in `graph/state.py`:

**PipelineState** (TypedDict — used by the LangGraph graph):
```
pending:     list[dict]          # raw {filename, raw_text} — input only
extracted:   Annotated[list, operator.add]   # fan-in from parallel extraction_nodes
with_risks:  Annotated[list, operator.add]   # fan-in from parallel risk_nodes
proposals:   Annotated[list, operator.add]   # fan-in from parallel scoring_nodes
memo:        str | None
status:      str                 # last-write-wins reducer
error:       str | None          # last-write-wins reducer
```

**VendorLensState** (Pydantic BaseModel — used in tests and response construction):
```
proposals: list[ProposalState]
memo: str | None
status: "pending"|"extracting"|"risk"|"scoring"|"memo"|"done"|"error"
error: str | None
```

Graph topology (all three agent stages run in parallel via Send()):
```
START → fan_out_extraction → extraction_node (×N, parallel)
      → fan_out_risk       → risk_node       (×N, parallel)
      → fan_out_scoring    → scoring_node    (×N, parallel)
      → memo_node          → END
```

Error handling: each node catches exceptions and returns `{"error": str(e)}`; last write wins on the `error` field.

---

## Agents

### Agent 1: Extraction Agent

File: agents/extraction_agent.py
Model: Gemini 3.5 Flash (primary) / Claude Sonnet 4.6 (fallback)
Input: vendor filename — runs 3 parallel RAG queries via LlamaIndex, top_k=8
Output: ProposalData (see state.py)
Note: Extract only what is stated. Null means not found, not hallucinated.

### Agent 2: Risk Agent

File: agents/risk_agent.py
Model: Gemini 3.5 Flash (primary) / Claude Sonnet 4.6 (fallback)
Input: ProposalData
Output: list[RiskFlag]
Tool: make_policy_lookup() from tools/mcp_server.py — keyword-scored search against bundle policy.txt
Policy context: built once at RiskAgent.__init__ time (5 queries, deduplicated), reused across all proposals

### Agent 3: Scoring Agent

File: agents/scoring_agent.py
Model: Gemini 3.5 Flash (primary) / Claude Sonnet 4.6 (fallback)
Input: ProposalData + list[RiskFlag]
Output: ScoreCard with 9 dimension scores (0–10) + weighted overall
Weights: parsed from rfp_criteria_<bundle>.txt at init time — not hardcoded
Overall: computed in Python as weighted average, not by the LLM

### Agent 4: Memo Writer Agent

File: agents/memo_agent.py
Model: Claude Sonnet 4.6 (always — prose quality matters here)
Input: all ProposalState objects with extracted, risks, scores populated
Output: Markdown recommendation memo (only HIGH risks passed to save tokens)

---

## RAG setup

Library: LlamaIndex
Vector store: ChromaDB (local, persisted to data/chroma_db/)
Embedding: Google `models/gemini-embedding-001`
Ingestion: `scripts/ingest.py` — SimpleDirectoryReader on `data/vendor_proposals/` (recursive),
  file_metadata override stores bare filename so ChromaDB filters still work
Chunking: SentenceSplitter chunk_size=512 overlap=50
Retrieval: Filter by `file_name` metadata, top_k=8, 3 parallel queries per proposal (deduplicated)

---

## Policy lookup tool

File: tools/mcp_server.py
Function: `make_policy_lookup(policy_path: Path) -> Callable[[str], str]`

Returns a closure that performs keyword-scored search against the given policy.txt.
Used by RiskAgent at init time — not an MCP server in the traditional sense, but
retains the mcp_server.py filename for continuity.

Query returns the top matching policy sections as a newline-separated string.
RiskAgent runs 5 targeted queries covering: security certs, data/DPA, liability/jurisdiction,
auto-renewal, and IP/incident response.

---

## API

Framework: FastAPI
Dev server: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` (inside Docker)

Endpoints:
POST /analyze       — multipart upload (files + bundle form field), enqueues job, returns {job_id}
GET  /stream/{id}   — SSE stream; replays buffered events then polls until done/error
                      Events: extracting | risk | scoring | memo | done | error
GET  /bundles       — returns list of registered bundle descriptors (id, label, description)
GET  /health        — {"status":"ok"}
POST /reload        — clears pipeline cache; call after re-running ingest.py without restarting

Pipeline cache: one compiled LangGraph pipeline per bundle_id, built on first use and cached
in-process. All requests to the same bundle share the cached pipeline.
CORS: localhost:3000

---

## Frontend

Framework: Next.js 15 + TypeScript + Mantine UI
Ricardo is expert in this stack. Claude Code defers to his judgment on UI.

Components:
- UploadZone — drag-and-drop or click-to-browse; SegmentedControl bundle selector; deduplicates files
- AgentProgressBar — SSE-driven; four labeled stages (Extracting → Risk → Scoring → Memo);
  spinner on active stage, checkmark + description when done
- ThinkingLog — simulated live activity log; per-stage lines emit on a 2s interval; auto-scrolls
- ProposalCard — overall score bar, 9-dimension breakdown bars, risk flag chips with hover tooltips
  (explanation + recommendation), collapsible contract details
- MemoPanel — markdown rendered via react-markdown
- Demo mode: `/?demo` loads DEMO_RESULT from lib/fixtures.ts — no backend needed

Display:
- Vendor cards sorted highest → lowest score, left to right
- "Best Choice" banner shown on the top-scoring card (suppressed when only one vendor)
- Score colors: green ≥ 7, amber 4–6.9, red < 4 (applied to bars, text, and badge outline)
- Risk tag colors: HIGH=red (filled), MEDIUM=amber (light), LOW=gray (light)
- Custom Mantine theme: ummaroon, umblue, umgreen, umyellow color scales

---

## Environment variables (.env — never commit)

ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=vendorlens

---

## Observability

LangSmith: set the four LANGCHAIN\_ env vars. No other code changes needed.
Every LLM call, retrieval, tool use, and agent handoff is automatically traced.
Dashboard: smith.langchain.com
This is a strong demo talking point — every AI decision is auditable.

---

## Required enhancement: Dropbox document connector

Status: required for sprint. Implement on Day 7 if time permits.
Resume keyword: document pipeline integration / enterprise content ingestion

### What it does

Instead of uploading PDFs manually through the UI, authorized UMPO staff
drop vendor proposals into a designated Dropbox folder. VendorLens polls
the folder on demand (or on a schedule) and pulls new files automatically.

This is how the tool would work in real production at UMPO — staff already
use Dropbox, no new behavior required from them.

### Implementation

File: tools/dropbox_connector.py
Library: dropbox (pip install dropbox)
Auth: Dropbox OAuth2 app token stored in .env

DROPBOX_ACCESS_TOKEN=
DROPBOX_VENDOR_PROPOSALS_PATH=/VendorLens/Proposals

Key functions:
list_new_proposals() -> list[str]
Lists files in the Dropbox folder not yet processed

download_proposal(filename: str) -> bytes
Downloads a file and returns raw bytes for LlamaIndex ingestion

mark_processed(filename: str)
Moves file to /VendorLens/Processed/ after pipeline completes

### Integration point

In api/main.py, add a second endpoint alongside /analyze:

POST /analyze/dropbox
Calls list_new_proposals()
Downloads each file
Passes to existing LangGraph pipeline
Returns same JSON response as /analyze

The frontend adds a second button: "Analyze from Dropbox"
alongside the existing drag-and-drop upload zone.

### Why this matters for the resume

Most AI portfolio projects use hardcoded files or manual uploads.
A live document source connector shows the system is designed for
real-world use, not just demos. It demonstrates understanding of
enterprise data pipelines — a meaningful differentiator.

Additional .env keys needed:
DROPBOX_ACCESS_TOKEN=
DROPBOX_VENDOR_PROPOSALS_PATH=/VendorLens/Proposals

---

## Making VendorLens generic

VendorLens is designed so that the AI pipeline — agents, RAG, scoring,
risk flagging, and memo writing — contains no hardcoded knowledge about
any specific procurement. All domain knowledge lives in three files in
`data/context_bundle/`. Swapping those files is the only change required
to evaluate vendors for a completely different RFP.

### What is configurable (no code changes needed)

| File                                       | What it controls                                               |
| ------------------------------------------ | -------------------------------------------------------------- |
| `context_bundles/<id>/policy.txt`          | Risk thresholds, HIGH/MEDIUM/LOW triggers, legal requirements  |
| `context_bundles/<id>/rfp_criteria_*.txt`  | Scoring dimensions, weights, and what each dimension evaluates |
| `context_bundles/<id>/scoring_rubric_*.txt`| 0-10 scale descriptions per dimension                          |
| `prompts.yaml`                             | Agent personas, org name, RFP title, tone of the memo          |

To add a new bundle:

1. Create `data/context_bundles/<new_id>/` with the three files above.
2. Register it in `tools/context_loader.py` → `BUNDLES` dict.
3. Update `prompts.yaml` if agent tone or org name needs to change.
4. Re-run `scripts/ingest.py` to ingest any new vendor proposal docs.
5. No Python code changes to agents, pipeline, or API.

### What needs to change for a different extraction schema

The extraction agent uses a fixed JSON schema defined in `prompts.yaml`.
That schema is currently LMS-specific (fields like `lti_support`,
`sis_integration`, `gradebook_passback`). For a different domain:

- Replace the field list in the extraction prompt with domain-appropriate fields.
- Update `graph/state.py` ProposalData model to match.
- Update the Scoring Agent dimensions in `prompts.yaml` to match the new rubric.

This is a ~30-minute configuration change, not a rewrite.

### Example: retargeting for a cybersecurity services RFP

| File                                          | Change                                                                                          |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `context_bundles/cyber/policy.txt`            | Swap FERPA/GLBA risk rules for NIST CSF or FedRAMP requirements                                 |
| `context_bundles/cyber/rfp_criteria_cyber.txt`| Dimensions: incident response capability, pen test frequency, zero-trust posture, staff vetting |
| `context_bundles/cyber/scoring_rubric_cyber.txt` | 0-10 rubric for each cyber dimension                                                         |
| `prompts.yaml`                                | Change org name, RFP title, extraction fields to match cyber contract terms                     |

### The demo talking point

"This is running against our LMS RFP today. To run it against our
cybersecurity vendor RFP next month, we replace three text files and
update the prompt config. The pipeline, the agents, and all the AI
infrastructure stay exactly the same."

That is the architectural decision that makes this a platform, not a one-off tool.

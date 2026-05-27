# Architecture

## Background

VendorLens is a multi-agent AI system built by Ricardo Santiago at UMPO.
Ricardo is an experienced full-stack developer building his first agentic
AI application. The architecture is intentionally straightforward — one
pipeline, four agents, clear handoffs — buildable in a sprint while
demonstrating production-grade patterns.

The agents are grounded in real UMPO policy. See context/ folder (local
only, not in repo) for the policy notes and RFP criteria that inform
agent prompts. If context/ is not present, refer to agent_prompts.md
which contains the distilled rules.

If you see improvements that don't blow up the timeline, flag them.

---

## Project structure

vendorlens/
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
dummy_docs/ <- vendor proposal text files
chroma_db/ <- auto-created on first run
policy_doc.txt <- UMPO policy rules (from context notes)
graph/
pipeline.py <- LangGraph graph definition
state.py <- VendorLensState + Pydantic models
tools/
mcp_server.py <- MCP tool server
.env <- API keys, never commit
requirements.txt
frontend/ <- Next.js app
context/ <- LOCAL ONLY, in .gitignore
real_policy_notes.md
real_rfp_criteria.md
real_contract_terms.md
.gitignore
README.md

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

VendorLensState {
proposals: [
{
filename: str,
raw_text: str,
extracted: ProposalData | None,
risks: list[RiskFlag] | None,
scores: ScoreCard | None
}
],
memo: str | None,
status: "pending"|"extracting"|"risk"|"scoring"|"memo"|"done"|"error",
error: str | None
}

Nodes: extraction_node -> risk_node -> scoring_node -> memo_node -> END
Error handling: any failure sets status="error", short-circuits to END
Parallel execution: use LangGraph Send() if straightforward, else sequential

---

## Agents

### Agent 1: Extraction Agent

File: agents/extraction_agent.py
Model: Claude Sonnet 4.6
Input: PDF filename + LlamaIndex retriever
Output: ProposalData (see state.py)
Tool: MCP document_reader
Note: Extract only what is stated. Null means not found, not hallucinated.

### Agent 2: Risk Agent

File: agents/risk_agent.py
Model: Claude Sonnet 4.6
Input: ProposalData
Output: list[RiskFlag]
Tool: MCP policy_lookup (searches policy_doc.txt)
Grounded in: UMPO SVM-01 + UMass Contract for Services (see context/)

### Agent 3: Scoring Agent

File: agents/scoring_agent.py
Model: Gemini Pro (deliberate — demonstrates multi-model integration)
Input: ProposalData + list[RiskFlag]
Output: ScoreCard with scores 0-10 per dimension + weighted overall

### Agent 4: Memo Writer Agent

File: agents/memo_agent.py
Model: Claude Sonnet 4.6
Input: Full VendorLensState
Output: Markdown recommendation memo

---

## RAG setup

Library: LlamaIndex
Vector store: ChromaDB (local, persisted to data/chroma_db/)
Embedding: Google embedding model (Ricardo has Gemini access)
Ingestion: SimpleDirectoryReader on data/dummy_docs/ at startup if DB absent
Chunking: SentenceSplitter chunk_size=512 overlap=50
Retrieval: Filter by filename metadata, top_k=5

---

## MCP tools

File: tools/mcp_server.py
SDK: pip install mcp (official Anthropic MCP Python SDK)
Transport: stdio

Tools:
document_reader(filename: str) -> str
Returns full extracted text of a proposal document

policy_lookup(query: str) -> str
Semantic search against data/policy_doc.txt
Returns relevant policy rules matching the query

Note: If MCP SDK + LangGraph integration is complex, implement as standard
LangGraph tool nodes first and wrap in MCP. Document both in comments.

---

## API

Framework: FastAPI
Endpoints:
POST /analyze — multipart PDF upload, runs pipeline, returns JSON
GET /health — {"status":"ok"} for Railway health check
GET /stream/{job_id} — SSE progress updates (implement if time permits)
CORS: localhost:3000 + Railway URL

---

## Frontend

Framework: Next.js + TypeScript + Tailwind CSS
Ricardo is expert in this stack. Claude Code defers to his judgment on UI.

Components: UploadZone, ProgressBar (per agent stage), ProposalCard
(vendor name, overall score colored by range, dimension score bars,
risk tags by severity, expandable contract details), MemoPanel
(markdown rendered), DownloadButton (.md export)

Score colors: green >= 7, amber 4-6.9, red < 4
Risk tag colors: HIGH=red, MEDIUM=amber, LOW=gray

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

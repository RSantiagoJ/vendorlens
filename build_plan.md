# Sprint Build Plan

## How to start each Claude Code session

First session:
"Read all .md files in this folder and in context/ before we start.
I want to build VendorLens. I am Ricardo, the developer described in
project_overview.md. Let's start with Day 1."

Resuming mid-sprint:
"Read all .md files in this folder and in context/. We are on Day N.
Here is where we left off: [brief status]. Let's continue."

Ricardo is comfortable with Python and is expert in TypeScript/React/Next.js.
He is new to LangGraph, LlamaIndex, and agentic AI patterns.
Explain what you are building and why as you go.
If you see a better approach, suggest it and explain the tradeoff.
Do not silently deviate from the plan.

---

## Day 1 — Environment + RAG foundation

Goal: Python environment running, dummy docs loaded into ChromaDB,
semantic query working end to end.
This is the foundation everything else depends on.

Tasks:

1. Create full project structure per architecture.md

2. Create backend/requirements.txt:
   langchain langgraph langchain-anthropic langchain-google-genai
   llama-index llama-index-vector-stores-chroma
   llama-index-embeddings-google chromadb
   fastapi uvicorn python-multipart
   anthropic google-generativeai
   langsmith mcp pydantic python-dotenv pymupdf

3. Create backend/.env with all keys from architecture.md as placeholders
   Ricardo needs to create a LangSmith account at smith.langchain.com (free)

4. Write graph/state.py — all Pydantic models:
   ProposalData, RiskFlag, ScoreCard, ProposalState, VendorLensState

5. Copy dummy doc content from dummy_data.md into backend/data/dummy_docs/
   Create backend/data/context_bundle/ with three files:
   - policy.txt (UMPO SVM-01 + UMass Contract for Services rules)
   - rfp_criteria.txt (scoring dimensions and weights from the real RFP)
   - scoring_rubric_lms.txt (rubric descriptions per dimension, 0-10 scale)
     Content sourced from dummy_data.md and context/ folder notes.
     Agents read these files directly. No wrapper needed.

6. Write backend/ingest.py:
   - SimpleDirectoryReader on data/dummy_docs/
   - SentenceSplitter chunk_size=512 overlap=50
   - Google embeddings
   - Store in ChromaDB with filename as metadata

7. Write test_rag.py and confirm:
   - Query "renewal terms" filtered to vendor_b returns correct chunks
   - Query "liability cap" filtered to vendor_a returns correct value

Checkpoint: test_rag.py returns correct chunks from correct documents.
Do not move to Day 2 until this works.

---

## Day 2 — Extraction Agent + MCP tools

Goal: ExtractionAgent returns clean ProposalData for all three proposals.
MCP server running with document_reader and policy_lookup tools.

Tasks:

1. Write tools/mcp_server.py
   - document_reader tool: reads file, returns full text
   - policy_lookup tool: semantic search against policy.txt
   - Use official MCP Python SDK (pip install mcp), stdio transport
   - See architecture.md note on fallback approach if needed

2. Write agents/extraction_agent.py
   - Targeted retrieval queries per field
   - Claude Sonnet 4.6 with system prompt from agent_prompts.md
   - Parse response into ProposalData Pydantic model
   - Null for missing fields, never hallucinate

3. Write test_extraction.py — run against all three proposals
   Verify: Vendor B (Canvas) shows $2,280,000/year fixed, no auto-renewal, $5M liability
   Verify: Vendor A (Blackboard) shows escalating pricing, 30-day opt-out, $50,000 liability cap

Checkpoint: All three return valid ProposalData with no hallucinated fields.

---

## Day 3 — Risk Agent + Scoring Agent

Goal: Risk flags and scores populated for all three proposals.
Scoring Agent using Gemini Pro independently of Claude.

Risk Agent expected output:
Vendor A (Blackboard): multiple HIGH flags (30-day opt-out, SOC2 Type I only,
no DPA standard, data use violation, North Carolina governing law, low liability cap)
Vendor B (Canvas): zero HIGH flags
Vendor C (D2L Brightspace): one to two HIGH flags (Ontario/Delaware governing law)

Tasks:

1. [DONE] Write agents/risk_agent.py
   - Uses \_policy_lookup from tools/mcp_server.py (5 targeted queries, deduplicated)
   - Claude Sonnet 4.6 via LangChain
   - Returns list[RiskFlag] with policy_excerpt from LLM

2. [DONE] Write agents/scoring_agent.py
   - Gemini 3.5 Flash primary, Claude Sonnet 4.6 fallback
   - Load rubric via context_loader.load_context_bundle() — inject into prompt
   - Weights parsed from rfp_criteria_lms.txt at runtime — not hardcoded
   - overall computed in Python as weighted average (not relying on LLM math)
   - Returns ScoreCard

3. [DONE] Write test_agents.py — run both against all three proposals
       Verify: Vendor B scores highest overall, Vendor A scores lowest

Checkpoint: Risk flags and scores are directionally correct.
Gemini Pro scoring agent works independently.

--- SESSION NOTES (Day 3, complete) ---

All tasks complete. Checkpoint passed.

- graph/state.py: ScoreCard fields use generic names (platform_functionality, etc.)
- prompts.yaml: institution-specific text removed from all agent prompts; risk rules
  live in policy.txt only; scoring_agent no longer asked to compute overall (done in Python)
- tools/context_loader.py: loads all .txt files from context_bundle/ as dict
- tools/llm_factory.py: now also exports load_prompt() — single source for prompt loading
- agents/extraction_agent.py: top-level imports, no duplication
- agents/risk_agent.py: top-level imports, Gemini primary / Anthropic fallback
- agents/scoring_agent.py: top-level imports, weights parsed from rfp_criteria_lms.txt,
  overall computed in Python via _compute_overall(), ScoreCard built from dict comprehension
- test_agents.py: all 3 agents on all 3 vendors; B highest, A lowest, A has ≥3 HIGH flags

---

## Day 4 — Memo Agent + LangGraph pipeline ✅ COMPLETE

Goal: Full pipeline runs end to end. LangSmith trace visible.
This is the most important milestone in the project.

Tasks:

1. Write agents/memo_agent.py
   - Claude Sonnet 4.6 via make_claude_llm() from llm_factory
   - System prompt from prompts.yaml
   - Returns markdown memo recommending Vendor B (Canvas by Instructure)

2. Write graph/pipeline.py
   - LangGraph StateGraph with PipelineState
   - All three agent stages (extraction, risk, scoring) parallelized via Send()
   - Fan-out/fan-in pattern: each stage dispatches one node per vendor in parallel
   - memo_node runs sequentially after all scoring completes

3. Confirm LangSmith:
   - Run pipeline once
   - Verify run appears at smith.langchain.com

4. Write tests/test_pipeline.py
   - --count flag (default 2) to run subset of vendors for faster demos
   - Memo should recommend Vendor B (Canvas by Instructure)

--- SESSION NOTES (Day 4, complete) ---

All tasks complete. Checkpoint passed. Canvas recommended with score 10.0.

- graph/pipeline.py: all three stages parallel via Send(); PipelineState uses
  operator.add accumulators (extracted, with_risks, proposals)
- agents/memo_agent.py: uses make_claude_llm() — intentionally Claude for prose quality
- tools/llm_factory.py: added make_claude_llm(), dedup_ordered(), cached load_prompt()
- agents/risk_agent.py: policy context cached in __init__ (runs once, not per vendor)
- agents/extraction_agent.py: dedup_ordered() replaces manual seen+ordered loop
- data/context_bundle/rfp_criteria_lms.txt: weights corrected to sum to 1.00
  (pricing_and_licensing reduced 0.15 → 0.10); max score is now 10.0
- File structure reorganized: tests/ and scripts/ directories created;
  test files and ingest.py moved out of backend root
- tests/test_pipeline.py: --count flag defaults to 2 for faster presentation runs

---

## Day 5 — FastAPI backend

Goal: REST API wrapping the pipeline. Frontend can connect.

Tasks:

1. Write api/models.py — Pydantic response models for JSON serialization

2. Write api/main.py:
   POST /analyze — multipart upload, runs pipeline, returns JSON
   GET /health — {"status":"ok"}
   GET /stream/{job_id} — SSE progress updates (required, not optional)
   Emit events: extracting | risk | scoring | memo | done | error
   Each event carries the job_id and current status string
   CORS for localhost:3000

3. Test with curl:
   curl -X POST http://localhost:8000/analyze \
    -F "files=@vendor_a_blackboard.txt" \
    -F "files=@vendor_b_canvas.txt" \
    -F "files=@vendor_c_brightspace.txt"

Checkpoint: curl returns valid JSON with proposals, risks, scores, memo.

---

## Day 6 — Next.js frontend

Goal: Professional web UI ready for a boardroom demo.
Ricardo is the expert here — own this layer.

Tasks:

1. npx create-next-app frontend --typescript --tailwind

2. Build components per architecture.md:
   UploadZone, AgentProgressBar, ProposalCard, MemoPanel, DownloadButton

   AgentProgressBar connects to GET /stream/{job_id} via EventSource.
   Show four labeled stages that light up as SSE events arrive:
   Extracting → Risk Analysis → Scoring → Writing Memo
   Each stage shows a spinner while active, checkmark when done.

3. Wire to FastAPI with fetch() and FormData

4. Test full end-to-end in browser

Checkpoint: Upload 3 files, watch progress, see cards and memo, download works.

---

## Day 7 — Deploy + polish

Goal: Public URL on Railway. Demo-ready. Resume-ready.

Tasks:

1. Add error handling (frontend + backend + pipeline)

2. Write README.md:
   - What it does (2-3 sentences)
   - Screenshot or GIF
   - Tech stack with all keywords
   - How to run locally
   - Live demo URL

3. Deploy backend to Railway:
   Procfile: web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   railway login && railway init && railway up
   Set env vars in Railway dashboard

4. Deploy frontend to Vercel:
   vercel deploy
   Update API base URL to Railway backend URL

5. Add to resume and LinkedIn

Checkpoint: Public URL works. Paste it into resume. Sprint complete.

---

## Demo script (5 minutes)

"Right now, reviewing vendor proposals requires someone to read every
document, extract the key terms, compare them, check them against our
procurement policy, and write a summary memo. That takes hours.
Let me show you what that looks like with agentic AI."

[Upload three dummy proposal files. Hit analyze.]

"This is the LMS RFP your committee issued in November 2025. These are three
fictional proposals from real vendors. VendorLens is running four AI agents —
extracting structured data, flagging risks against our actual procurement policy,
scoring against our real RFP criteria, and writing the memo."

[Cards appear.]

"Three vendors, scored and compared. Vendor A has multiple high-severity
risk flags including a SOC 2 Type I certification, no standard Data Processing
Agreement, and North Carolina governing law — none of which meet our standards.
Vendor B scores highest across every dimension."

[Scroll to memo.]

"Here is the recommendation memo, ready to hand to a director."

[Switch to LangSmith.]

"Every decision the AI made is fully auditable here."

"And the policy, criteria, and rubric are all configurable — any procurement
team could drop in their own documents and run this against their RFP."

"This took 15 seconds. It would have taken a contracts analyst half a day."

---

## Day 7 optional: Dropbox connector

Prerequisite: Core sprint (Days 1-7) complete and deployed.
Time estimate: 2-3 hours if the pipeline is working cleanly.

Goal: Staff can drop PDFs into a Dropbox folder and trigger analysis
from the UI instead of uploading manually.

Tasks:

1. Create a Dropbox app at dropbox.com/developers
   - Set permissions: files.content.read, files.content.write
   - Generate an access token
   - Add to backend/.env

2. Write tools/dropbox_connector.py per architecture.md spec
   - list_new_proposals()
   - download_proposal()
   - mark_processed()

3. Add POST /analyze/dropbox endpoint to api/main.py
   - Calls connector, passes files to existing pipeline
   - Returns same response shape as /analyze

4. Add "Analyze from Dropbox" button to frontend
   - Calls /analyze/dropbox
   - Same progress bar and results rendering

5. Test end-to-end:
   - Drop a dummy proposal PDF into the Dropbox folder
   - Hit the button in the UI
   - Confirm pipeline runs and results render

6. Update README.md to mention Dropbox integration

7. Update resume bullet to include:
   "enterprise document pipeline integration via Dropbox API"

Checkpoint: Drop file into Dropbox, click button, see results.
No manual upload needed.

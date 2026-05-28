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
   - policy.txt         (UMPO SVM-01 + UMass Contract for Services rules)
   - rfp_criteria.txt   (scoring dimensions and weights from the real RFP)
   - scoring_rubric.txt (rubric descriptions per dimension, 0-10 scale)
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
   - policy_lookup tool: semantic search against policy_doc.txt
   - Use official MCP Python SDK (pip install mcp), stdio transport
   - See architecture.md note on fallback approach if needed

2. Write agents/extraction_agent.py
   - Targeted retrieval queries per field
   - Claude Sonnet 4.6 with system prompt from agent_prompts.md
   - Parse response into ProposalData Pydantic model
   - Null for missing fields, never hallucinate

3. Write test_extraction.py — run against all three proposals
   Verify: Vendor B shows $158,000 fixed price, no auto-renewal, $3M liability
   Verify: Vendor A shows $195,000, 30-day opt-out, $16,250 liability cap

Checkpoint: All three return valid ProposalData with no hallucinated fields.

---

## Day 3 — Risk Agent + Scoring Agent

Goal: Risk flags and scores populated for all three proposals.
Scoring Agent using Gemini Pro independently of Claude.

Risk Agent expected output:
Vendor A: multiple HIGH flags (30-day opt-out, SOC2 Type I only,
no DPA, data use violation, Texas governing law, IP transfer)
Vendor B: zero HIGH flags
Vendor C: one HIGH flag (Illinois governing law, data use for benchmarking)

Tasks:

1. Write agents/risk_agent.py
   - Uses policy_lookup MCP tool
   - Claude Sonnet 4.6 with system prompt from agent_prompts.md
   - Returns list[RiskFlag]

2. Write agents/scoring_agent.py
   - Gemini Pro
   - Load rubric via context_loader.load_context_bundle() — inject into prompt
   - Do not hardcode rubric weights in the prompt or agent file
   - Returns ScoreCard

3. Write test_agents.py — run both against all three proposals
   Verify: Vendor B scores highest overall, Vendor A scores lowest

Checkpoint: Risk flags and scores are directionally correct.
Gemini Pro scoring agent works independently.

---

## Day 4 — Memo Agent + LangGraph pipeline

Goal: Full pipeline runs end to end. LangSmith trace visible.
This is the most important milestone in the project.

Tasks:

1. Write agents/memo_agent.py
   - Claude Sonnet 4.6
   - System prompt from agent_prompts.md
   - Returns markdown memo recommending Vendor B (SocialBridge)

2. Write graph/pipeline.py
   - LangGraph StateGraph with VendorLensState
   - Nodes: extraction_node, risk_node, scoring_node, memo_node
   - Sequential edges with error handling
   - Parallel execution via Send() if straightforward

3. Confirm LangSmith:
   - Run pipeline once
   - Verify run appears at smith.langchain.com
   - Every agent call and retrieval should be visible

4. Write test_pipeline.py
   - Run full pipeline against all three dummy proposals
   - Memo should recommend Vendor B (SocialBridge Solutions)

Checkpoint: graph.run() returns complete state with memo.
Full trace visible in LangSmith.

---

## Day 5 — FastAPI backend

Goal: REST API wrapping the pipeline. Frontend can connect.

Tasks:

1. Write api/models.py — Pydantic response models for JSON serialization

2. Write api/main.py:
   POST /analyze — multipart upload, runs pipeline, returns JSON
   GET /health — {"status":"ok"}
   GET /stream/{job_id} — SSE progress (implement if time permits)
   CORS for localhost:3000

3. Test with curl:
   curl -X POST http://localhost:8000/analyze \
    -F "files=@vendor_a_pulsemedia.txt" \
    -F "files=@vendor_b_socialbridge.txt" \
    -F "files=@vendor_c_campusvoice.txt"

Checkpoint: curl returns valid JSON with proposals, risks, scores, memo.

---

## Day 6 — Next.js frontend

Goal: Professional web UI ready for a boardroom demo.
Ricardo is the expert here — own this layer.

Tasks:

1. npx create-next-app frontend --typescript --tailwind

2. Build components per architecture.md:
   UploadZone, ProgressBar, ProposalCard, MemoPanel, DownloadButton

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

"This is the RFP your committee issued in November 2025. These are three
fictional vendor responses. VendorLens is running four AI agents — extracting
structured data, flagging risks against our actual SVM-01 policy, scoring
against our real RFP criteria, and writing the memo."

[Cards appear.]

"Three vendors, scored and compared. Vendor A has multiple high-severity
risk flags including a SOC 2 Type I certification, no Data Processing
Agreement, and Texas governing law — none of which meet our standards.
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

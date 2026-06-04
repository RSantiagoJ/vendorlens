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
  overall computed in Python via \_compute_overall(), ScoreCard built from dict comprehension
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
- agents/risk_agent.py: policy context cached in **init** (runs once, not per vendor)
- agents/extraction_agent.py: dedup_ordered() replaces manual seen+ordered loop
- data/context_bundle/rfp_criteria_lms.txt: weights corrected to sum to 1.00
  (pricing_and_licensing reduced 0.15 → 0.10); max score is now 10.0
- File structure reorganized: tests/ and scripts/ directories created;
  test files and ingest.py moved out of backend root
- tests/test_pipeline.py: --count flag defaults to 2 for faster presentation runs

---

## Day 5 — FastAPI backend ✅ COMPLETE

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

3. Start the server (all Python runs inside Docker):
   docker compose run --service-ports backend \
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

4. Test with curl:

   # POST returns job_id immediately

   curl -X POST http://localhost:8000/analyze \
    -F "files=@data/dummy_docs/vendor_a_blackboard.txt" \
    -F "files=@data/dummy_docs/vendor_b_canvas.txt" \
    -F "files=@data/dummy_docs/vendor_c_brightspace.txt"

   # Stream progress + final result (paste job_id from above)

   curl -N http://localhost:8000/stream/{job_id}

Checkpoint: SSE stream ends with a "done" event containing proposals, risks, scores, memo.

Note: All Python commands use docker compose — never run python3 directly on the host.
Docker requires sudo on this machine:
sudo docker compose run backend python3 -m pytest ← for tests
sudo docker compose exec backend bash ← interactive shell

--- SESSION NOTES (Day 5, complete) ---

All tasks complete. Checkpoint passed via scripts/test_api.sh.

- api/models.py: AnalyzeResponse, ProposalResult, AnalysisResult — thin wrappers reusing graph/state types
- api/main.py: pipeline singleton initialized on first request; pipeline runs in ThreadPoolExecutor
  via loop.run_in_executor so the event loop stays unblocked; SSE uses plain StreamingResponse
  (no sse-starlette dependency); stream() with stream_mode="updates" drives progress events
- POST /analyze returns job_id immediately; GET /stream/{job_id} replays all buffered events
  then live-polls until done/error — handles clients that connect after job starts
- scripts/test_api.sh: starts server in Docker, health check, POST, SSE stream; no jq or python needed

Ready for Day 6.

---

## Day 6 — Next.js frontend ✅ COMPLETE

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

--- SESSION NOTES (Day 6, complete) ---

All tasks complete. Checkpoint passed.

- frontend/ bootstrapped with Next.js 15 + TypeScript + Mantine UI (replaced Tailwind — better component library for this UI surface)
- Components built: UploadZone, AgentProgressBar, ProposalCard, MemoPanel, ThinkingLog
- AgentProgressBar: four labeled stages driven by SSE events; spinner on active stage, checkmark when done
- ThinkingLog: simulated live activity feed showing per-stage work lines on a timed interval
- ProposalCard: overall score bar, 9-dimension breakdown bars, risk flag chips with hover tooltips, collapsible contract details
- Demo mode: /?demo loads DEMO_RESULT fixture from lib/fixtures.ts — no backend needed for boardroom demos
- Bundle selector: SegmentedControl in UploadZone populated from GET /bundles; falls back to hardcoded defaults if backend unreachable
- Vendor cards sorted highest → lowest score left to right; winner gets green border + "Best Choice" banner (hidden when only one vendor)
- lib/types.ts mirrors backend Pydantic models exactly

---

## Day 7 — UI Polish + Intelligence Enhancements ✅ COMPLETE

Goal: Elevate the demo experience with richer visualizations, live-feed intelligence,
and a polished results presentation ahead of the innovation sprint.
(Terraform deferred to Day 8 where it pairs with a new agent for maximum impact.)

Tasks completed:

1. Radar chart — multi-dimensional score visualization, all vendors overlaid
2. Score animations — bars animate in on load
3. PDF export — one-click export of vendor cards + memo
4. Confetti — winner celebration burst when Best Choice banner appears
5. Typewriter effect — completion summaries in the live feed stream character-by-character
6. Elapsed timers — each stage shows live wall-clock time
7. Richer completion summaries — per-stage outcome lines with counts (e.g., "Found 6 risk flags")
8. Real vendor names in activity log — uses actual company names throughout
9. Risk flag counts in activity log — HIGH/MEDIUM/LOW counts surfaced in live feed
10. Head-to-head vendor comparison table — dimension-by-dimension structured table below cards
11. Google API key rotation — cycles through fallback keys before failing on rate limit

Dropbox connector abandoned entirely. All Day 7 work was UI/intelligence enhancements.
Key files: ProposalCard.tsx (radar chart, animations, PDF), ThinkingLog.tsx
(typewriter, timers, summaries), VendorComparisonTable.tsx (new component).

---

## Day 8 — Negotiation Playbook Agent + Terraform Deploy 🎯

### The story for leadership

> "VendorLens doesn't just tell you who won. It tells you how to negotiate
> with them — using the other vendors' scores as leverage."

Four agents already run: extract → risk → score → memo.
Day 8 adds a fifth: the **Negotiation Playbook Agent**.

After scoring completes, a new agent reads all vendor scorecards and generates:
- Which dimensions are weaknesses for the recommended vendor (negotiation targets)
- Where competing vendors score higher (pressure points to cite in the vendor call)
- Specific contract asks: DPA language, liability cap adjustments, pricing flexibility
- A concise "walk-in brief" the procurement director reads before the vendor call

This is the innovation sprint "wow" moment: the system goes from analysis to action.
Terraform provisions a live AWS URL so the demo runs on real production infrastructure.

AWS account: personal account — no work access dependencies.
All resources provisioned under Ricardo's own account with full admin control.

---

### Part 1 — Negotiation Playbook Agent (the new AI capability)

**New files:**
- `backend/agents/negotiation_agent.py` — 5th agent using Claude Sonnet 4.6
  - Receives all scored proposals (same input shape as memo_agent)
  - System prompt: analyze competitive gaps, identify leverage, generate tactical brief
  - Returns `NegotiationBrief`: `{ recommended_vendor, leverage_points: [], key_asks: [], walk_in_summary }`
- `backend/graph/state.py` — add `NegotiationBrief` Pydantic model; add field to `ProposalState`
- `backend/graph/pipeline.py` — add `negotiation_node` after memo_node (sequential, same pattern)
- `backend/api/main.py` — emit `negotiating` SSE event; include `negotiation` in done payload
- `frontend/lib/types.ts` — add `NegotiationBrief` type mirroring backend model
- `frontend/components/NegotiationPanel.tsx` — new component, same card style as MemoPanel
  - Leverage points as a bulleted list with vendor name callouts
  - Key asks as a visual checklist
  - Walk-in summary in a highlighted blockquote
- `frontend/app/page.tsx` — render NegotiationPanel below MemoPanel when data arrives

**Agent prompt guidance (add to `prompts.yaml`):**
```
You are a procurement strategist advising a university negotiating team.
You have scored multiple vendor proposals. Your job:
1. Identify 3-5 dimensions where the recommended vendor scored below 8.
   For each, note if a competitor scored higher — that is negotiation leverage.
2. List 3-5 specific contract asks that address the identified gaps.
3. Write a 2-sentence walk-in summary the director reads before the vendor call.
Return JSON only. No preamble.
```

**Checkpoint:** After analysis, a "Negotiation Playbook" panel appears below the memo
with leverage points, key asks, and walk-in summary for the winning vendor.

---

### Part 2 — Terraform: infrastructure as code (deploy + learn)

Goal: provision the full AWS stack in one command; get a live URL for the demo.
Secondary goal: understand Terraform core concepts hands-on.

**Prerequisites:**
- Log in at aws.amazon.com with personal account (full admin, no work dependency)
- `aws configure` with personal account access keys
- `terraform` CLI installed locally (`brew install terraform` or tfenv)

**Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**terraform/ directory:**
```
terraform/
  main.tf        — AWS provider; S3 remote state backend
  variables.tf   — region, app_name, environment
  outputs.tf     — app_runner_url (the live demo URL)
  ecr.tf         — ECR repository for the backend Docker image
  s3.tf          — upload bucket (replaces /tmp in the API)
  ssm.tf         — SSM Parameter Store: ANTHROPIC_API_KEY, GOOGLE_API_KEY, LANGCHAIN_API_KEY
  iam.tf         — App Runner task role with SSM read permission
  apprunner.tf   — App Runner service: pulls from ECR, reads secrets from SSM, auto-scales to zero
```

**Deploy sequence:**
```bash
# 1. Build and push image to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_URI>
docker build -t vendorlens-backend backend/
docker tag vendorlens-backend:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# 2. Provision all infrastructure
cd terraform && terraform init
terraform plan -out=tfplan
terraform apply tfplan

# 3. Print the live URL
terraform output app_runner_url
```

**One backend change for S3 uploads:**
`api/main.py`: if `S3_BUCKET` env var is set, write uploaded files to S3 instead of `/tmp`.
Graceful fallback to `/tmp` when running locally — no Docker config changes for local dev.

**Frontend deploy:**
```bash
echo "NEXT_PUBLIC_API_URL=$(terraform output -raw app_runner_url)" > frontend/.env.production
cd frontend && vercel deploy --prod
```

**Cost estimate (personal account):**
- App Runner scales to zero at idle — ~$0.005/request when not running
- Active analysis runs: ~$0.064/vCPU-hour
- S3 + SSM: negligible at demo volume
- Realistic monthly total: $3–10 for occasional demo use
- `terraform destroy` after the presentation tears everything down to $0

**Terraform concepts touched hands-on:**

| Concept         | Where it appears                                                               |
| --------------- | ------------------------------------------------------------------------------ |
| Provider config | `aws` provider block in `main.tf`                                              |
| Remote state    | S3 backend in `main.tf` — keeps `.tfstate` out of git                         |
| Resources       | `aws_ecr_repository`, `aws_s3_bucket`, `aws_ssm_parameter`,                   |
|                 | `aws_apprunner_service`, `aws_iam_role`, `aws_iam_role_policy`                 |
| Data sources    | `aws_iam_policy_document` for generating trust + permission policies           |
| Variables       | `variables.tf` — region, app_name, environment; passed via `terraform.tfvars` |
| Outputs         | `outputs.tf` — `app_runner_url` printed after apply; consumed by frontend      |

Commands:
```
terraform init     — download AWS provider, initialize S3 backend
terraform plan     — preview what will be created/changed/destroyed
terraform apply    — provision infrastructure
terraform output   — print app_runner_url after apply
terraform destroy  — tear everything down (cost control after demo)
```

**Checkpoint:** `terraform output app_runner_url` returns a live HTTPS URL. App works
end-to-end in prod including the new Negotiation Playbook panel.

---

### Innovation sprint demo script (8 minutes)

**Opening (30 sec):**
> "Vendor proposal review today is hours of analyst time per RFP cycle.
> I want to show you what happens when you automate the full analysis —
> and push it one step further."

**Part 1 — The analysis (3 min):**
> [Open live URL. Switch to LMS bundle.]
> "Four AI agents — extract, risk, score, memo — running in parallel on three proposals."
> [Show vendor cards with radar chart and comparison table.]
> "Canvas scores highest. Blackboard has six high-severity policy violations.
> Here's the recommendation memo."

**Part 2 — The negotiation playbook (2 min):**
> [Scroll to Negotiation Playbook panel.]
> "But here's what's new. The system didn't stop at 'Canvas wins.'
> It read Canvas's weaker dimensions and turned them into negotiation leverage.
> These are the talking points your procurement director walks into the vendor
> call with. The AI went from analysis to action."

**Part 3 — The infrastructure story (2 min):**
> [Open terraform/ in editor — show the 8 files.]
> "This entire system — API, storage, secrets, auto-scaling — is defined in
> 8 Terraform files. One command to provision it from zero. App Runner scales
> to zero at idle so the monthly cost is essentially nothing when not in use."
> [Show `terraform output app_runner_url` pointing at the live URL.]
> "Any institution can fork this repo and have it running in 10 minutes."

**Closing (30 sec):**
> "Ten days. Five AI agents. Cloud-deployed. Fully auditable in LangSmith.
> The policy, criteria, and rubric are plain text files — any team can swap
> them for their own RFP in an afternoon."

---

### Resume bullet

```
Built VendorLens — an agentic AI procurement platform using LangGraph, Claude, and Gemini.
Five AI agents (extract, risk, score, memo, negotiation) analyze vendor proposals against
institutional policy and RFP criteria, producing scored comparisons and negotiation strategy.
Provisioned full AWS stack (App Runner, ECR, S3, SSM Parameter Store) via Terraform.
```

---

## Post-Day 6 enhancements (completed)

### RFP bundle system
- Added multi-bundle support: LMS, Payroll Processing, Finance & HR (ERP)
- Each bundle has its own `context_bundle_<id>/` directory with `policy.txt`,
  `rfp_criteria_<id>.txt`, and `scoring_rubric_<id>.txt`
- Bundle registered in `tools/context_loader.py` → `BUNDLES` dict
- Frontend bundle selector uses icons per bundle (laptop / coins / bank)
- Default bundle is `lms`

### Scoring dimensions
- Added `innovation_roadmap` as a 9th scoring dimension across all bundles
- LMS: `enterprise_readiness` reduced 0.10 → 0.05 to make room; new dimension at 0.05
- All three bundles updated (rfp_criteria + scoring_rubric files)
- `ScoreCard` in `graph/state.py` and `lib/types.ts` updated
- `ScoringAgent` weight check updated from 8 → 9

### Vendor proposals
- `dummy_docs/` renamed to `vendor_proposals/` and organized into subfolders: `lms/`, `payroll/`, `erp/`
- Filenames simplified: `vendor_a_blackboard.txt` → `lms/blackboard.txt` etc.
- `scripts/ingest.py` updated: `recursive=True`, `file_metadata` override stores bare filename so ChromaDB filters still work
- `tools/mcp_server.py` updated: `rglob()` to find files across subfolders
- Real-company dummy proposals written for all three bundles:
  - LMS: Blackboard (Anthology), Canvas (Instructure), Brightspace (D2L)
  - Payroll: ADP Workforce Now, Ceridian Dayforce, Paylocity
  - ERP: Workday Financials + HCM, Oracle Cloud ERP + HCM, Unit4 ERP for Education

### UI improvements
- **Winner banner**: recommended vendor name and score shown at the top of results before vendor cards
- **Live view layout**: AgentProgressBar (left) and ThinkingLog (right) side by side during processing
- **Risk flag tooltips**: hovering a risk badge shows explanation + recommendation in a Mantine Tooltip
- **Score color legend**: ≥7 Strong · 4–6 Fair · <4 Weak shown below overall score bar
- **Risk severity legend**: HIGH · MEDIUM · LOW color key inline with the "Risk Flags" heading
- **RFP category badge**: moved from floating next to progress bar into the winner banner
- **Live activity log**: updated to say "Gemini Flash" (not "Claude Sonnet") for extraction and risk stages
- All institution-specific text (UMPO, UMass, SVM-01, LMS-specific labels) removed from frontend copy

### Code cleanup (post-Day 6)
- `api/main.py`: `asyncio.get_event_loop()` → `get_running_loop()` in all async contexts; `Optional[str]` → `str | None`; `{k: v for k, v in …}` → `dict(initial_state)`
- `api/models.py`: removed `typing` imports; all fields use `X | None` and `list[X]` (modern Python 3.10+ syntax)
- `graph/pipeline.py`: removed obvious one-liner docstrings from inner fan-out and node functions
- `agents/scoring_agent.py`: collapsed 4-line bundle key lookup to 2 `bundle.get(next(…), "")` calls
- `frontend/app/page.tsx`: eliminated IIFE inside JSX; derived vars (`scored`, `winner`, `sortedProposals`, `currentBundle`) now hoisted before `return`
- `frontend/components/ProposalCard.tsx`: unified `scoreColor`/`scoreTextColor`/`riskColor` into `SCORE_TIERS` lookup + `scoreTier()` helper and `RISK_COLORS` map; replaced 3-pass filter-spread for risk sorting with a single `.sort()` using `SEVERITY_ORDER`
- `frontend/components/ThinkingLog.tsx`: replaced 4-condition `||` chain in `isActiveStage` with a `Set.has()` lookup

### Post-Day 6 session 2 (bug fixes + cleanup)

- **Pipeline refactor**: collapsed three-stage fan-out (`extraction_node → risk_node → scoring_node`)
  into a single `vendor_node` that runs extract → risk → score sequentially per vendor.
  All vendors still process in parallel. Eliminates barrier-synchronized waves that caused
  duplicate LLM calls. `_NODE_EVENT` in `api/main.py` updated to match.

- **ChromaDB race condition fixed**: `load_index()` converted to a thread-safe singleton using
  double-checked locking (`threading.Lock`). Startup warmup fires all bundle pipelines concurrently;
  previously they all tried to create `PersistentClient` at the same path simultaneously, causing
  a crash on every boot.

- **Cybersecurity bundle fully removed**: bundle was already deleted from the backend `BUNDLES` dict
  but the hardcoded frontend default list in `page.tsx` still included it, causing it to flash on
  every page load before the `/bundles` fetch resolved. Frontend now initializes `bundles` as `[]`
  and shows a Mantine `Skeleton` placeholder until the backend responds — backend is the single
  source of truth for available bundles.

- **`pathlib.Path` import added** to `context_loader.py` — missing import was silently crashing
  the API on startup (only caught when the Docker image was rebuilt clean).

- **Risk tooltip readability**: recommendation text inside Mantine `Tooltip` changed from
  `c="dimmed"` (gray, unreadable on dark background) to `opacity: 0.75` (white-tinted, readable).

- **`scripts/setup.sh`** added — all-in-one first-time setup: build image, ingest proposals,
  start API, install frontend deps, launch Next.js.

- **`backend/README.md`** updated: Docker restart reference table added, stale SSE event list
  corrected (`extracting → memo → done`), bundle path corrected to `context_bundles/<id>/`.

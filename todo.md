# VendorLens: AI Learning Roadmap

This guide highlights the primary components and code patterns in VendorLens that you should study to master agentic AI, custom RAG pipelines, and Model Context Protocol (MCP) integrations.

---

## Roadmap: Deep AI Topics to Explore

### 1. Multi-Agent Orchestration (LangGraph)

- **Target File**: [pipeline.py](file:///home/ricardo/projects/vendorlens/backend/graph/pipeline.py)
- **Core Concepts to Study**:
  - **State Graph (`StateGraph`)**: How nodes and edges are wired to define a stateful workflow.
  - **Parallel Execution (`Send`)**: How LangGraph enables fan-out/fan-in parallel node processing across a list of proposals.
  - **Streaming Engine (`stream(..., stream_mode="updates")`)**: How the pipeline streams partial graph state modifications as nodes complete.

### 2. Highly Optimized RAG Pipelines

- **Target Files**: [extraction_agent.py](file:///home/ricardo/projects/vendorlens/backend/agents/extraction_agent.py) & [chroma.py](file:///home/ricardo/projects/vendorlens/backend/tools/chroma.py)
- **Core Concepts to Study**:
  - **Local Embeddings**: How the project uses `FastEmbedEmbedding` with `BAAI/bge-small-en-v1.5` on ONNX runtime to avoid API costs for retrieval.
  - **Parallel Retrieval (`ThreadPoolExecutor`)**: Querying multiple independent semantic scopes concurrently to reconstruct a comprehensive document profile.
  - **Deduplication**: Using `dedup_ordered` to prevent redundant overlapping text chunks from inflating prompt token counts.

### 3. Model Context Protocol (MCP)

- **Target File**: [mcp_server.py](file:///home/ricardo/projects/vendorlens/backend/tools/mcp_server.py)
- **Core Concepts to Study**:
  - **Tool Server (`FastMCP`)**: Exposing Python helper functions as structured JSON tools over standard I/O (stdio).
  - **Tool Utilization**: How agents call these functions directly or adapt them into tool configurations for graph nodes.

### 4. Prompt Caching (Anthropic Caching)

- **Target Files**: [llm_factory.py](file:///home/ricardo/projects/vendorlens/backend/tools/llm_factory.py#L90-L105) & [risk_agent.py](file:///home/ricardo/projects/vendorlens/backend/agents/risk_agent.py#L46-L55)
- **Core Concepts to Study**:
  - **Ephemerals**: Passing structured content with `"cache_control": {"type": "ephemeral"}` metadata markers in the system prompt.
  - **Context Folding**: Designing system prompts to incorporate static context (like procurement policies) once at startup so subsequent concurrent runs hit the cache, saving ~90% in token costs.

### 5. Verify Haiku max token usage

- is the current value of 16384 too high

---

## Day 11 — Pipeline Audit & Persistence (current)

### Completed this session
- **Boundary contract test suite** (`test_boundaries.py`, 40 tests) — covers every
  inter-layer data handoff (LLM output → parse_llm_json → Pydantic model → pipeline node)
- **`parse_llm_json` array bug** — was extracting `{` before `[` when preamble text preceded
  a JSON array, returning a single object instead of the list
- **`memo_agent` return type** — normalized `invoke_llm_cached` list response to `str`
- **Scoring scale** — removed spurious `× 10` multiplier; overall now correctly 0–10
  to match the rubric. Prior scale was 0–100 (introduced by an LLM fixing a UI display)
- **`CLAUDE.md`** — project-level test-first rules and pipeline contract documentation

### Still to do
- Verify Haiku max_tokens (16384 — may be unnecessarily high for scoring task)
- `_get_pipeline` lock — concurrent `/analyze` calls for the same bundle race on pipeline construction; add a per-bundle asyncio lock
- `_jobs` TTL eviction — in-memory dict still grows unbounded for jobs not yet persisted or legacy paths; add a TTL cleanup pass

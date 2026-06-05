# VendorLens: AI Learning Roadmap

This guide highlights the primary components and code patterns in VendorLens that you should study to master agentic AI, custom RAG pipelines, and Model Context Protocol (MCP) integrations.

---

## Roadmap: Deep AI Topics to Explore

### 1. Multi-Agent Orchestration (LangGraph)
* **Target File**: [pipeline.py](file:///home/ricardo/projects/vendorlens/backend/graph/pipeline.py)
* **Core Concepts to Study**:
  * **State Graph (`StateGraph`)**: How nodes and edges are wired to define a stateful workflow.
  * **Parallel Execution (`Send`)**: How LangGraph enables fan-out/fan-in parallel node processing across a list of proposals.
  * **Streaming Engine (`stream(..., stream_mode="updates")`)**: How the pipeline streams partial graph state modifications as nodes complete.

### 2. Highly Optimized RAG Pipelines
* **Target Files**: [extraction_agent.py](file:///home/ricardo/projects/vendorlens/backend/agents/extraction_agent.py) & [chroma.py](file:///home/ricardo/projects/vendorlens/backend/tools/chroma.py)
* **Core Concepts to Study**:
  * **Local Embeddings**: How the project uses `FastEmbedEmbedding` with `BAAI/bge-small-en-v1.5` on ONNX runtime to avoid API costs for retrieval.
  * **Parallel Retrieval (`ThreadPoolExecutor`)**: Querying multiple independent semantic scopes concurrently to reconstruct a comprehensive document profile.
  * **Deduplication**: Using `dedup_ordered` to prevent redundant overlapping text chunks from inflating prompt token counts.

### 3. Model Context Protocol (MCP)
* **Target File**: [mcp_server.py](file:///home/ricardo/projects/vendorlens/backend/tools/mcp_server.py)
* **Core Concepts to Study**:
  * **Tool Server (`FastMCP`)**: Exposing Python helper functions as structured JSON tools over standard I/O (stdio).
  * **Tool Utilization**: How agents call these functions directly or adapt them into tool configurations for graph nodes.

### 4. Prompt Caching (Anthropic Caching)
* **Target Files**: [llm_factory.py](file:///home/ricardo/projects/vendorlens/backend/tools/llm_factory.py#L90-L105) & [risk_agent.py](file:///home/ricardo/projects/vendorlens/backend/agents/risk_agent.py#L46-L55)
* **Core Concepts to Study**:
  * **Ephemerals**: Passing structured content with `"cache_control": {"type": "ephemeral"}` metadata markers in the system prompt.
  * **Context Folding**: Designing system prompts to incorporate static context (like procurement policies) once at startup so subsequent concurrent runs hit the cache, saving ~90% in token costs.

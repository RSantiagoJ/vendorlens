# VendorLens: Debugging & Pipeline Fixes

This document details the issues resolved during the pipeline analysis. Saved for future research and reference.

---

## 1. Outdated Google API Key Blocker in Test Suite

### Context
During initial development (Day 1-3), the project used Google Gemini for extraction, risk assessment, and scoring. In Day 4, the runtime was refactored to use Anthropic's Claude Sonnet/Haiku models and a local HuggingFace embedding model (`BAAI/bge-small-en-v1.5`) via LlamaIndex's `FastEmbed` wrapper.

### The Problem
While the application's runtime agents and Chroma DB loader were correctly updated to use Anthropic and local embeddings (obsoleting `GOOGLE_API_KEY`), the test scripts:
* `backend/tests/test_agents.py`
* `backend/tests/test_pipeline.py`
* `backend/tests/test_rag.py`

still retained startup validation logic requiring `GOOGLE_API_KEY` to be set:
```python
if not os.getenv("GOOGLE_API_KEY"):
    sys.exit("ERROR: GOOGLE_API_KEY is not set in backend/.env")
```
Because `GOOGLE_API_KEY` was correctly commented out in `backend/.env` after the migration, the test suite crashed immediately before initializing the agents or executing any queries, making it impossible to verify the pipeline locally.

### The Fix
Updated the test files to remove the `GOOGLE_API_KEY` check:
* Removed the check completely from `test_rag.py` (which runs 100% locally with zero external API calls).
* Substituted `ANTHROPIC_API_KEY` verification in `test_agents.py` and `test_pipeline.py` (which utilize Claude models for processing).

---

## 2. Score Rationale Leakage to Memo Agent

### Context
The `ScoringAgent` evaluates vendor proposals across 9 dimensions, outputting a numerical score and a short text rationale/justification for each. The `MemoAgent` synthesizes the final executive proposal memo.

### The Problem
The pipeline is designed to be highly token-efficient. According to the design specs and code comments, the `MemoAgent` is only supposed to receive numeric scores—the detailed rationales and medium/low risks are intended for the frontend UI panels, not the final executive memo.

In [memo_agent.py](file:///home/ricardo/projects/vendorlens/backend/agents/memo_agent.py), the code attempted to filter out the rationales:
```python
"scores": {
    k: (v.score if hasattr(v, "score") else v)
    for k, v in p.scores.model_dump().items()
} if p.scores else None,
```
However, calling `.model_dump()` on a Pydantic object recursively serializes all nested models into standard Python dictionaries. As a result, `v` was a dictionary, not a Pydantic `DimensionScore` object. Because dictionaries do not have a `score` attribute, `hasattr(v, "score")` evaluated to `False` for all items, bypassing the filter and forwarding the entire dictionary (containing the rationale) to the memo LLM. This caused token wastage and bloated the memo prompt.

### The Fix
Updated the comprehension block to identify if `v` is a dictionary, and safely extract the `"score"` key directly:
```python
"scores": {
    k: (v["score"] if isinstance(v, dict) and "score" in v else v)
    for k, v in p.scores.model_dump().items()
} if p.scores else None,
```
This guarantees that only numeric scores are forwarded to the `MemoAgent`, matching the design specification and reducing input token counts.

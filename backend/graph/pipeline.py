"""
graph/pipeline.py — Day 4

LangGraph pipeline orchestrating all four VendorLens agents.

Architecture:
  START
    └─ fan_out_extraction   (conditional edge → Send per proposal)
         ├─ extraction_node ─┐
         ├─ extraction_node  ├── parallel; fan-in via operator.add → extracted
         └─ extraction_node ─┘
                  ↓
         fan_out_risk        (conditional edge → Send per extracted proposal)
         ├─ risk_node ───────┐
         ├─ risk_node        ├── parallel; fan-in via operator.add → with_risks
         └─ risk_node ───────┘
                  ↓
         fan_out_scoring     (conditional edge → Send per proposal-with-risks)
         ├─ scoring_node ────┐
         ├─ scoring_node     ├── parallel; fan-in via operator.add → proposals
         └─ scoring_node ────┘
                  ↓
            memo_node         (sequential; writes `memo`)
                  ↓
                END

State design:
  `extracted`, `with_risks`, and `proposals` all use operator.add reducers so
  parallel nodes accumulate results safely without clobbering each other.

LangSmith tracing is automatic when LANGCHAIN_TRACING_V2=true and
LANGCHAIN_API_KEY are set in backend/.env.
"""

import operator
import os
from pathlib import Path
from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from dotenv import load_dotenv

load_dotenv()

import chromadb
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from agents.extraction_agent import ExtractionAgent
from agents.memo_agent import MemoAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from graph.state import ProposalState

BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "vendor_proposals"


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

def _last(a, b):
    """Reducer that keeps the most recent write — used for status and error."""
    return b


class PipelineState(TypedDict):
    pending: List[dict]                               # raw {filename, raw_text} — input only
    extracted: Annotated[List[dict], operator.add]    # fan-in from parallel extraction_nodes
    with_risks: Annotated[List[dict], operator.add]   # fan-in from parallel risk_nodes
    proposals: Annotated[List[dict], operator.add]    # fan-in from parallel scoring_nodes
    memo: Optional[str]
    status: Annotated[str, _last]                     # parallel-safe: last write wins
    error: Annotated[Optional[str], _last]            # parallel-safe: last write wins


# ---------------------------------------------------------------------------
# Index loader
# ---------------------------------------------------------------------------

def _load_index() -> VectorStoreIndex:
    embed_model = GoogleGenAIEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=os.environ["GOOGLE_API_KEY"],
    )
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(vector_store)


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------

def build_pipeline():
    """Initialize all agents and compile the LangGraph pipeline.

    Agents are initialized once here and captured by each node closure,
    so they are reused across all proposals and pipeline runs.

    Returns:
        Compiled LangGraph CompiledStateGraph ready to invoke.
    """
    print("  Loading ChromaDB index...")
    index = _load_index()
    extraction_agent = ExtractionAgent(index)
    risk_agent = RiskAgent()
    scoring_agent = ScoringAgent()
    memo_agent = MemoAgent()
    print("  Agents initialized.")

    # -----------------------------------------------------------------------
    # Fan-out dispatchers (conditional edges — return Send objects)
    # -----------------------------------------------------------------------

    def fan_out_extraction(state: PipelineState) -> List[Send]:
        """Dispatch one extraction_node per pending proposal."""
        return [Send("extraction_node", p) for p in state["pending"]]

    def fan_out_risk(state: PipelineState) -> List[Send]:
        """Dispatch one risk_node per extracted proposal."""
        return [Send("risk_node", p) for p in state["extracted"]]

    def fan_out_scoring(state: PipelineState) -> List[Send]:
        """Dispatch one scoring_node per risk-analyzed proposal."""
        return [Send("scoring_node", p) for p in state["with_risks"]]

    # -----------------------------------------------------------------------
    # Node definitions (closures capture the agent singletons above)
    # -----------------------------------------------------------------------

    def extraction_node(raw: dict) -> dict:
        """Extract structured data from one raw proposal (runs in parallel)."""
        try:
            proposal_data = extraction_agent.extract(raw["filename"])
            proposal = ProposalState(
                filename=raw["filename"],
                raw_text=raw["raw_text"],
                extracted=proposal_data,
            )
            return {"extracted": [proposal.model_dump()]}
        except Exception as e:
            proposal = ProposalState(filename=raw["filename"], raw_text=raw["raw_text"])
            return {"extracted": [proposal.model_dump()], "error": str(e)}

    def risk_node(proposal_dict: dict) -> dict:
        """Run risk analysis on one proposal (runs in parallel)."""
        try:
            p = ProposalState(**proposal_dict)
            if p.extracted:
                risks = risk_agent.analyze(p.extracted)
                return {"with_risks": [p.model_copy(update={"risks": risks}).model_dump()]}
            return {"with_risks": [proposal_dict]}
        except Exception as e:
            return {"with_risks": [proposal_dict], "error": str(e)}

    def scoring_node(proposal_dict: dict) -> dict:
        """Score one proposal (runs in parallel)."""
        try:
            p = ProposalState(**proposal_dict)
            if p.extracted:
                scores = scoring_agent.score(p.extracted, p.risks or [])
                return {"proposals": [p.model_copy(update={"scores": scores}).model_dump()]}
            return {"proposals": [proposal_dict]}
        except Exception as e:
            return {"proposals": [proposal_dict], "error": str(e)}

    def memo_node(state: PipelineState) -> dict:
        """Write the recommendation memo from all scored proposals."""
        try:
            proposals = [ProposalState(**p) for p in state["proposals"]]
            memo = memo_agent.write(proposals)
            return {"memo": memo, "status": "done"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # -----------------------------------------------------------------------
    # Graph assembly
    # -----------------------------------------------------------------------

    graph = StateGraph(PipelineState)

    graph.add_node("extraction_node", extraction_node)
    graph.add_node("risk_node", risk_node)
    graph.add_node("scoring_node", scoring_node)
    graph.add_node("memo_node", memo_node)

    graph.add_conditional_edges(START, fan_out_extraction, ["extraction_node"])
    graph.add_conditional_edges("extraction_node", fan_out_risk, ["risk_node"])
    graph.add_conditional_edges("risk_node", fan_out_scoring, ["scoring_node"])
    graph.add_edge("scoring_node", "memo_node")
    graph.add_edge("memo_node", END)

    return graph.compile()

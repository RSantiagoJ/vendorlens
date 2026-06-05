"""
graph/pipeline.py

LangGraph pipeline orchestrating all four VendorLens agents.

Architecture:
  START
    └─ fan_out_vendors   (conditional edge → Send per proposal)
         ├─ vendor_subgraph ─┐   each subgraph: extract_node → risk_node → score_node
         ├─ vendor_subgraph  ├── parallel; fan-in via operator.add → proposals
         └─ vendor_subgraph ─┘
                  ↓
            memo_node     (sequential; writes `memo`)
                  ↓
                END

Using a subgraph per vendor (rather than a single monolithic node) lets the
FastAPI SSE stream observe per-stage state updates via stream_mode="updates",
subgraphs=True, so the UI can show extraction → risk → scoring progression
in real time instead of jumping straight to done.
"""

import logging
import operator
from typing import Annotated, List, Optional
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Send
from langgraph.graph import END, START, StateGraph

from agents.extraction_agent import ExtractionAgent
from agents.memo_agent import MemoAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from graph.state import ProposalData, ProposalState, RiskFlag
from tools.chroma import load_index


# ---------------------------------------------------------------------------
# State schemas
# ---------------------------------------------------------------------------

def _last(_, b):
    return b


class PipelineState(TypedDict):
    pending: List[dict]                               # raw {filename} dicts — input only
    proposals: Annotated[List[dict], operator.add]    # fan-in from parallel vendor_subgraphs
    memo: Optional[str]
    status: Annotated[str, _last]
    error: Annotated[Optional[str], _last]


class VendorSubgraphState(TypedDict, total=False):
    filename: str                                     # required — always in Send payload
    raw_text: Optional[str]                           # optional — passed through to ProposalState
    extracted: Optional[dict]                         # set by extract_node
    risks: Optional[list]                             # set by risk_node
    error: Optional[str]                              # set on any stage failure
    proposals: Annotated[List[dict], operator.add]    # set by score_node; fan-in'd to parent


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------

def build_pipeline(bundle_id: str = "lms"):
    """Initialize all agents and compile the LangGraph pipeline for a given bundle."""
    logger.info("Loading ChromaDB index (bundle: %s)", bundle_id)
    index = load_index()
    extraction_agent = ExtractionAgent(index)
    risk_agent = RiskAgent(bundle_id=bundle_id)
    scoring_agent = ScoringAgent(bundle_id=bundle_id)
    memo_agent = MemoAgent()
    logger.info("Agents initialized")

    # -----------------------------------------------------------------------
    # Vendor subgraph nodes
    # -----------------------------------------------------------------------

    def extract_node(state: VendorSubgraphState) -> dict:
        filename = state["filename"]
        try:
            proposal_data = extraction_agent.extract(filename)
            return {"extracted": proposal_data.model_dump()}
        except Exception as e:
            logger.exception("extract_node failed for %s", filename)
            return {"error": str(e)}

    def risk_node(state: VendorSubgraphState) -> dict:
        if state.get("error"):
            return {}
        try:
            proposal_data = ProposalData(**state["extracted"])
            risks = risk_agent.analyze(proposal_data)
            return {"risks": [r.model_dump() for r in risks]}
        except Exception as e:
            logger.exception("risk_node failed for %s", state["filename"])
            return {"error": str(e)}

    def score_node(state: VendorSubgraphState) -> dict:
        filename = state["filename"]
        raw_text = state.get("raw_text")
        if state.get("error"):
            proposal = ProposalState(filename=filename, raw_text=raw_text, error=state["error"])
            return {"proposals": [proposal.model_dump()]}
        try:
            proposal_data = ProposalData(**state["extracted"])
            risks = [RiskFlag(**r) for r in (state.get("risks") or [])]
            scores = scoring_agent.score(proposal_data, risks)
            proposal = ProposalState(
                filename=filename,
                raw_text=raw_text,
                extracted=proposal_data,
                risks=risks,
                scores=scores,
            )
            return {"proposals": [proposal.model_dump()]}
        except Exception as e:
            logger.exception("score_node failed for %s", filename)
            proposal = ProposalState(filename=filename, raw_text=raw_text, error=str(e))
            return {"proposals": [proposal.model_dump()]}

    # -----------------------------------------------------------------------
    # Vendor subgraph assembly
    # -----------------------------------------------------------------------

    vendor_sg = StateGraph(VendorSubgraphState)
    vendor_sg.add_node("extract_node", extract_node)
    vendor_sg.add_node("risk_node", risk_node)
    vendor_sg.add_node("score_node", score_node)
    vendor_sg.add_edge(START, "extract_node")
    vendor_sg.add_edge("extract_node", "risk_node")
    vendor_sg.add_edge("risk_node", "score_node")
    vendor_sg.add_edge("score_node", END)
    vendor_subgraph = vendor_sg.compile()

    # -----------------------------------------------------------------------
    # Parent graph
    # -----------------------------------------------------------------------

    def fan_out_vendors(state: PipelineState) -> List[Send]:
        return [Send("vendor_subgraph", p) for p in state["pending"]]

    def memo_node(state: PipelineState) -> dict:
        try:
            all_proposals = [ProposalState(**p) for p in state["proposals"]]
            good = [p for p in all_proposals if p.scores is not None]
            failed = [p for p in all_proposals if p.scores is None]

            if not good:
                errors = "; ".join(
                    f"{p.filename}: {p.error or 'unknown error'}" for p in failed
                )
                return {"status": "error", "error": f"All vendors failed processing: {errors}"}

            memo = memo_agent.write(good)

            if failed:
                names = ", ".join(p.filename for p in failed)
                return {
                    "memo": memo,
                    "status": "done",
                    "error": f"Excluded from memo (processing failed): {names}",
                }

            return {"memo": memo, "status": "done"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    graph = StateGraph(PipelineState)
    graph.add_node("vendor_subgraph", vendor_subgraph)
    graph.add_node("memo_node", memo_node)
    graph.add_conditional_edges(START, fan_out_vendors, ["vendor_subgraph"])
    graph.add_edge("vendor_subgraph", "memo_node")
    graph.add_edge("memo_node", END)

    return graph.compile()

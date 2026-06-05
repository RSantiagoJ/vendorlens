"""
graph/pipeline.py — Day 4

LangGraph pipeline orchestrating all four VendorLens agents.

Architecture:
  START
    └─ fan_out_vendors   (conditional edge → Send per proposal)
         ├─ vendor_node ─┐   each node runs extract→risk→score sequentially
         ├─ vendor_node  ├── parallel; fan-in via operator.add → proposals
         └─ vendor_node ─┘
                  ↓
            memo_node     (sequential; writes `memo`)
                  ↓
                END

Each vendor_node processes one proposal end-to-end (extraction → risk → scoring)
so all three pipeline stages run concurrently across vendors instead of in
barrier-synchronized waves that caused duplicate LLM calls.

LangSmith tracing is automatic when LANGCHAIN_TRACING_V2=true and
LANGCHAIN_API_KEY are set in backend/.env.
"""

import logging
import operator
from typing import Annotated, List, Optional
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from agents.extraction_agent import ExtractionAgent
from agents.memo_agent import MemoAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from graph.state import ProposalState
from tools.chroma import load_index


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

def _last(_, b):
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
# Pipeline builder
# ---------------------------------------------------------------------------

def build_pipeline(bundle_id: str = "lms"):
    """Initialize all agents and compile the LangGraph pipeline for a given bundle.

    Args:
        bundle_id: Context bundle to use for risk and scoring agents (e.g. "lms", "payroll", "erp").

    Returns:
        Compiled LangGraph CompiledStateGraph ready to invoke.
    """
    logger.info("Loading ChromaDB index (bundle: %s)", bundle_id)
    index = load_index()
    extraction_agent = ExtractionAgent(index)
    risk_agent = RiskAgent(bundle_id=bundle_id)
    scoring_agent = ScoringAgent(bundle_id=bundle_id)
    memo_agent = MemoAgent()
    logger.info("Agents initialized")

    # -----------------------------------------------------------------------
    # Fan-out dispatchers (conditional edges — return Send objects)
    # -----------------------------------------------------------------------

    def fan_out_vendors(state: PipelineState) -> List[Send]:
        return [Send("vendor_node", p) for p in state["pending"]]

    # -----------------------------------------------------------------------
    # Node definitions (closures capture the agent singletons above)
    # -----------------------------------------------------------------------

    def vendor_node(raw: dict) -> dict:
        """Process one vendor end-to-end: extract → risk → score."""
        filename = raw["filename"]
        raw_text = raw["raw_text"]
        try:
            proposal_data = extraction_agent.extract(filename)
            proposal = ProposalState(filename=filename, raw_text=raw_text, extracted=proposal_data)
            risks = risk_agent.analyze(proposal_data)
            proposal = proposal.model_copy(update={"risks": risks})
            scores = scoring_agent.score(proposal_data, risks)
            proposal = proposal.model_copy(update={"scores": scores})
            return {"proposals": [proposal.model_dump()]}
        except Exception as e:
            logger.exception("vendor_node failed for %s", filename)
            proposal = ProposalState(filename=filename, raw_text=raw_text, error=str(e))
            return {"proposals": [proposal.model_dump()]}

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

    # -----------------------------------------------------------------------
    # Graph assembly
    # -----------------------------------------------------------------------

    graph = StateGraph(PipelineState)

    graph.add_node("vendor_node", vendor_node)
    graph.add_node("memo_node", memo_node)

    graph.add_conditional_edges(START, fan_out_vendors, ["vendor_node"])
    graph.add_edge("vendor_node", "memo_node")
    graph.add_edge("memo_node", END)

    return graph.compile()

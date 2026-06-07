"""
graph/pipeline.py

LangGraph pipeline orchestrating all four VendorLens agents.

Architecture:
  START
    └─ warm_caches    (parallel warm-up calls to prime Anthropic prompt caches)
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
from agents.negotiation_agent import NegotiationAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from graph.state import ProposalData, ProposalState, RiskFlag
from tools.chroma import load_index
from tools.llm_factory import invoke_llm_cached


# ---------------------------------------------------------------------------
# State schemas
# ---------------------------------------------------------------------------

def _last(_, b):
    return b


class PipelineState(TypedDict):
    pending: List[dict]                               # raw {filename} dicts — input only
    proposals: Annotated[List[dict], operator.add]    # fan-in from parallel vendor_subgraphs
    memo: Optional[str]
    negotiation_plans: Annotated[Optional[list], _last]
    status: Annotated[str, _last]
    error: Annotated[Optional[str], _last]


class VendorSubgraphState(TypedDict, total=False):
    filename: str                                     # required — always in Send payload
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
    negotiation_agent = NegotiationAgent()
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

        # Safely parse whatever state we have so far to avoid losing it on error
        proposal_data = None
        if state.get("extracted"):
            try:
                proposal_data = ProposalData(**state["extracted"])
            except Exception:
                pass

        risks = None
        if state.get("risks") is not None:
            try:
                risks = [RiskFlag(**r) for r in state["risks"]]
            except Exception:
                pass

        upstream_error = state.get("error")

        # Extraction failure is fatal — no data to score.
        if upstream_error and not proposal_data:
            proposal = ProposalState(
                filename=filename,
                error=upstream_error,
            )
            return {"proposals": [proposal.model_dump()]}

        # Risk failure is non-fatal — score with whatever risks we have (may be empty).
        try:
            if not proposal_data:
                raise ValueError("No extraction data available for scoring.")
            scores = scoring_agent.score(proposal_data, risks or [])
            proposal = ProposalState(
                filename=filename,
                extracted=proposal_data,
                risks=risks,
                scores=scores,
                error=upstream_error,  # surface risk-stage error even on scoring success
            )
            return {"proposals": [proposal.model_dump()]}
        except Exception as e:
            logger.exception("score_node failed for %s", filename)
            proposal = ProposalState(
                filename=filename,
                extracted=proposal_data,
                risks=risks,
                error=str(e),
            )
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

    def warm_caches_node(state: PipelineState) -> dict:
        """Pre-warm Anthropic prompt caches before parallel vendor fan-out.

        Fires one minimal call per agent in parallel so cache entries exist
        before the vendor subgraphs start — all 3 vendors then get cache hits
        on the first run instead of only on subsequent runs.
        """
        from concurrent.futures import ThreadPoolExecutor

        targets = [
            (extraction_agent.llm,    extraction_agent.system_prompt),
            (risk_agent.llm,          risk_agent.system_prompt),
            (scoring_agent.llm,       scoring_agent.system_prompt),
            (negotiation_agent.llm,   negotiation_agent.system_prompt),
        ]

        def warm(args):
            llm, prompt = args
            invoke_llm_cached(llm, prompt, "ready")

        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(warm, targets))
        except Exception:
            logger.warning("Cache warm-up failed — continuing without pre-warmed caches", exc_info=True)

        return {}

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

    def negotiation_node(state: PipelineState) -> dict:
        try:
            all_proposals = [ProposalState(**p) for p in state["proposals"]]
            briefs = negotiation_agent.plan(all_proposals)
            return {"negotiation_plans": [b.model_dump() for b in briefs]}
        except Exception as e:
            logger.exception("negotiation_node failed")
            return {"negotiation_plans": []}

    graph = StateGraph(PipelineState)
    graph.add_node("warm_caches", warm_caches_node)
    graph.add_node("vendor_subgraph", vendor_subgraph)
    graph.add_node("memo_node", memo_node)
    graph.add_node("negotiation_node", negotiation_node)
    graph.add_edge(START, "warm_caches")
    graph.add_conditional_edges("warm_caches", fan_out_vendors, ["vendor_subgraph"])
    graph.add_edge("vendor_subgraph", "memo_node")
    graph.add_edge("memo_node", "negotiation_node")
    graph.add_edge("negotiation_node", END)

    return graph.compile()

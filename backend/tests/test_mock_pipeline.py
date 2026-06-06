"""
test_mock_pipeline.py — offline pipeline test suite.

Simulates the LangGraph pipeline and agent logic with mock embedding,
retrieval, and LLM responses. No external API keys or connections needed.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from graph.pipeline import build_pipeline
from graph.state import ProposalState
from agents.scoring_agent import ScoringAgent, _parse_score_value

from llama_index.core.embeddings.mock_embed_model import MockEmbedding


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_EXTRACTION_BLACKBOARD = {
    "vendor_name": "Blackboard Learn Ultra",
    "total_cost": "$2,640,000",
    "pricing_model": "$44 per student FTE",
    "price_escalation": "6% automatically",
    "overage_fees": None,
    "contract_length": "3 years",
    "renewal_terms": "successive 1-year terms",
    "termination_clause": "180 days written notice",
    "liability_cap": "$50,000",
    "data_ownership": "Institution owns raw content",
    "data_processing_agreement": "Available upon request",
    "security_certifications": "SOC 2 Type I",
    "incident_response_docs": "Available upon request",
    "sla_uptime": "99% annual",
    "sla_response_times": "Best effort",
    "sla_penalties": "None",
    "support_model": "Mon-Fri 8am-8pm",
    "training_offered": "Two recorded webinars",
    "multi_campus_support": "Yes",
    "user_roles": "Student, Instructor, Admin",
    "mobile_app": "iOS and Android",
    "accessibility_vpat": "VPAT 2.1; WCAG 2.0 AA only",
    "social_listening": None,
    "analytics_reporting": "Basic reporting",
    "integrations": "Banner, Workday",
    "sandbox_available": "No",
    "customer_references": "Seven references",
    "supplier_diversity": None,
    "deliverables": ["Implementation plan"],
    "ip_ownership": "Anthology proprietary",
    "governing_law": "North Carolina",
}

MOCK_RISKS_BLACKBOARD = [
    {
        "clause": "Data ownership language",
        "severity": "HIGH",
        "explanation": "Vague data-ownership language.",
        "recommendation": "Negotiate portability.",
        "policy_reference": "FERPA 34 CFR §99.31",
        "policy_excerpt": "Quote",
    },
    {
        "clause": "Missing Data Processing Agreement",
        "severity": "HIGH",
        "explanation": "No DPA provided.",
        "recommendation": "Require DPA.",
        "policy_reference": "FERPA 34 CFR Part 99",
        "policy_excerpt": "Quote",
    },
    {
        "clause": "SOC 2 Type I only",
        "severity": "HIGH",
        "explanation": "Only SOC 2 Type I certification.",
        "recommendation": "Require SOC 2 Type II.",
        "policy_reference": "Security policy Section 3",
        "policy_excerpt": "Quote",
    },
]

# All 9 dimensions present with valid float scores.
MOCK_SCORING_VALID = {
    "platform_functionality": {"score": 6.0, "rationale": "Legacy platform."},
    "accessibility_compliance": {"score": 5.0, "rationale": "WCAG 2.0 AA only."},
    "integration_capability": {"score": 6.0, "rationale": "Native Banner integration."},
    "pricing_transparency": {"score": 8.0, "rationale": "Lowest cost."},
    "security_and_compliance": {"score": 4.0, "rationale": "SOC 2 Type I only."},
    "support_and_training": {"score": 5.0, "rationale": "Email-only support."},
    "enterprise_readiness": {"score": 6.0, "rationale": "Scales but dated."},
    "innovation_roadmap": {"score": 5.0, "rationale": "Roadmap not provided."},
    "risk_level": {"score": 0.0, "rationale": "Three HIGH severity risk flags."},
}

# risk_level returns "N/A" instead of a float.
MOCK_SCORING_INVALID_FLOAT = {**MOCK_SCORING_VALID, "risk_level": {"score": "N/A", "rationale": "Three HIGH severity risk flags."}}

# Only one dimension returned; the other 8 are missing.
MOCK_SCORING_PARTIAL = {
    "platform_functionality": {"score": 7.0, "rationale": "Good core functionality."},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_CRITERIA = (
    "core_lms_functionality         weight: 0.20\n"
    "accessibility_compliance       weight: 0.15\n"
    "integration_interoperability   weight: 0.10\n"
    "pricing_and_licensing          weight: 0.10\n"
    "security_and_compliance        weight: 0.20\n"
    "support_and_training           weight: 0.10\n"
    "enterprise_readiness           weight: 0.05\n"
    "innovation_roadmap             weight: 0.05\n"
    "risk_level                     weight: 0.05\n"
)


def _build_graph():
    from llama_index.core import Settings
    Settings.embed_model = MockEmbedding(embed_dim=384)
    return build_pipeline(bundle_id="lms")


def _state(*filenames):
    return {
        "pending": [{"filename": f} for f in filenames],
        "proposals": [],
        "memo": None,
        "status": "pending",
        "error": None,
    }


# ---------------------------------------------------------------------------
# Full pipeline — happy paths
# ---------------------------------------------------------------------------

@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.extraction_agent.invoke_llm_cached")
@patch("agents.risk_agent.invoke_llm_cached")
@patch("agents.scoring_agent.invoke_llm_cached")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_valid_run(
    mock_memo, mock_score_llm, mock_risk_llm, mock_extract_llm, mock_retrieve, mock_load_index
):
    """Full happy path: all agents succeed, proposal is scored, memo is written."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.return_value = "some text chunks"
    mock_extract_llm.return_value = json.dumps(MOCK_EXTRACTION_BLACKBOARD)
    mock_risk_llm.return_value = json.dumps(MOCK_RISKS_BLACKBOARD)
    mock_score_llm.return_value = json.dumps(MOCK_SCORING_VALID)
    mock_memo.return_value = "Mock Recommendation Memo"

    result = _build_graph().invoke(_state("blackboard.txt"))

    assert result["status"] == "done"
    assert result["memo"] == "Mock Recommendation Memo"
    assert len(result["proposals"]) == 1

    p = result["proposals"][0]
    assert p["error"] is None
    assert p["extracted"]["vendor_name"] == "Blackboard Learn Ultra"
    assert p["risks"] is not None
    assert len(p["risks"]) == 3
    # (6*.20 + 5*.15 + 6*.10 + 8*.10 + 4*.20 + 5*.10 + 6*.05 + 5*.05 + 0*.05) * 10 = 52.0
    assert p["scores"]["overall"] == 52.0


@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.extraction_agent.invoke_llm_cached")
@patch("agents.risk_agent.invoke_llm_cached")
@patch("agents.scoring_agent.invoke_llm_cached")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_multi_vendor_both_succeed(
    mock_memo, mock_score_llm, mock_risk_llm, mock_extract_llm, mock_retrieve, mock_load_index
):
    """Two vendors through the fan-out/fan-in both produce scored proposals."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.return_value = "some text chunks"
    mock_extract_llm.return_value = json.dumps(MOCK_EXTRACTION_BLACKBOARD)
    mock_risk_llm.return_value = json.dumps(MOCK_RISKS_BLACKBOARD)
    mock_score_llm.return_value = json.dumps(MOCK_SCORING_VALID)
    mock_memo.return_value = "Memo for two vendors"

    result = _build_graph().invoke(_state("blackboard.txt", "canvas.txt"))

    assert result["status"] == "done"
    assert len(result["proposals"]) == 2
    for p in result["proposals"]:
        assert p["scores"] is not None
        assert p["error"] is None


# ---------------------------------------------------------------------------
# Full pipeline — failure / degraded paths
# ---------------------------------------------------------------------------

@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_extraction_fail(mock_memo, mock_retrieve, mock_load_index):
    """Extraction crash → proposal preserves the error, no scores, pipeline status=error."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.side_effect = Exception("ChromaDB unavailable")

    result = _build_graph().invoke(_state("blackboard.txt"))

    assert result["status"] == "error"
    assert len(result["proposals"]) == 1

    p = result["proposals"][0]
    assert p["extracted"] is None
    assert p["scores"] is None
    assert "ChromaDB unavailable" in p["error"]
    mock_memo.assert_not_called()


@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.extraction_agent.invoke_llm_cached")
@patch("agents.risk_agent.invoke_llm_cached")
@patch("agents.scoring_agent.invoke_llm_cached")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_risk_fail_still_scores(
    mock_memo, mock_score_llm, mock_risk_llm, mock_extract_llm, mock_retrieve, mock_load_index
):
    """Risk crash is non-fatal — scoring proceeds with empty risks, data is returned."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.return_value = "some text chunks"
    mock_extract_llm.return_value = json.dumps(MOCK_EXTRACTION_BLACKBOARD)
    mock_risk_llm.side_effect = Exception("Policy file missing")
    mock_score_llm.return_value = json.dumps(MOCK_SCORING_VALID)
    mock_memo.return_value = "Memo written despite risk failure"

    result = _build_graph().invoke(_state("blackboard.txt"))

    assert result["status"] == "done"
    p = result["proposals"][0]
    assert p["extracted"]["vendor_name"] == "Blackboard Learn Ultra"
    assert p["scores"] is not None, "scoring must proceed even when risk analysis fails"
    assert p["risks"] is None
    assert p["error"] is not None  # risk-stage error preserved for UI display


@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.extraction_agent.invoke_llm_cached")
@patch("agents.risk_agent.invoke_llm_cached")
@patch("agents.scoring_agent.invoke_llm_cached")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_scoring_fail_retains_data(
    mock_memo, mock_score_llm, mock_risk_llm, mock_extract_llm, mock_retrieve, mock_load_index
):
    """Scoring crash preserves extraction + risk data in the proposal."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.return_value = "some text chunks"
    mock_extract_llm.return_value = json.dumps(MOCK_EXTRACTION_BLACKBOARD)
    mock_risk_llm.return_value = json.dumps(MOCK_RISKS_BLACKBOARD)
    mock_score_llm.side_effect = Exception("Simulated scoring crash")
    mock_memo.return_value = "should not matter"

    result = _build_graph().invoke(_state("blackboard.txt"))

    assert len(result["proposals"]) == 1
    p = result["proposals"][0]
    assert p["extracted"]["vendor_name"] == "Blackboard Learn Ultra"
    assert p["risks"] is not None
    assert len(p["risks"]) == 3
    assert p["scores"] is None
    assert p["error"] is not None


@patch("graph.pipeline.load_index")
@patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
@patch("agents.memo_agent.MemoAgent.write")
def test_pipeline_all_vendors_fail(mock_memo, mock_retrieve, mock_load_index):
    """All vendors fail extraction → memo_node returns error status."""
    mock_load_index.return_value = MagicMock()
    mock_retrieve.side_effect = Exception("Extraction failure")

    result = _build_graph().invoke(_state("blackboard.txt", "canvas.txt"))

    assert result["status"] == "error"
    assert result["error"] is not None
    assert len(result["proposals"]) == 2
    for p in result["proposals"]:
        assert p["scores"] is None
    mock_memo.assert_not_called()


# ---------------------------------------------------------------------------
# ScoringAgent unit tests
# ---------------------------------------------------------------------------

def test_score_value_parsing():
    """_parse_score_value handles all real-world LLM output formats."""
    # Numeric pass-through
    assert _parse_score_value(7) == 7.0
    assert _parse_score_value(7.5) == 7.5
    assert _parse_score_value(0) == 0.0

    # None / empty / sentinel strings
    assert _parse_score_value(None) == 0.0
    assert _parse_score_value("N/A") == 0.0
    assert _parse_score_value("n/a") == 0.0
    assert _parse_score_value("na") == 0.0
    assert _parse_score_value("none") == 0.0
    assert _parse_score_value("null") == 0.0
    assert _parse_score_value("unknown") == 0.0
    assert _parse_score_value("") == 0.0

    # Fraction format ("numerator/denominator")
    assert _parse_score_value("8/10") == 8.0
    assert _parse_score_value("7.5/10") == 7.5

    # Leading number with trailing prose
    assert _parse_score_value("7.5 overall") == 7.5
    assert _parse_score_value("9 out of 10") == 9.0

    # Completely unparseable
    assert _parse_score_value("excellent") == 0.0


@patch("tools.context_loader.load_context_bundle")
def test_scoring_agent_na_score(mock_bundle):
    """ScoringAgent handles 'N/A' score from LLM without crashing."""
    mock_bundle.return_value = {"scoring_rubric_lms": "rubric", "rfp_criteria_lms": _MOCK_CRITERIA}
    agent = ScoringAgent(bundle_id="lms")

    from graph.state import ProposalData, RiskFlag
    prop = ProposalData(vendor_name="Blackboard")
    risks = [RiskFlag(clause="test", severity="HIGH", explanation="x", recommendation="x", policy_reference="x")]

    with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
        mock_invoke.return_value = json.dumps(MOCK_SCORING_INVALID_FLOAT)
        scorecard = agent.score(prop, risks)

    assert scorecard.risk_level.score == 0.0
    assert scorecard.overall is not None


@patch("tools.context_loader.load_context_bundle")
def test_scoring_agent_partial_scorecard(mock_bundle):
    """LLM drops fields → missing dimensions default to 0.0, not a crash."""
    mock_bundle.return_value = {"scoring_rubric_lms": "rubric", "rfp_criteria_lms": _MOCK_CRITERIA}
    agent = ScoringAgent(bundle_id="lms")

    from graph.state import ProposalData
    prop = ProposalData(vendor_name="TestVendor")

    with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
        mock_invoke.return_value = json.dumps(MOCK_SCORING_PARTIAL)
        scorecard = agent.score(prop, [])

    assert scorecard.platform_functionality.score == 7.0
    assert scorecard.accessibility_compliance.score == 0.0
    assert scorecard.risk_level.score == 0.0
    # only platform_functionality contributes: 7.0 * 0.20 * 10 = 14.0
    assert scorecard.overall == 14.0


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------

def test_weight_sum():
    """rfp_criteria weights must sum to 1.0 so that a perfect proposal scores 100.0."""
    from agents.scoring_agent import _parse_weights
    from tools.context_loader import load_context_bundle
    bundle = load_context_bundle("lms")
    criteria = bundle.get(next(k for k in bundle if k.startswith("rfp_criteria")), "")
    weights = _parse_weights(criteria)
    total = round(sum(weights.values()), 10)
    assert total == pytest.approx(1.0), (
        f"rfp_criteria weights sum to {total:.4f} — "
        f"a perfect proposal would score {total * 10 * 10:.1f} instead of 100.0. "
        f"Fix rfp_criteria_lms.txt so weights sum to exactly 1.00."
    )

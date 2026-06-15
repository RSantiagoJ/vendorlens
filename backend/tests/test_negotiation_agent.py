"""
test_negotiation_agent.py — Unit tests for NegotiationAgent.

All offline — LLM calls are mocked.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from graph.state import NegotiationBrief, NegotiationTactic, ProposalState, ProposalData, RiskFlag, ScoreCard, DimensionScore


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_scorecard(overall: float = 7.0) -> ScoreCard:
    dim = DimensionScore(score=overall, rationale="test")
    return ScoreCard(
        platform_functionality=dim,
        accessibility_compliance=dim,
        integration_capability=dim,
        pricing_transparency=dim,
        security_and_compliance=dim,
        support_and_training=dim,
        enterprise_readiness=dim,
        innovation_roadmap=dim,
        risk_level=dim,
        overall=overall,
    )


def _make_proposal(vendor_name: str, overall: float = 7.0, risks: list | None = None) -> ProposalState:
    return ProposalState(
        filename=f"{vendor_name.lower()}.txt",
        extracted=ProposalData(
            vendor_name=vendor_name,
            total_cost="$1,000,000",
            pricing_model="Per-seat annual",
            price_escalation="5% annually",
            termination_clause="90 days written notice",
            liability_cap="$50,000",
        ),
        risks=risks or [
            RiskFlag(
                clause="Liability cap",
                severity="HIGH",
                explanation="Cap is far below contract value.",
                recommendation="Negotiate to $500K minimum.",
                policy_reference="Section 4.2",
            )
        ],
        scores=_make_scorecard(overall),
    )


MOCK_LLM_RESPONSE = json.dumps([
    {
        "vendor_name": "AlphaVendor",
        "overall_approach": "Firm but fair — we have a credible BATNA.",
        "priority_tactics": [
            {
                "area": "Pricing escalation",
                "their_position": "5% annual auto-escalation",
                "our_ask": "Cap escalation at 3% or CPI, whichever is lower",
                "leverage": "Competitor offers fixed pricing over the same term",
            },
            {
                "area": "Liability cap",
                "their_position": "$50,000 cap — 5% of contract value",
                "our_ask": "Minimum $500,000 or 1x annual contract value",
                "leverage": "Institutional procurement policy requires adequate coverage; HIGH risk flag raised",
            },
        ],
        "red_lines": [
            "Liability cap must exceed $250,000",
            "SOC 2 Type II required before go-live",
        ],
        "concessions_to_offer": [
            "Multi-year commitment (3 years)",
            "Quarterly instead of monthly invoicing",
        ],
        "batna": "BetaVendor scored 6.5/10 overall — viable alternative if AlphaVendor won't move on red lines",
    }
])


# ---------------------------------------------------------------------------
# Model shape tests (can run without the agent)
# ---------------------------------------------------------------------------

class TestNegotiationModels:
    def test_negotiation_tactic_fields(self):
        t = NegotiationTactic(
            area="Pricing",
            their_position="$44/seat",
            our_ask="$38/seat",
            leverage="Competitor is cheaper",
        )
        assert t.area == "Pricing"
        assert t.our_ask == "$38/seat"

    def test_negotiation_brief_fields(self):
        b = NegotiationBrief(
            vendor_name="TestVendor",
            overall_approach="Be firm.",
            priority_tactics=[
                NegotiationTactic(
                    area="Pricing",
                    their_position="$44/seat",
                    our_ask="$38/seat",
                    leverage="Competitor is cheaper",
                )
            ],
            red_lines=["SOC 2 Type II required"],
            concessions_to_offer=["3-year commitment"],
            batna="Competitor scored 8.0",
        )
        assert b.vendor_name == "TestVendor"
        assert len(b.priority_tactics) == 1
        assert len(b.red_lines) == 1

    def test_negotiation_brief_model_dump_round_trip(self):
        b = NegotiationBrief(
            vendor_name="TestVendor",
            overall_approach="Be firm.",
            priority_tactics=[
                NegotiationTactic(
                    area="Pricing",
                    their_position="$44/seat",
                    our_ask="$38/seat",
                    leverage="Competitor is cheaper",
                )
            ],
            red_lines=["SOC 2 Type II required"],
            concessions_to_offer=["3-year commitment"],
            batna="Competitor scored 8.0",
        )
        d = b.model_dump()
        b2 = NegotiationBrief(**d)
        assert b2.vendor_name == b.vendor_name
        assert b2.priority_tactics[0].area == b.priority_tactics[0].area

    def test_proposal_state_has_negotiation_brief_field(self):
        """ProposalState must not carry a negotiation brief — briefs live at the top level."""
        p = ProposalState(filename="test.txt")
        assert not hasattr(p, "negotiation_brief"), (
            "NegotiationBrief belongs in VendorLensState.negotiation_plans, not ProposalState"
        )


# ---------------------------------------------------------------------------
# NegotiationAgent unit tests
# ---------------------------------------------------------------------------

class TestNegotiationAgent:
    @patch("agents.negotiation_agent.invoke_llm_cached")
    @patch("agents.negotiation_agent.make_haiku_llm")
    @patch("agents.negotiation_agent.load_prompt")
    def test_plan_returns_list_of_briefs(self, mock_load_prompt, mock_haiku, mock_llm):
        mock_load_prompt.return_value = "You are a negotiation expert."
        mock_haiku.return_value = MagicMock()
        mock_llm.return_value = MOCK_LLM_RESPONSE

        from agents.negotiation_agent import NegotiationAgent
        agent = NegotiationAgent()
        proposals = [_make_proposal("AlphaVendor", overall=7.0)]
        result = agent.plan(proposals)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], NegotiationBrief)

    @patch("agents.negotiation_agent.invoke_llm_cached")
    @patch("agents.negotiation_agent.make_haiku_llm")
    @patch("agents.negotiation_agent.load_prompt")
    def test_plan_brief_has_required_fields(self, mock_load_prompt, mock_haiku, mock_llm):
        mock_load_prompt.return_value = "You are a negotiation expert."
        mock_haiku.return_value = MagicMock()
        mock_llm.return_value = MOCK_LLM_RESPONSE

        from agents.negotiation_agent import NegotiationAgent
        agent = NegotiationAgent()
        proposals = [_make_proposal("AlphaVendor", overall=7.0)]
        result = agent.plan(proposals)

        brief = result[0]
        assert brief.vendor_name == "AlphaVendor"
        assert brief.overall_approach
        assert len(brief.priority_tactics) >= 1
        assert len(brief.red_lines) >= 1
        assert len(brief.concessions_to_offer) >= 1
        assert brief.batna

    @patch("agents.negotiation_agent.invoke_llm_cached")
    @patch("agents.negotiation_agent.make_haiku_llm")
    @patch("agents.negotiation_agent.load_prompt")
    def test_plan_tactic_has_required_fields(self, mock_load_prompt, mock_haiku, mock_llm):
        mock_load_prompt.return_value = "You are a negotiation expert."
        mock_haiku.return_value = MagicMock()
        mock_llm.return_value = MOCK_LLM_RESPONSE

        from agents.negotiation_agent import NegotiationAgent
        agent = NegotiationAgent()
        result = agent.plan([_make_proposal("AlphaVendor")])

        tactic = result[0].priority_tactics[0]
        assert tactic.area
        assert tactic.their_position
        assert tactic.our_ask
        assert tactic.leverage

    @patch("agents.negotiation_agent.invoke_llm_cached")
    @patch("agents.negotiation_agent.make_haiku_llm")
    @patch("agents.negotiation_agent.load_prompt")
    def test_plan_skips_failed_proposals(self, mock_load_prompt, mock_haiku, mock_llm):
        """Proposals with scores=None (failed vendors) must not appear in briefs."""
        mock_load_prompt.return_value = "You are a negotiation expert."
        mock_haiku.return_value = MagicMock()
        mock_llm.return_value = MOCK_LLM_RESPONSE

        from agents.negotiation_agent import NegotiationAgent
        agent = NegotiationAgent()
        good = _make_proposal("AlphaVendor", overall=7.0)
        failed = ProposalState(filename="failed.txt", error="extraction failed")

        # LLM mock returns 1 brief — agent must only pass good proposals
        result = agent.plan([good, failed])
        assert len(result) == 1

    @patch("agents.negotiation_agent.invoke_llm_cached")
    @patch("agents.negotiation_agent.make_haiku_llm")
    @patch("agents.negotiation_agent.load_prompt")
    def test_plan_handles_list_llm_response(self, mock_load_prompt, mock_haiku, mock_llm):
        """invoke_llm_cached can return a list of content blocks — agent must handle it."""
        mock_load_prompt.return_value = "You are a negotiation expert."
        mock_haiku.return_value = MagicMock()
        mock_llm.return_value = [{"type": "text", "text": MOCK_LLM_RESPONSE}]

        from agents.negotiation_agent import NegotiationAgent
        agent = NegotiationAgent()
        result = agent.plan([_make_proposal("AlphaVendor")])
        assert len(result) == 1
        assert isinstance(result[0], NegotiationBrief)

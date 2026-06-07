"""
test_boundaries.py — Data contract tests at every inter-layer handoff.

Each test targets one boundary (the edge between two pipeline stages) and
verifies that the data shape produced by the upstream stage is correctly
consumed by the downstream stage. No real API calls are made.

Boundaries:
  B1  LLM raw string → parse_llm_json
  B2  parse_llm_json dict → ProposalData.model_validate()
  B3  ProposalData ↔ model_dump() round-trip
  B4  Risk LLM list → RiskFlag construction
  B5  ProposalState ↔ model_dump() round-trip (nested models, as in memo_node)
  B6  invoke_llm_cached return → memo_agent.write() return type contract
  B7  _compute_overall scale vs. rubric declaration (max 10.0)
"""

import json
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from graph.state import DimensionScore, ProposalData, ProposalState, RiskFlag, ScoreCard
from tools.llm_factory import parse_llm_json


# ---------------------------------------------------------------------------
# Shared builders — produce the exact dict shapes that flow between stages
# ---------------------------------------------------------------------------

def _dimension_score_dict(score: float = 7.0) -> dict:
    return {"score": score, "rationale": "Test rationale."}


def _scorecard_dict(overall: float = 70.0) -> dict:
    return {
        "platform_functionality":   _dimension_score_dict(7.0),
        "accessibility_compliance": _dimension_score_dict(7.0),
        "integration_capability":   _dimension_score_dict(7.0),
        "pricing_transparency":     _dimension_score_dict(7.0),
        "security_and_compliance":  _dimension_score_dict(7.0),
        "support_and_training":     _dimension_score_dict(7.0),
        "enterprise_readiness":     _dimension_score_dict(7.0),
        "innovation_roadmap":       _dimension_score_dict(7.0),
        "risk_level":               _dimension_score_dict(7.0),
        "overall": overall,
    }


def _risk_flag_dict(**overrides) -> dict:
    return {
        "clause": "Liability cap",
        "severity": "HIGH",
        "explanation": "Cap is too low.",
        "recommendation": "Negotiate a higher cap.",
        "policy_reference": "Section 4.2",
        "policy_excerpt": None,
        **overrides,
    }


def _proposal_data_dict(**overrides) -> dict:
    return {
        "vendor_name": "TestVendor",
        "total_cost": "$1,000,000",
        "deliverables": ["Implementation plan", "Training"],
        **overrides,
    }


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

_ALL_SCORECARD_FIELDS = [
    "platform_functionality", "accessibility_compliance", "integration_capability",
    "pricing_transparency", "security_and_compliance", "support_and_training",
    "enterprise_readiness", "innovation_roadmap", "risk_level",
]


# ---------------------------------------------------------------------------
# B1 — LLM raw string → parse_llm_json
# ---------------------------------------------------------------------------

class TestB1ParseLLMJson:
    """parse_llm_json must robustly extract JSON from every format Claude can return."""

    def test_plain_json_object(self):
        raw = '{"vendor_name": "Acme", "total_cost": "$100k"}'
        assert parse_llm_json(raw)["vendor_name"] == "Acme"

    def test_plain_json_array(self):
        raw = '[{"clause": "test", "severity": "HIGH"}]'
        result = parse_llm_json(raw)
        assert isinstance(result, list)
        assert result[0]["clause"] == "test"

    def test_fenced_json_with_language_tag(self):
        raw = '```json\n{"vendor_name": "Acme"}\n```'
        assert parse_llm_json(raw)["vendor_name"] == "Acme"

    def test_fenced_json_without_language_tag(self):
        raw = '```\n{"vendor_name": "Acme"}\n```'
        assert parse_llm_json(raw)["vendor_name"] == "Acme"

    def test_json_with_preamble_text(self):
        raw = 'Here is the extracted data:\n{"vendor_name": "Acme"}\nLet me know if you need more.'
        assert parse_llm_json(raw)["vendor_name"] == "Acme"

    def test_json_array_with_preamble_text(self):
        raw = 'Risk flags identified:\n[{"clause": "test", "severity": "HIGH"}]'
        result = parse_llm_json(raw)
        assert isinstance(result, list)

    def test_list_content_blocks(self):
        """Anthropic returns content as a list of typed block dicts in some configurations."""
        raw = [{"type": "text", "text": '{"vendor_name": "Acme"}'}]
        assert parse_llm_json(raw)["vendor_name"] == "Acme"

    def test_list_content_blocks_with_array_payload(self):
        raw = [{"type": "text", "text": '[{"clause": "x", "severity": "LOW"}]'}]
        result = parse_llm_json(raw)
        assert isinstance(result, list)

    def test_no_valid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="No valid JSON"):
            parse_llm_json("This is just prose with no JSON.")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_llm_json("")


# ---------------------------------------------------------------------------
# B2 — parse_llm_json dict → ProposalData.model_validate()
# ---------------------------------------------------------------------------

class TestB2ProposalDataValidation:
    """The dict that parse_llm_json returns must be safely constructable into ProposalData."""

    def test_valid_full_extraction(self):
        proposal = ProposalData.model_validate(_proposal_data_dict())
        assert proposal.vendor_name == "TestVendor"
        assert proposal.deliverables == ["Implementation plan", "Training"]

    def test_all_none_fields_are_valid(self):
        """LLM returns explicit nulls — all optional fields must accept None, not raise."""
        proposal = ProposalData.model_validate({})
        assert proposal.vendor_name is None
        assert proposal.deliverables is None

    def test_extra_fields_are_ignored(self):
        """LLM may return extra fields not in the schema — must not raise."""
        data = _proposal_data_dict(nonexistent_field="surprise", another="value")
        proposal = ProposalData.model_validate(data)
        assert proposal.vendor_name == "TestVendor"

    def test_deliverables_as_string_raises(self):
        """LLM returns 'deliverables' as a plain string instead of a list.

        If Pydantic silently iterates the string into characters the caller
        gets ['I','m','p',...] — silent data corruption. Must raise instead.
        """
        data = _proposal_data_dict(deliverables="Implementation plan")
        with pytest.raises(ValidationError):
            ProposalData.model_validate(data)

    def test_deliverables_as_null_is_valid(self):
        assert ProposalData.model_validate(_proposal_data_dict(deliverables=None)).deliverables is None

    def test_deliverables_as_empty_list_is_valid(self):
        assert ProposalData.model_validate(_proposal_data_dict(deliverables=[])).deliverables == []


# ---------------------------------------------------------------------------
# B3 — ProposalData model_dump() round-trip
# ---------------------------------------------------------------------------

class TestB3ProposalDataRoundTrip:
    """model_dump() output must reconstruct to an identical model — no data lost."""

    def test_full_round_trip(self):
        original = ProposalData(**_proposal_data_dict())
        restored = ProposalData(**original.model_dump())
        assert restored == original

    def test_round_trip_preserves_none_fields(self):
        original = ProposalData(vendor_name="Test")
        restored = ProposalData(**original.model_dump())
        assert restored.total_cost is None
        assert restored.deliverables is None

    def test_exclude_none_dump_still_validates(self):
        """model_dump(exclude_none=True) is used in risk_agent — result must still parse."""
        original = ProposalData(**_proposal_data_dict())
        dumped = original.model_dump(exclude_none=True)
        restored = ProposalData.model_validate(dumped)
        assert restored.vendor_name == original.vendor_name
        assert restored.deliverables == original.deliverables

    def test_exclude_none_dump_omits_none_fields(self):
        """Verifies exclude_none=True actually drops nulls so we don't over-send to LLM."""
        original = ProposalData(vendor_name="Only Name")
        dumped = original.model_dump(exclude_none=True)
        assert "total_cost" not in dumped
        assert "deliverables" not in dumped
        assert dumped["vendor_name"] == "Only Name"


# ---------------------------------------------------------------------------
# B4 — Risk LLM list → RiskFlag construction
# ---------------------------------------------------------------------------

class TestB4RiskFlagConstruction:
    """risk_agent.analyze() does [RiskFlag(**f) for f in parse_llm_json(raw)].
    Every failure mode the LLM can produce must be caught here.
    """

    def test_valid_risk_flag(self):
        flag = RiskFlag(**_risk_flag_dict())
        assert flag.severity == "HIGH"
        assert flag.policy_excerpt is None

    def test_all_valid_severity_literals(self):
        for severity in ("HIGH", "MEDIUM", "LOW"):
            assert RiskFlag(**_risk_flag_dict(severity=severity)).severity == severity

    def test_invalid_severity_raises(self):
        """LLM returns 'CRITICAL' or lowercase — must raise, not silently store."""
        for bad in ("CRITICAL", "SEVERE", "high", "medium", "low", ""):
            with pytest.raises(ValidationError):
                RiskFlag(**_risk_flag_dict(severity=bad))

    def test_missing_required_clause_raises(self):
        data = _risk_flag_dict()
        del data["clause"]
        with pytest.raises(ValidationError):
            RiskFlag(**data)

    def test_missing_required_explanation_raises(self):
        data = _risk_flag_dict()
        del data["explanation"]
        with pytest.raises(ValidationError):
            RiskFlag(**data)

    def test_missing_required_recommendation_raises(self):
        data = _risk_flag_dict()
        del data["recommendation"]
        with pytest.raises(ValidationError):
            RiskFlag(**data)

    def test_missing_required_policy_reference_raises(self):
        data = _risk_flag_dict()
        del data["policy_reference"]
        with pytest.raises(ValidationError):
            RiskFlag(**data)

    def test_list_construction_mimics_risk_agent(self):
        """Exact pattern used in risk_agent.analyze()."""
        raw_flags = [
            _risk_flag_dict(severity="HIGH"),
            _risk_flag_dict(severity="MEDIUM"),
            _risk_flag_dict(severity="LOW"),
        ]
        flags = [RiskFlag(**f) for f in raw_flags]
        assert [f.severity for f in flags] == ["HIGH", "MEDIUM", "LOW"]

    def test_empty_list_is_valid(self):
        assert [RiskFlag(**f) for f in []] == []

    def test_round_trip_via_model_dump(self):
        original = RiskFlag(**_risk_flag_dict())
        assert RiskFlag(**original.model_dump()) == original


# ---------------------------------------------------------------------------
# B5 — ProposalState model_dump() → ProposalState(**p) round-trip
#       This is exactly what memo_node and _run_pipeline do.
# ---------------------------------------------------------------------------

class TestB5ProposalStateRoundTrip:
    """ProposalState.model_dump() → ProposalState(**dict) must correctly reconstruct
    all nested Pydantic models (ProposalData, RiskFlag, ScoreCard, DimensionScore).
    """

    def _full_state(self) -> ProposalState:
        return ProposalState(
            filename="test.txt",
            extracted=ProposalData(**_proposal_data_dict()),
            risks=[RiskFlag(**_risk_flag_dict()), RiskFlag(**_risk_flag_dict(severity="LOW"))],
            scores=ScoreCard(**_scorecard_dict(overall=70.0)),
            error=None,
        )

    def test_full_round_trip_preserves_nested_models(self):
        original = self._full_state()
        restored = ProposalState(**original.model_dump())

        assert restored.filename == "test.txt"
        assert restored.extracted.vendor_name == "TestVendor"
        assert restored.extracted.deliverables == ["Implementation plan", "Training"]
        assert len(restored.risks) == 2
        assert restored.risks[0].severity == "HIGH"
        assert restored.risks[1].severity == "LOW"
        assert restored.scores.overall == 70.0
        assert restored.scores.platform_functionality.score == 7.0

    def test_round_trip_error_no_scores(self):
        """Extraction failed — error is set, everything else None."""
        original = ProposalState(
            filename="failed.txt",
            error="Extraction failed: ChromaDB unavailable",
        )
        restored = ProposalState(**original.model_dump())
        assert restored.error == "Extraction failed: ChromaDB unavailable"
        assert restored.scores is None
        assert restored.extracted is None

    def test_round_trip_risk_error_with_scores(self):
        """Risk failed but scoring proceeded — both error and scores must survive."""
        original = ProposalState(
            filename="partial.txt",
            extracted=ProposalData(vendor_name="Test"),
            risks=None,
            scores=ScoreCard(**_scorecard_dict(overall=60.0)),
            error="Risk analysis failed: policy file missing",
        )
        restored = ProposalState(**original.model_dump())
        assert restored.scores.overall == 60.0
        assert restored.risks is None
        assert "policy file missing" in restored.error

    def test_dimension_score_nested_type_survives(self):
        """Each DimensionScore must reconstruct as a DimensionScore, not a plain dict."""
        original = self._full_state()
        restored = ProposalState(**original.model_dump())
        dim = restored.scores.platform_functionality
        assert isinstance(dim, DimensionScore)
        assert dim.score == 7.0
        assert dim.rationale == "Test rationale."

    def test_memo_node_list_reconstruction_pattern(self):
        """Exact pattern used in memo_node:
        all_proposals = [ProposalState(**p) for p in state['proposals']]
        """
        dumped_list = [self._full_state().model_dump() for _ in range(3)]
        reconstructed = [ProposalState(**p) for p in dumped_list]

        assert len(reconstructed) == 3
        for p in reconstructed:
            assert p.scores is not None
            assert p.extracted is not None
            assert isinstance(p.scores.risk_level, DimensionScore)


# ---------------------------------------------------------------------------
# B6 — invoke_llm_cached return → memo_agent.write() return type contract
# ---------------------------------------------------------------------------

class TestB6MemoAgentReturnType:
    """memo_agent.write() must always return str.

    invoke_llm_cached returns llm.invoke(...).content, which is normally str
    but can be a list of content block dicts with Anthropic's API.
    memo_agent passes this value directly to the caller without normalizing it.
    """

    def _sample_proposals(self):
        return [
            ProposalState(
                filename="test.txt",
                extracted=ProposalData(vendor_name="TestVendor"),
                scores=ScoreCard(**_scorecard_dict(overall=70.0)),
            )
        ]

    def test_returns_str_when_llm_returns_str(self):
        from agents.memo_agent import MemoAgent
        agent = MemoAgent()
        with patch("agents.memo_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = "# Recommendation\n\nChoose TestVendor."
            result = agent.write(self._sample_proposals())

        assert isinstance(result, str), (
            f"memo_agent.write() must return str, got {type(result).__name__}"
        )

    def test_returns_str_when_llm_returns_list_content_blocks(self):
        """Anthropic multi-part content block response must be normalized to str."""
        from agents.memo_agent import MemoAgent
        agent = MemoAgent()
        with patch("agents.memo_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = [
                {"type": "text", "text": "# Recommendation\n\nChoose TestVendor."}
            ]
            result = agent.write(self._sample_proposals())

        assert isinstance(result, str), (
            f"memo_agent.write() must normalize list content to str, "
            f"got {type(result).__name__}. "
            f"Fix: normalize invoke_llm_cached output before returning."
        )
        assert "Recommendation" in result


# ---------------------------------------------------------------------------
# B7 — _compute_overall scale must match the rubric declaration
# ---------------------------------------------------------------------------

class TestB7ScoringScale:
    """The scoring rubric injected into the LLM system prompt states:
        'Scale: 0-10 per dimension.'
        'Maximum possible overall score is 10.0.'
        'A perfect vendor scores 10.0. No vendor can score above 10.0.'

    _compute_overall must produce overall in [0.0, 10.0], not [0.0, 100.0].
    """

    def _make_agent(self):
        from agents.scoring_agent import ScoringAgent
        with patch("tools.context_loader.load_context_bundle") as mock_bundle:
            mock_bundle.return_value = {
                "scoring_rubric_lms": "rubric",
                "rfp_criteria_lms": _MOCK_CRITERIA,
            }
            return ScoringAgent(bundle_id="lms")

    def _uniform_scores(self, score: float) -> dict:
        return {field: {"score": score, "rationale": "."} for field in _ALL_SCORECARD_FIELDS}

    def test_perfect_score_equals_ten(self):
        """All dimensions at 10.0 → overall must be 10.0, not 100.0."""
        agent = self._make_agent()
        with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = json.dumps(self._uniform_scores(10.0))
            scorecard = agent.score(ProposalData(vendor_name="Perfect"), [])

        assert scorecard.overall == pytest.approx(10.0), (
            f"Rubric declares max score 10.0, got {scorecard.overall}. "
            f"_compute_overall has an extra ×10 multiplier — remove it."
        )

    def test_zero_score_equals_zero(self):
        agent = self._make_agent()
        with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = json.dumps(self._uniform_scores(0.0))
            scorecard = agent.score(ProposalData(vendor_name="Worst"), [])

        assert scorecard.overall == 0.0

    def test_overall_never_exceeds_ten(self):
        agent = self._make_agent()
        with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = json.dumps(self._uniform_scores(10.0))
            scorecard = agent.score(ProposalData(vendor_name="Test"), [])

        assert scorecard.overall <= 10.0, (
            f"overall={scorecard.overall} exceeds rubric maximum of 10.0"
        )

    def test_out_of_range_dimension_score_is_clamped(self):
        """LLM returns dimension score > 10 — must be clamped before reaching ScoreCard.

        Without clamping, a single score of 15 produces overall > 10, violating the
        rubric contract even though _compute_overall itself is correct.
        """
        from agents.scoring_agent import _parse_score_value
        assert _parse_score_value(15) == 10.0, (
            "_parse_score_value(15) returned 15.0 — values above 10 must be clamped to 10.0"
        )
        assert _parse_score_value(10.5) == 10.0
        assert _parse_score_value(100) == 10.0

    def test_negative_dimension_score_is_clamped(self):
        """LLM returns negative score — must be clamped to 0.0."""
        from agents.scoring_agent import _parse_score_value
        assert _parse_score_value(-1) == 0.0, (
            "_parse_score_value(-1) returned -1.0 — negative values must be clamped to 0.0"
        )
        assert _parse_score_value(-0.1) == 0.0

    def test_overall_clamped_when_llm_returns_out_of_range_scores(self):
        """End-to-end: LLM returns 15 on all dimensions → overall must still be ≤ 10."""
        agent = self._make_agent()
        with patch("agents.scoring_agent.invoke_llm_cached") as mock_invoke:
            mock_invoke.return_value = json.dumps(self._uniform_scores(15.0))
            scorecard = agent.score(ProposalData(vendor_name="Test"), [])

        assert scorecard.overall <= 10.0, (
            f"overall={scorecard.overall} — out-of-range dimension scores must be clamped "
            f"so the weighted sum cannot exceed 10.0"
        )
        for field in _ALL_SCORECARD_FIELDS:
            assert getattr(scorecard, field).score <= 10.0, (
                f"{field}.score={getattr(scorecard, field).score} exceeds 10.0"
            )

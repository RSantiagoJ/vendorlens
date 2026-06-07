"""
ScoringAgent — Day 3

Scores a vendor proposal against RFP evaluation criteria using:
  - Claude Haiku 3.5 — mechanical scoring task; 4x faster than Sonnet
  - Rubric and weights loaded from data/context_bundle/ at runtime

How it works:
  1. Load scoring rubric and RFP criteria from context_bundle/.
  2. Inject both into the system prompt so the LLM has full context.
  3. Pass extracted ProposalData + risk flag summary to the LLM.
  4. LLM returns JSON with a score + rationale per dimension.
  5. Compute weighted overall in Python using weights parsed from the
     rfp_criteria file — never hardcoded in this module.
"""

import json
import re

from dotenv import load_dotenv

load_dotenv()

from graph.state import DimensionScore, ProposalData, RiskFlag, ScoreCard
from tools.context_loader import load_context_bundle
from tools.llm_factory import invoke_llm_cached, load_prompt, make_haiku_llm, parse_llm_json

# Structural mapping: rfp_criteria dimension names → ScoreCard field names.
# Weights for each dimension come from the rfp_criteria context bundle file.
_CRITERIA_TO_SCORECARD: dict[str, str] = {
    "core_lms_functionality": "platform_functionality",
    "accessibility_compliance": "accessibility_compliance",
    "integration_interoperability": "integration_capability",
    "pricing_and_licensing": "pricing_transparency",
    "security_and_compliance": "security_and_compliance",
    "support_and_training": "support_and_training",
    "enterprise_readiness": "enterprise_readiness",
    "innovation_roadmap": "innovation_roadmap",
    "risk_level": "risk_level",
}

_SCORECARD_FIELDS = list(_CRITERIA_TO_SCORECARD.values())


def _parse_weights(criteria_text: str) -> dict[str, float]:
    """Extract dimension weights from rfp_criteria_lms.txt content.

    Matches lines like: "core_lms_functionality         weight: 0.20"
    Returns a dict keyed by ScoreCard field name, e.g. {"platform_functionality": 0.20}.
    """
    weights: dict[str, float] = {}
    for criteria_name, scorecard_field in _CRITERIA_TO_SCORECARD.items():
        match = re.search(rf"{re.escape(criteria_name)}\s+weight:\s+([\d.]+)", criteria_text)
        if match:
            weights[scorecard_field] = float(match.group(1))
    return weights


def _parse_score_value(val) -> float:
    """Safely convert a score value (string, float, int, None) to a float between 0.0 and 10.0."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip().lower()
    if not s or s in ("n/a", "na", "none", "null", "unknown"):
        return 0.0

    if "/" in s:
        try:
            numerator = s.split("/")[0].strip()
            return float(numerator)
        except (ValueError, IndexError):
            pass

    try:
        # Extract leading number if present (e.g. "8.5 overall")
        match = re.search(r"^\d+(?:\.\d+)?", s)
        if match:
            return float(match.group(0))
        return float(s)
    except ValueError:
        return 0.0


class ScoringAgent:
    def __init__(self, bundle_id: str = "lms"):
        bundle = load_context_bundle(bundle_id)
        # Find criteria and rubric by prefix — works for any bundle naming
        rubric = bundle.get(next((k for k in bundle if k.startswith("scoring_rubric")), ""), "")
        criteria = bundle.get(next((k for k in bundle if k.startswith("rfp_criteria")), ""), "")

        base_prompt = load_prompt("scoring_agent")
        self.system_prompt = (
            f"{base_prompt}\n\n"
            f"--- SCORING RUBRIC ---\n{rubric}\n\n"
            f"--- RFP EVALUATION CRITERIA ---\n{criteria}"
        )

        self._weights = _parse_weights(criteria)
        if len(self._weights) != 9:
            raise RuntimeError(
                f"Expected 9 dimension weights from rfp_criteria file, "
                f"got {len(self._weights)}: {self._weights}"
            )

        self.llm = make_haiku_llm(cache=True)
        self.llm_name = "Claude Haiku 3.5"

    def _compute_overall(self, dim_scores: dict[str, float]) -> float:
        """Weighted average using weights parsed from rfp_criteria_lms.txt."""
        return round(
            sum(dim_scores[field] * self._weights[field] for field in _SCORECARD_FIELDS), 1
        )

    def score(self, proposal_data: ProposalData, risk_flags: list[RiskFlag]) -> ScoreCard:
        """Score a vendor proposal across all RFP dimensions.

        Args:
            proposal_data: Populated ProposalData from ExtractionAgent.
            risk_flags:    list[RiskFlag] from RiskAgent.

        Returns:
            ScoreCard with per-dimension scores and a weighted overall.
        """
        high_count = sum(1 for f in risk_flags if f.severity == "HIGH")
        risk_summary = json.dumps(
            [{"clause": f.clause, "severity": f.severity} for f in risk_flags],
        )

        raw = invoke_llm_cached(
            self.llm,
            self.system_prompt,
            f"Extracted contract data:\n{proposal_data.model_dump_json(exclude_none=True)}\n\n"
            f"Risk flags from Risk Agent:\n{risk_summary}\n\n"
            f"HIGH severity risk count: {high_count}\n\n"
            "Score this proposal on all 9 dimensions. Return JSON only.",
        )
        data = parse_llm_json(raw)

        for field in _SCORECARD_FIELDS:
            if field not in data:
                data[field] = {"score": 0.0, "rationale": "Score not provided by LLM."}
            else:
                raw_val = data[field].get("score")
                data[field]["score"] = _parse_score_value(raw_val)

        dim_scores = {field: data[field]["score"] for field in _SCORECARD_FIELDS}
        return ScoreCard(
            **{field: DimensionScore(**data[field]) for field in _SCORECARD_FIELDS},
            overall=self._compute_overall(dim_scores),
        )

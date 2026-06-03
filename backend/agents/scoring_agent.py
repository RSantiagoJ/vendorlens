"""
ScoringAgent — Day 3

Scores a vendor proposal against RFP evaluation criteria using:
  - Gemini 3.5 Flash (primary, free tier) via LangChain
  - Claude Sonnet 4.6 (fallback) via LangChain
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
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage

BASE_DIR = Path(__file__).parent.parent
PROMPTS_PATH = BASE_DIR / "prompts.yaml"

# Structural mapping: rfp_criteria dimension names → ScoreCard field names.
# The weights for each dimension come from the rfp_criteria context bundle file.
_CRITERIA_TO_SCORECARD: dict[str, str] = {
    "core_lms_functionality": "platform_functionality",
    "accessibility_compliance": "accessibility_compliance",
    "integration_interoperability": "integration_capability",
    "pricing_and_licensing": "pricing_transparency",
    "security_and_compliance": "security_and_compliance",
    "support_and_training": "support_and_training",
    "enterprise_readiness": "enterprise_readiness",
    "risk_level": "risk_level",
}

_SCORECARD_FIELDS = list(_CRITERIA_TO_SCORECARD.values())


def _load_prompt(role: str) -> str:
    with open(PROMPTS_PATH, "r") as f:
        return yaml.safe_load(f)[role]["system"]


def _parse_weights(criteria_text: str) -> dict[str, float]:
    """Extract dimension weights from rfp_criteria_lms.txt content.

    Matches lines like: "core_lms_functionality         weight: 0.20"
    Returns a dict keyed by ScoreCard field name, e.g. {"platform_functionality": 0.20}.
    """
    weights: dict[str, float] = {}
    for criteria_name, scorecard_field in _CRITERIA_TO_SCORECARD.items():
        pattern = rf"{re.escape(criteria_name)}\s+weight:\s+([\d.]+)"
        match = re.search(pattern, criteria_text)
        if match:
            weights[scorecard_field] = float(match.group(1))
    return weights


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences that some models add despite instructions."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        end = -1 if lines[-1].strip() == "```" else len(lines)
        raw = "\n".join(lines[1:end])
    return raw.strip()


class ScoringAgent:
    def __init__(self):
        from tools.context_loader import load_context_bundle

        bundle = load_context_bundle()
        rubric = bundle.get("scoring_rubric_lms", "")
        criteria = bundle.get("rfp_criteria_lms", "")

        base_prompt = _load_prompt("scoring_agent")
        self.system_prompt = (
            f"{base_prompt}\n\n"
            f"--- SCORING RUBRIC ---\n{rubric}\n\n"
            f"--- RFP EVALUATION CRITERIA ---\n{criteria}"
        )

        self._weights = _parse_weights(criteria)
        if len(self._weights) != 8:
            raise RuntimeError(
                f"Expected 8 dimension weights from rfp_criteria_lms.txt, "
                f"got {len(self._weights)}: {self._weights}"
            )

        from tools.llm_factory import make_llm  # noqa: PLC0415
        self.llm, self.llm_name = make_llm()

    def _compute_overall(self, dim_scores: dict[str, float]) -> float:
        """Weighted average using weights parsed from rfp_criteria_lms.txt."""
        total = sum(dim_scores[field] * self._weights[field] for field in _SCORECARD_FIELDS)
        return round(total, 1)

    def score(self, proposal_data: "ProposalData", risk_flags: list) -> "ScoreCard":
        """Score a vendor proposal across all RFP dimensions.

        Args:
            proposal_data: Populated ProposalData from ExtractionAgent.
            risk_flags:    list[RiskFlag] from RiskAgent.

        Returns:
            ScoreCard with per-dimension scores and a weighted overall.
        """
        from graph.state import DimensionScore, RiskFlag, ScoreCard

        high_count = sum(
            1 for f in risk_flags
            if isinstance(f, RiskFlag) and f.severity == "HIGH"
        )

        extracted_json = proposal_data.model_dump_json(indent=2)
        risk_summary = json.dumps(
            [{"clause": f.clause, "severity": f.severity} for f in risk_flags],
            indent=2,
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Extracted contract data:\n{extracted_json}\n\n"
                    f"Risk flags from Risk Agent:\n{risk_summary}\n\n"
                    f"HIGH severity risk count: {high_count}\n\n"
                    "Score this proposal on all 8 dimensions. Return JSON only."
                )
            ),
        ]
        response = self.llm.invoke(messages)

        content = response.content
        if isinstance(content, list):
            raw = "".join(
                part["text"] if isinstance(part, dict) else str(part)
                for part in content
            )
        else:
            raw = content

        data = json.loads(_strip_fences(raw))

        dim_scores = {field: float(data[field]["score"]) for field in _SCORECARD_FIELDS}
        overall = self._compute_overall(dim_scores)

        return ScoreCard(
            platform_functionality=DimensionScore(**data["platform_functionality"]),
            accessibility_compliance=DimensionScore(**data["accessibility_compliance"]),
            integration_capability=DimensionScore(**data["integration_capability"]),
            pricing_transparency=DimensionScore(**data["pricing_transparency"]),
            security_and_compliance=DimensionScore(**data["security_and_compliance"]),
            support_and_training=DimensionScore(**data["support_and_training"]),
            enterprise_readiness=DimensionScore(**data["enterprise_readiness"]),
            risk_level=DimensionScore(**data["risk_level"]),
            overall=overall,
        )

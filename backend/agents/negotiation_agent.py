"""
NegotiationAgent — Day 15

Generates a per-vendor negotiation brief after scoring is complete.
Uses Claude Haiku 3.5 — structured output, one batched call for all vendors.

Input:  list[ProposalState] with extracted, risks, and scores populated.
Output: list[NegotiationBrief] — one brief per scoreable vendor.

Each brief contains:
  - overall_approach: tone/posture to open with
  - priority_tactics: 3–5 highest-leverage negotiation moves
  - red_lines: non-negotiables (walk away if unmet)
  - concessions_to_offer: what the university can give to get movement
  - batna: best alternative (references competitor scores)
"""

import json
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from graph.state import NegotiationBrief, NegotiationTactic, ProposalState
from tools.llm_factory import invoke_llm_cached, load_prompt, make_haiku_llm, parse_llm_json


class NegotiationAgent:
    def __init__(self):
        self.system_prompt = load_prompt("negotiation_agent")
        self.llm = make_haiku_llm(cache=True)

    def plan(self, proposals: list[ProposalState]) -> list[NegotiationBrief]:
        """Generate negotiation briefs for all scoreable vendors.

        Args:
            proposals: All ProposalState objects from the pipeline.
                       Failed proposals (scores=None) are skipped.

        Returns:
            list[NegotiationBrief] — one per scoreable vendor.
        """
        good = [p for p in proposals if p.scores is not None]
        if not good:
            return []

        proposal_data = [
            {
                "vendor_name": p.extracted.vendor_name if p.extracted else p.filename,
                "overall_score": p.scores.overall,
                "scores": {
                    k: v["score"] if isinstance(v, dict) else v
                    for k, v in p.scores.model_dump().items()
                    if k != "overall"
                },
                "extracted": p.extracted.model_dump(exclude_none=True) if p.extracted else {},
                "high_risks": [
                    {"clause": r.clause, "explanation": r.explanation, "recommendation": r.recommendation}
                    for r in (p.risks or []) if r.severity == "HIGH"
                ],
                "all_risk_count": len(p.risks or []),
            }
            for p in good
        ]

        raw = invoke_llm_cached(
            self.llm,
            self.system_prompt,
            f"Vendor evaluation data:\n{json.dumps(proposal_data)}\n\n"
            "Generate negotiation briefs. Return JSON array only.",
        )

        if isinstance(raw, list):
            raw = "".join(
                part["text"] if isinstance(part, dict) else str(part) for part in raw
            )

        data = parse_llm_json(raw)
        if not isinstance(data, list):
            data = [data]

        briefs = []
        for item in data:
            try:
                tactics = [NegotiationTactic(**t) for t in item.get("priority_tactics", [])]
                brief = NegotiationBrief(
                    vendor_name=item["vendor_name"],
                    overall_approach=item["overall_approach"],
                    priority_tactics=tactics,
                    red_lines=item.get("red_lines", []),
                    concessions_to_offer=item.get("concessions_to_offer", []),
                    batna=item.get("batna", ""),
                )
                briefs.append(brief)
            except Exception:
                logger.exception("[negotiation] failed to parse brief for item: %s", item)

        logger.info("[negotiation] generated %d briefs", len(briefs))
        return briefs

"""
RiskAgent — Day 3

Evaluates extracted ProposalData against procurement policy using:
  - _policy_lookup from tools/mcp_server.py (keyword-scored policy search)
  - Claude Sonnet 4.6 with Anthropic prompt caching

How it works:
  1. Run five targeted policy_lookup queries at init time to pull the most
     relevant policy sections for each risk category (security, data,
     contract terms, SLA, IP). Policy context is constant across all
     proposals, so it is folded into the system prompt once at init.
  2. The combined system prompt (base + policy context) is cached by
     Anthropic after the first vendor call — vendors 2 and 3 pay ~10% of
     the normal input token cost for that portion.
  3. LLM returns a JSON array of risk flags; parse into list[RiskFlag].

policy_excerpt is populated by the LLM when the policy context contains
a verbatim passage that triggered the flag. Null if no specific text found.
"""

import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from graph.state import ProposalData, RiskFlag
from tools.context_loader import get_policy_path
from tools.llm_factory import dedup_ordered, invoke_llm_cached, load_prompt, make_claude_llm, parse_llm_json

# Policy query groups that cover all HIGH/MEDIUM risk categories.
# Each query targets the keyword-scoring logic in _policy_lookup.
_POLICY_QUERIES = [
    "SOC2 Type II ISO 27001 security certification requirements",
    "data processing agreement DPA FERPA data ownership university data",
    "liability cap termination penalty governing law Massachusetts courts",
    "auto-renewal opt-out notice period termination for convenience",
    "incident response disaster recovery IP ownership configurations",
]


class RiskAgent:
    def __init__(self, bundle_id: str = "lms"):
        base_prompt = load_prompt("risk_agent")
        self.llm = make_claude_llm(cache=True)

        from tools.mcp_server import make_policy_lookup
        policy_lookup = make_policy_lookup(get_policy_path(bundle_id))
        policy_context = self._gather_policy_context(policy_lookup)

        # Fold policy context into the system prompt so it gets cached.
        # Every vendor in a run uses the same policy — vendors 2+ hit the cache.
        self.system_prompt = (
            f"{base_prompt}\n\n"
            f"--- PROCUREMENT POLICY CONTEXT ---\n{policy_context}"
        )

    def _gather_policy_context(self, policy_lookup) -> str:
        """Run targeted policy_lookup queries once and deduplicate the results."""
        sections = [
            section.strip()
            for query in _POLICY_QUERIES
            for section in policy_lookup(query).split("\n\n")
        ]
        return "\n\n".join(dedup_ordered(sections))

    def analyze(self, proposal_data: ProposalData) -> list[RiskFlag]:
        """Identify risk flags in a vendor proposal.

        Args:
            proposal_data: Populated ProposalData from ExtractionAgent.

        Returns:
            list[RiskFlag] — may be empty if no risks are found.
        """
        raw = invoke_llm_cached(
            self.llm,
            self.system_prompt,
            f"Extracted contract data:\n{proposal_data.model_dump_json(exclude_none=True)}\n\n"
            "Identify all risks. Return JSON array only.",
        )
        flags = [RiskFlag(**flag) for flag in parse_llm_json(raw)]
        logger.info("[risk] %s: %d flags (%d HIGH, %d MEDIUM, %d LOW)",
            proposal_data.vendor_name, len(flags),
            sum(1 for f in flags if f.severity == "HIGH"),
            sum(1 for f in flags if f.severity == "MEDIUM"),
            sum(1 for f in flags if f.severity == "LOW"),
        )
        return flags

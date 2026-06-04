"""
RiskAgent — Day 3

Evaluates extracted ProposalData against procurement policy using:
  - _policy_lookup from tools/mcp_server.py (keyword-scored policy search)
  - LLM via make_llm() — Gemini 3.5 Flash primary, Claude Sonnet 4.6 fallback

How it works:
  1. Run five targeted policy_lookup queries at init time to pull the most
     relevant policy sections for each risk category (security, data,
     contract terms, SLA, IP). Policy context is constant across all
     proposals, so it is built once and reused.
  2. Pass the extracted proposal JSON + policy context to the LLM.
  3. LLM returns a JSON array of risk flags.
  4. Parse into list[RiskFlag].

policy_excerpt is populated by the LLM when the policy context contains
a verbatim passage that triggered the flag. Null if no specific text found.
"""

from dotenv import load_dotenv

load_dotenv()

from graph.state import ProposalData, RiskFlag
from tools.context_loader import get_policy_path
from tools.llm_factory import dedup_ordered, invoke_llm, load_prompt, make_llm, parse_llm_json

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
        self.system_prompt = load_prompt("risk_agent")
        self.llm, _ = make_llm()

        from tools.mcp_server import make_policy_lookup
        policy_lookup = make_policy_lookup(get_policy_path(bundle_id))
        self._policy_context = self._gather_policy_context(policy_lookup)

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
        raw = invoke_llm(
            self.llm,
            self.system_prompt,
            f"Extracted contract data:\n{proposal_data.model_dump_json(exclude_none=True)}\n\n"
            f"Relevant policy context:\n{self._policy_context}\n\n"
            "Identify all risks. Return JSON array only.",
        )
        return [RiskFlag(**flag) for flag in parse_llm_json(raw)]

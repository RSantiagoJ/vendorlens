"""
RiskAgent — Day 3

Evaluates extracted ProposalData against procurement policy using:
  - _policy_lookup from tools/mcp_server.py (keyword-scored policy search)
  - LLM via make_llm() — Gemini 3.5 Flash primary, Claude Sonnet 4.6 fallback

How it works:
  1. Run five targeted policy_lookup queries to pull the most relevant policy
     sections for each risk category (security, data, contract terms, SLA, IP).
  2. Pass the extracted proposal JSON + policy context to the LLM.
  3. LLM returns a JSON array of risk flags.
  4. Parse into list[RiskFlag].

policy_excerpt is populated by the LLM when the policy context contains
a verbatim passage that triggered the flag. Null if no specific text found.
"""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ProposalData, RiskFlag
from tools.llm_factory import load_prompt, make_llm, parse_llm_json

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
    def __init__(self):
        self.system_prompt = load_prompt("risk_agent")
        self.llm, self.llm_name = make_llm()

        # Deferred to avoid importing MCP server at module load time
        from tools.mcp_server import _policy_lookup
        self._policy_lookup = _policy_lookup

    def _gather_policy_context(self) -> str:
        """Run targeted policy_lookup queries and deduplicate the results."""
        seen: set[str] = set()
        ordered: list[str] = []
        for query in _POLICY_QUERIES:
            for section in self._policy_lookup(query).split("\n\n"):
                section = section.strip()
                if section and section not in seen:
                    seen.add(section)
                    ordered.append(section)
        return "\n\n".join(ordered)

    def analyze(self, proposal_data: ProposalData) -> list[RiskFlag]:
        """Identify risk flags in a vendor proposal.

        Args:
            proposal_data: Populated ProposalData from ExtractionAgent.

        Returns:
            list[RiskFlag] — may be empty if no risks are found.
        """
        policy_context = self._gather_policy_context()
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Extracted contract data:\n{proposal_data.model_dump_json(indent=2)}\n\n"
                    f"Relevant policy context:\n{policy_context}\n\n"
                    "Identify all risks. Return JSON array only."
                )
            ),
        ]
        response = self.llm.invoke(messages)
        return [RiskFlag(**flag) for flag in parse_llm_json(response.content)]

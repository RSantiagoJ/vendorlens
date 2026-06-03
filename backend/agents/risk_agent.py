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

import json
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage

BASE_DIR = Path(__file__).parent.parent
PROMPTS_PATH = BASE_DIR / "prompts.yaml"

# Policy query groups that cover all HIGH/MEDIUM risk categories.
# Each query targets the keyword-scoring logic in _policy_lookup.
_POLICY_QUERIES = [
    "SOC2 Type II ISO 27001 security certification requirements",
    "data processing agreement DPA FERPA data ownership university data",
    "liability cap termination penalty governing law Massachusetts courts",
    "auto-renewal opt-out notice period termination for convenience",
    "incident response disaster recovery IP ownership configurations",
]


def _load_prompt(role: str) -> str:
    with open(PROMPTS_PATH, "r") as f:
        return yaml.safe_load(f)[role]["system"]


class RiskAgent:
    def __init__(self):
        self.system_prompt = _load_prompt("risk_agent")

        # Import here so the module can be imported without MCP overhead
        from tools.mcp_server import _policy_lookup  # noqa: PLC0415
        self._policy_lookup = _policy_lookup

        from tools.llm_factory import make_llm  # noqa: PLC0415
        self.llm, self.llm_name = make_llm()

    def _gather_policy_context(self) -> str:
        """Run targeted policy_lookup queries and deduplicate the results.

        Returns a single string with the top matching policy sections for all
        risk categories. Deduplication ensures the context stays compact.
        """
        seen: set[str] = set()
        ordered: list[str] = []
        for query in _POLICY_QUERIES:
            result = self._policy_lookup(query)
            for section in result.split("\n\n"):
                section = section.strip()
                if section and section not in seen:
                    seen.add(section)
                    ordered.append(section)
        return "\n\n".join(ordered)

    def analyze(self, proposal_data: "ProposalData") -> list:
        """Identify risk flags in a vendor proposal.

        Args:
            proposal_data: Populated ProposalData from ExtractionAgent.

        Returns:
            list[RiskFlag] — may be empty if no risks are found.
        """
        from graph.state import RiskFlag  # noqa: PLC0415

        policy_context = self._gather_policy_context()
        extracted_json = proposal_data.model_dump_json(indent=2)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Extracted contract data:\n{extracted_json}\n\n"
                    f"Relevant policy context:\n{policy_context}\n\n"
                    "Identify all risks. Return JSON array only."
                )
            ),
        ]
        response = self.llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if Claude wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        flags_data: list[dict] = json.loads(raw)
        return [RiskFlag(**flag) for flag in flags_data]

"""
MemoAgent — Day 4

Writes a formal recommendation memo from the full pipeline output.
Uses Claude Sonnet 4.6 directly — memo writing needs nuanced prose.

Takes all ProposalState objects with extracted, risks, and scores populated.
Returns a markdown string ready to display or download.
"""

import json

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ProposalState
from tools.llm_factory import load_prompt, make_claude_llm


class MemoAgent:
    def __init__(self):
        self.system_prompt = load_prompt("memo_agent")
        self.llm = make_claude_llm()

    def write(self, proposals: list[ProposalState]) -> str:
        """Write the recommendation memo from fully-processed proposals.

        Args:
            proposals: All ProposalState objects with extracted, risks, scores set.

        Returns:
            Markdown string containing the full recommendation memo.
        """
        # Only HIGH risks are used by the memo prompt — sending MEDIUM/LOW wastes tokens.
        proposal_data = [
            {
                "filename": p.filename,
                "extracted": p.extracted.model_dump(exclude_none=True) if p.extracted else None,
                "high_risks": [r.model_dump() for r in (p.risks or []) if r.severity == "HIGH"],
                "scores": p.scores.model_dump() if p.scores else None,
            }
            for p in proposals
        ]

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Vendor evaluation data:\n{json.dumps(proposal_data)}\n\n"
                    "Write the recommendation memo. Return markdown only."
                )
            ),
        ]
        response = self.llm.invoke(messages)
        return response.content

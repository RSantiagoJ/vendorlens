"""
ExtractionAgent — Day 2

Extracts structured ProposalData from a vendor proposal document using:
  - LlamaIndex retriever (targeted RAG queries filtered to one vendor file)
  - Claude Sonnet 4.6 via LangChain (auto-traced to LangSmith)

Three query groups cover all ProposalData fields. Chunks are deduplicated
and assembled before the LLM call. Claude returns JSON only; the response
is parsed into a ProposalData Pydantic model.

Null is returned for any field not explicitly stated — no hallucination.

For production use with multi-page PDFs, increase top_k or add more
query groups to ensure full document coverage within context limits.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

BASE_DIR = Path(__file__).parent.parent
PROMPTS_PATH = BASE_DIR / "prompts.yaml"

# Three query groups cover all 30 ProposalData fields without redundant
# embedding API calls. top_k=8 per query captures all chunks in short docs.
_RETRIEVAL_QUERIES = [
    "pricing annual fee cost contract length renewal auto-renewal termination notice liability",
    "security certifications SOC2 ISO27001 DPA data processing agreement incident response data ownership IP intellectual property governing law",
    "platform features social listening analytics accessibility VPAT WCAG SLA uptime support training sandbox integrations campus user roles mobile",
]


def _load_prompt(role: str) -> str:
    with open(PROMPTS_PATH, "r") as f:
        return yaml.safe_load(f)[role]["system"]


class ExtractionAgent:
    def __init__(self, index: VectorStoreIndex):
        self.index = index
        self.system_prompt = _load_prompt("extraction_agent")

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                api_key=anthropic_key,
            )
        else:
            google_key = os.getenv("GOOGLE_API_KEY")
            if not google_key:
                raise ValueError("Neither ANTHROPIC_API_KEY nor GOOGLE_API_KEY is set in environment.")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                google_api_key=google_key,
            )

    def _retrieve_chunks(self, filename: str) -> str:
        """Run three targeted RAG queries for one vendor doc.

        Returns deduplicated chunks joined by a separator so Claude sees
        the full relevant context without repetition.
        """
        filters = MetadataFilters(filters=[
            MetadataFilter(key="file_name", value=filename)
        ])
        retriever = self.index.as_retriever(
            filters=filters,
            similarity_top_k=8,
        )
        seen: set[str] = set()
        ordered: list[str] = []
        for query in _RETRIEVAL_QUERIES:
            for node in retriever.retrieve(query):
                text = node.get_content()
                if text not in seen:
                    seen.add(text)
                    ordered.append(text)
        return "\n\n---\n\n".join(ordered)

    def extract(self, filename: str) -> "ProposalData":
        """Extract structured data from a vendor proposal.

        Args:
            filename: The bare filename, e.g. vendor_a_pulsemedia.txt

        Returns:
            ProposalData with all extractable fields populated and
            null for any field not found in the document.
        """
        # Import here to avoid circular imports when graph/state.py imports agents
        from graph.state import ProposalData  # noqa: PLC0415

        chunks = self._retrieve_chunks(filename)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Relevant chunks from the vendor proposal:\n{chunks}\n\n"
                    "Extract all fields. Return JSON only."
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

        # Strip markdown fences in case the model adds them despite instructions
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        data = json.loads(raw)
        return ProposalData.model_validate(data)

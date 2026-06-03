"""
ExtractionAgent — Day 2

Extracts structured ProposalData from a vendor proposal document using:
  - LlamaIndex retriever (targeted RAG queries filtered to one vendor file)
  - LLM via make_llm() — Gemini 3.5 Flash primary, Claude Sonnet 4.6 fallback

Three query groups cover all ProposalData fields. Chunks are deduplicated
and assembled before the LLM call. The LLM returns JSON only; the response
is parsed into a ProposalData Pydantic model.

Null is returned for any field not explicitly stated — no hallucination.
"""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

from graph.state import ProposalData
from tools.llm_factory import load_prompt, make_llm, parse_llm_json

# Three query groups cover all 30 ProposalData fields without redundant
# embedding API calls. top_k=8 per query captures all chunks in short docs.
_RETRIEVAL_QUERIES = [
    "pricing annual fee cost contract length renewal auto-renewal termination notice liability",
    "security certifications SOC2 ISO27001 DPA data processing agreement incident response data ownership IP intellectual property governing law",
    "platform features social listening analytics accessibility VPAT WCAG SLA uptime support training sandbox integrations campus user roles mobile",
]


class ExtractionAgent:
    def __init__(self, index: VectorStoreIndex):
        self.index = index
        self.system_prompt = load_prompt("extraction_agent")
        self.llm, self.llm_name = make_llm()

    def _retrieve_chunks(self, filename: str) -> str:
        """Run three targeted RAG queries for one vendor doc.

        Returns deduplicated chunks joined by a separator so the LLM sees
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

    def extract(self, filename: str) -> ProposalData:
        """Extract structured data from a vendor proposal.

        Args:
            filename: The bare filename, e.g. vendor_a_blackboard.txt

        Returns:
            ProposalData with all extractable fields populated and
            null for any field not found in the document.
        """
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
        return ProposalData.model_validate(parse_llm_json(response.content))

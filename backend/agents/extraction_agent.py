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

from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from graph.state import ProposalData
from tools.llm_factory import dedup_ordered, invoke_llm, load_prompt, make_llm, parse_llm_json

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
        self.llm, _ = make_llm()

    def _retrieve_chunks(self, filename: str) -> str:
        """Run three targeted RAG queries in parallel for one vendor doc."""
        filters = MetadataFilters(filters=[
            MetadataFilter(key="file_name", value=filename)
        ])
        retriever = self.index.as_retriever(
            filters=filters,
            similarity_top_k=8,
        )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def run_query(query: str) -> list[str]:
            return [node.get_content() for node in retriever.retrieve(query)]

        with ThreadPoolExecutor(max_workers=len(_RETRIEVAL_QUERIES)) as pool:
            results = pool.map(run_query, _RETRIEVAL_QUERIES)

        chunks = [chunk for batch in results for chunk in batch]
        return "\n\n---\n\n".join(dedup_ordered(chunks))

    def extract(self, filename: str) -> ProposalData:
        """Extract structured data from a vendor proposal.

        Args:
            filename: The bare filename, e.g. blackboard.txt

        Returns:
            ProposalData with all extractable fields populated and
            null for any field not found in the document.
        """
        chunks = self._retrieve_chunks(filename)
        raw = invoke_llm(
            self.llm,
            self.system_prompt,
            f"Relevant chunks from the vendor proposal:\n{chunks}\n\nExtract all fields. Return JSON only.",
        )
        return ProposalData.model_validate(parse_llm_json(raw))

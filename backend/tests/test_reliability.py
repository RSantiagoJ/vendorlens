"""
test_reliability.py — System reliability tests for live-demo safety.

Covers failure modes that would be visible to an audience:

  R1  _get_pipeline() is safe under concurrent calls — only one pipeline built
  R2  _ingest_file() skips duplicate filenames — no double-vector pollution
  R3  Full mock pipeline produces well-formed output structure
"""

import threading
from unittest.mock import MagicMock, patch

import pytest

from graph.state import ProposalData, ProposalState, RiskFlag, ScoreCard, DimensionScore


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _dim(score: float = 7.0) -> dict:
    return {"score": score, "rationale": "Test."}


def _scorecard():
    fields = [
        "platform_functionality", "accessibility_compliance", "integration_capability",
        "pricing_transparency", "security_and_compliance", "support_and_training",
        "enterprise_readiness", "innovation_roadmap", "risk_level",
    ]
    return ScoreCard(**{f: DimensionScore(**_dim()) for f in fields}, overall=7.0)


# ---------------------------------------------------------------------------
# R1 — _get_pipeline() concurrent safety
# ---------------------------------------------------------------------------

class TestR1PipelineConcurrency:
    """_get_pipeline() must build at most one pipeline per bundle_id
    even when multiple threads call it simultaneously.
    """

    def test_single_pipeline_built_under_concurrency(self):
        """Simulate 5 concurrent requests for the same bundle.
        Only one pipeline should be constructed.
        """
        from api.main import _pipelines
        _pipelines.clear()

        build_count = 0
        built_pipeline = MagicMock()

        def counting_build(bundle_id="lms"):
            nonlocal build_count
            import time
            time.sleep(0.05)  # exaggerate the race window
            build_count += 1
            return built_pipeline

        results = []
        errors = []

        def call_get_pipeline():
            try:
                from api.main import _get_pipeline
                with patch("api.main.build_pipeline", side_effect=counting_build):
                    results.append(_get_pipeline("lms"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_get_pipeline) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Threads raised exceptions: {errors}"
        assert len(results) == 5
        assert all(r is built_pipeline for r in results), (
            "All threads must receive the same pipeline object"
        )
        assert build_count == 1, (
            f"build_pipeline called {build_count} times — expected exactly 1. "
            f"Add a threading.Lock around _get_pipeline to prevent duplicate builds."
        )

        _pipelines.clear()

    def test_different_bundles_get_separate_pipelines(self):
        """lms and payroll bundles must each get their own pipeline."""
        from api.main import _pipelines
        _pipelines.clear()

        lms_pipeline = MagicMock()
        payroll_pipeline = MagicMock()
        call_args = []

        def build_by_bundle(bundle_id="lms"):
            call_args.append(bundle_id)
            return lms_pipeline if bundle_id == "lms" else payroll_pipeline

        with patch("api.main.build_pipeline", side_effect=build_by_bundle):
            from api.main import _get_pipeline
            p1 = _get_pipeline("lms")
            p2 = _get_pipeline("payroll")
            p3 = _get_pipeline("lms")  # cached — must not rebuild

        assert p1 is lms_pipeline
        assert p2 is payroll_pipeline
        assert p3 is lms_pipeline
        assert call_args.count("lms") == 1, "lms pipeline must only be built once"
        assert call_args.count("payroll") == 1

        _pipelines.clear()


# ---------------------------------------------------------------------------
# R2 — _ingest_file() duplicate skip
# ---------------------------------------------------------------------------

class TestR2IngestDeduplication:
    """Uploading the same file twice must not insert duplicate vectors."""

    def _mock_index(self, already_indexed: bool):
        """Return a mock LlamaIndex index whose ChromaDB collection reports
        whether the filename is already present."""
        mock_collection = MagicMock()
        if already_indexed:
            mock_collection.get.return_value = {"ids": ["existing-chunk-id"]}
        else:
            mock_collection.get.return_value = {"ids": []}

        mock_vector_store = MagicMock()
        mock_vector_store._collection = mock_collection

        mock_index = MagicMock()
        mock_index._vector_store = mock_vector_store
        return mock_index, mock_collection

    def test_skips_ingest_when_filename_already_indexed(self):
        """Second upload of same file must not call insert_nodes."""
        from api.main import _ingest_file
        mock_index, mock_collection = self._mock_index(already_indexed=True)

        _ingest_file("blackboard.txt", b"content", mock_index)

        mock_index.insert_nodes.assert_not_called(), (
            "insert_nodes must not be called when filename is already in the index. "
            "Add a duplicate check before inserting."
        )

    def test_ingests_when_filename_not_yet_indexed(self):
        """First upload of a file must proceed normally."""
        from api.main import _ingest_file
        mock_index, mock_collection = self._mock_index(already_indexed=False)

        mock_node = MagicMock()
        with (
            patch("api.main.SimpleDirectoryReader") as mock_reader,
            patch("api.main._splitter") as mock_splitter,
        ):
            mock_doc = MagicMock()
            mock_reader.return_value.load_data.return_value = [mock_doc]
            mock_splitter.get_nodes_from_documents.return_value = [mock_node]

            _ingest_file("newvendor.txt", b"vendor content", mock_index)

        mock_index.insert_nodes.assert_called_once_with([mock_node])

    def test_skips_gracefully_when_collection_check_fails(self):
        """If the duplicate check itself raises, ingest should still proceed."""
        from api.main import _ingest_file
        mock_index, mock_collection = self._mock_index(already_indexed=False)
        mock_collection.get.side_effect = Exception("ChromaDB connection error")

        with (
            patch("api.main.SimpleDirectoryReader") as mock_reader,
            patch("api.main._splitter") as mock_splitter,
        ):
            mock_reader.return_value.load_data.return_value = [MagicMock()]
            mock_splitter.get_nodes_from_documents.return_value = [MagicMock()]

            # Must not raise — a failed dedup check should fall through to ingest
            _ingest_file("vendor.txt", b"content", mock_index)


# ---------------------------------------------------------------------------
# R3 — Full mock pipeline output structure
# ---------------------------------------------------------------------------

class TestR3PipelineOutputStructure:
    """The pipeline result dict must always have the exact keys the API and
    frontend depend on, regardless of which vendors succeed or fail.
    """

    REQUIRED_TOP_KEYS = {"status", "proposals", "memo", "error"}
    REQUIRED_PROPOSAL_KEYS = {"filename", "extracted", "risks", "scores", "error"}

    def _run(self, state, mock_retrieve, mock_extract, mock_risk, mock_score, mock_memo):
        import json
        from tests.test_mock_pipeline import (
            MOCK_EXTRACTION_BLACKBOARD, MOCK_RISKS_BLACKBOARD, MOCK_SCORING_VALID,
            _build_graph,
        )
        mock_retrieve.return_value = "chunks"
        mock_extract.return_value = json.dumps(MOCK_EXTRACTION_BLACKBOARD)
        mock_risk.return_value = json.dumps(MOCK_RISKS_BLACKBOARD)
        mock_score.return_value = json.dumps(MOCK_SCORING_VALID)
        mock_memo.return_value = "Recommendation memo."
        return _build_graph().invoke(state)

    @patch("graph.pipeline.load_index")
    @patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
    @patch("agents.extraction_agent.invoke_llm_cached")
    @patch("agents.risk_agent.invoke_llm_cached")
    @patch("agents.scoring_agent.invoke_llm_cached")
    @patch("agents.memo_agent.MemoAgent.write")
    def test_result_has_required_top_level_keys(
        self, mock_memo, mock_score, mock_risk, mock_extract, mock_retrieve, mock_load_index
    ):
        mock_load_index.return_value = MagicMock()
        from tests.test_mock_pipeline import _state
        result = self._run(
            _state("blackboard.txt"),
            mock_retrieve, mock_extract, mock_risk, mock_score, mock_memo,
        )
        for key in self.REQUIRED_TOP_KEYS:
            assert key in result, f"Missing top-level key '{key}' in pipeline result"

    @patch("graph.pipeline.load_index")
    @patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
    @patch("agents.extraction_agent.invoke_llm_cached")
    @patch("agents.risk_agent.invoke_llm_cached")
    @patch("agents.scoring_agent.invoke_llm_cached")
    @patch("agents.memo_agent.MemoAgent.write")
    def test_each_proposal_has_required_keys(
        self, mock_memo, mock_score, mock_risk, mock_extract, mock_retrieve, mock_load_index
    ):
        mock_load_index.return_value = MagicMock()
        from tests.test_mock_pipeline import _state
        result = self._run(
            _state("blackboard.txt", "canvas.txt"),
            mock_retrieve, mock_extract, mock_risk, mock_score, mock_memo,
        )
        for proposal in result["proposals"]:
            for key in self.REQUIRED_PROPOSAL_KEYS:
                assert key in proposal, (
                    f"Missing key '{key}' in proposal dict — "
                    f"frontend will break if this key is absent"
                )

    @patch("graph.pipeline.load_index")
    @patch("agents.extraction_agent.ExtractionAgent._retrieve_chunks")
    @patch("agents.extraction_agent.invoke_llm_cached")
    @patch("agents.risk_agent.invoke_llm_cached")
    @patch("agents.scoring_agent.invoke_llm_cached")
    @patch("agents.memo_agent.MemoAgent.write")
    def test_overall_score_within_rubric_bounds(
        self, mock_memo, mock_score, mock_risk, mock_extract, mock_retrieve, mock_load_index
    ):
        """overall must be in [0, 10] — the rubric maximum."""
        mock_load_index.return_value = MagicMock()
        from tests.test_mock_pipeline import _state
        result = self._run(
            _state("blackboard.txt"),
            mock_retrieve, mock_extract, mock_risk, mock_score, mock_memo,
        )
        for p in result["proposals"]:
            if p.get("scores"):
                overall = p["scores"]["overall"]
                assert 0.0 <= overall <= 10.0, (
                    f"overall={overall} out of rubric bounds [0, 10]"
                )

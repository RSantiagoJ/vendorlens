"""
test_persistence.py — DB persistence layer tests.

Tests are written against the interface before implementation (TDD).
All tests use mocks — no real database or API keys required.

Boundaries:
  P1  AnalysisRun model stores the correct fields from a completed job
  P2  _persist_run() calls session.add() with the right data on success
  P3  _persist_run() is skipped gracefully when DATABASE_URL is not set
  P4  _persist_run() logs a warning and does not raise on DB error
  P5  GET /jobs/{job_id} returns result from in-memory store when available
  P6  GET /jobs/{job_id} falls back to DB when job is not in memory
  P7  GET /jobs/{job_id} returns 404 when not in memory or DB
"""

import pytest
from unittest.mock import MagicMock, patch

from graph.state import ProposalData, ProposalState, RiskFlag, ScoreCard, DimensionScore
from api.models import AnalysisResult, ProposalResult


# ---------------------------------------------------------------------------
# Shared builders
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


def _proposal_result(filename: str = "test.txt") -> ProposalResult:
    return ProposalResult(
        filename=filename,
        vendor_name="TestVendor",
        extracted=ProposalData(vendor_name="TestVendor", total_cost="$1M"),
        risks=[RiskFlag(
            clause="Liability cap",
            severity="HIGH",
            explanation="Too low.",
            recommendation="Negotiate.",
            policy_reference="Section 4",
        )],
        scores=_scorecard(),
        error=None,
    )


def _analysis_result(job_id: str = "test-job-123") -> AnalysisResult:
    return AnalysisResult(
        job_id=job_id,
        bundle_id="lms",
        proposals=[_proposal_result("blackboard.txt"), _proposal_result("canvas.txt")],
        memo="# Recommendation\n\nChoose Canvas.",
        status="done",
        error=None,
    )


# ---------------------------------------------------------------------------
# P1 — AnalysisRun model stores correct fields
# ---------------------------------------------------------------------------

class TestP1AnalysisRunModel:
    def test_model_stores_required_fields(self):
        from db.models import AnalysisRun
        result = _analysis_result()
        run = AnalysisRun(
            job_id=result.job_id,
            bundle_id=result.bundle_id,
            status=result.status,
            memo=result.memo,
            error=result.error,
            proposals=[p.model_dump() for p in result.proposals],
        )
        assert run.job_id == "test-job-123"
        assert run.bundle_id == "lms"
        assert run.status == "done"
        assert run.memo == "# Recommendation\n\nChoose Canvas."
        assert run.error is None
        assert len(run.proposals) == 2

    def test_proposals_stored_as_list_of_dicts(self):
        from db.models import AnalysisRun
        result = _analysis_result()
        run = AnalysisRun(
            job_id=result.job_id,
            bundle_id=result.bundle_id,
            status=result.status,
            proposals=[p.model_dump() for p in result.proposals],
        )
        assert isinstance(run.proposals, list)
        assert isinstance(run.proposals[0], dict)
        assert run.proposals[0]["filename"] == "blackboard.txt"

    def test_proposals_can_be_reconstructed_as_proposal_state(self):
        """Stored proposals must round-trip back to ProposalState."""
        from db.models import AnalysisRun
        result = _analysis_result()
        run = AnalysisRun(
            job_id=result.job_id,
            bundle_id=result.bundle_id,
            status=result.status,
            proposals=[p.model_dump() for p in result.proposals],
        )
        restored = [ProposalState(**p) for p in run.proposals]
        assert restored[0].scores.overall == 7.0
        assert restored[0].risks[0].severity == "HIGH"

    def test_error_job_stored_correctly(self):
        from db.models import AnalysisRun
        run = AnalysisRun(
            job_id="failed-job",
            bundle_id="lms",
            status="error",
            error="All vendors failed processing",
            proposals=[],
        )
        assert run.status == "error"
        assert run.error is not None
        assert run.memo is None


# ---------------------------------------------------------------------------
# P2 — _persist_run() calls session correctly on success
# ---------------------------------------------------------------------------

class TestP2PersistRun:
    def test_persist_run_adds_analysis_run_to_session(self):
        from api.main import _persist_run
        mock_session = MagicMock()

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-123", "lms", _analysis_result("job-123"))

        mock_session.add.assert_called_once()
        run = mock_session.add.call_args[0][0]

        from db.models import AnalysisRun
        assert isinstance(run, AnalysisRun)
        assert run.job_id == "job-123"
        assert run.bundle_id == "lms"
        assert run.status == "done"

    def test_persist_run_commits_session(self):
        from api.main import _persist_run
        mock_session = MagicMock()

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-123", "lms", _analysis_result("job-123"))

        mock_session.commit.assert_called_once()

    def test_persist_run_closes_session(self):
        from api.main import _persist_run
        mock_session = MagicMock()

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-123", "lms", _analysis_result("job-123"))

        mock_session.close.assert_called_once()

    def test_persist_run_stores_proposals_as_dicts(self):
        from api.main import _persist_run
        mock_session = MagicMock()

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-123", "lms", _analysis_result("job-123"))

        run = mock_session.add.call_args[0][0]
        assert isinstance(run.proposals, list)
        assert all(isinstance(p, dict) for p in run.proposals)


# ---------------------------------------------------------------------------
# P3 — _persist_run() skipped when DATABASE_URL is not configured
# ---------------------------------------------------------------------------

class TestP3NoDatabaseUrl:
    def test_persist_run_skips_when_no_session(self):
        from api.main import _persist_run
        with patch("api.main.get_db_session", return_value=None):
            # Must not raise
            _persist_run("job-123", "lms", _analysis_result("job-123"))


# ---------------------------------------------------------------------------
# P4 — _persist_run() logs warning and does not raise on DB error
# ---------------------------------------------------------------------------

class TestP4DBError:
    def test_persist_run_does_not_raise_on_db_error(self):
        from api.main import _persist_run
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB connection lost")

        with patch("api.main.get_db_session", return_value=mock_session):
            # Must not raise — pipeline result is still valid even if persistence fails
            _persist_run("job-123", "lms", _analysis_result("job-123"))

    def test_persist_run_closes_session_even_on_error(self):
        from api.main import _persist_run
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB connection lost")

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-123", "lms", _analysis_result("job-123"))

        mock_session.close.assert_called_once()

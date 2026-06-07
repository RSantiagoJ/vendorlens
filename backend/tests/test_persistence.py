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


# ---------------------------------------------------------------------------
# P8 — error runs are persisted (not only success runs)
# ---------------------------------------------------------------------------

class TestP8ErrorRunPersistence:
    """When _run_pipeline hits the except block the error result must be
    persisted so it survives a restart and appears in the audit trail.
    """

    def test_persist_run_accepts_error_status(self):
        """An AnalysisResult with status='error' and no proposals must persist cleanly."""
        from api.main import _persist_run
        from api.models import AnalysisResult
        mock_session = MagicMock()

        error_result = AnalysisResult(
            job_id="err-job-001",
            bundle_id="lms",
            proposals=[],
            status="error",
            error="Pipeline crashed: ChromaDB unavailable",
        )

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("err-job-001", "lms", error_result)

        mock_session.add.assert_called_once()
        run = mock_session.add.call_args[0][0]
        assert run.status == "error"
        assert run.error == "Pipeline crashed: ChromaDB unavailable"
        assert run.proposals == []

    def test_error_path_in_run_pipeline_calls_persist(self):
        """_run_pipeline's except block must call _persist_run with error status."""
        from api.main import _run_pipeline, _jobs
        import uuid

        job_id = str(uuid.uuid4())
        _jobs[job_id] = {"status": "pending", "events": [], "result": None, "error": None}

        with (
            patch("api.main.load_index", side_effect=Exception("ChromaDB down")),
            patch("api.main._persist_run") as mock_persist,
        ):
            _run_pipeline(job_id, [("blackboard.txt", b"content")], "lms")

        mock_persist.assert_called_once()
        _, _, persisted_result = mock_persist.call_args[0]
        assert persisted_result.status == "error"
        assert persisted_result.error is not None

        _jobs.pop(job_id, None)


# ---------------------------------------------------------------------------
# P9 — _jobs TTL eviction after successful persistence
# ---------------------------------------------------------------------------

class TestP9JobEviction:
    """Completed jobs must be scheduled for eviction from _jobs after
    persistence succeeds. Eviction prevents unbounded memory growth.
    """

    def test_eviction_scheduled_after_persist(self):
        """After _persist_run succeeds, a timer must be scheduled to evict the job."""
        from api.main import _persist_run, _schedule_eviction, _jobs
        import uuid

        job_id = str(uuid.uuid4())
        _jobs[job_id] = {"status": "done", "events": [], "result": None, "error": None}

        with (
            patch("api.main.get_db_session", return_value=MagicMock()),
            patch("api.main._schedule_eviction") as mock_evict,
        ):
            _persist_run(job_id, "lms", _analysis_result(job_id))

        mock_evict.assert_called_once_with(job_id)
        _jobs.pop(job_id, None)

    def test_schedule_eviction_removes_job_after_delay(self):
        """_schedule_eviction must call _jobs.pop after the configured TTL."""
        from api.main import _jobs, _schedule_eviction
        import uuid
        import time

        job_id = str(uuid.uuid4())
        _jobs[job_id] = {"status": "done", "events": [], "result": None, "error": None}

        with patch("api.main.threading.Timer") as mock_timer:
            _schedule_eviction(job_id)

        mock_timer.assert_called_once()
        ttl = mock_timer.call_args[0][0]
        evict_fn = mock_timer.call_args[0][1]

        assert 60 <= ttl <= 3600, f"TTL {ttl}s is unreasonable"

        # Simulate the timer firing — job must be removed
        evict_fn()
        assert job_id not in _jobs, "Job must be evicted from _jobs after TTL"

    def test_eviction_is_safe_if_job_already_gone(self):
        """_schedule_eviction timer firing on an already-removed job must not raise."""
        from api.main import _jobs, _schedule_eviction

        with patch("api.main.threading.Timer") as mock_timer:
            _schedule_eviction("nonexistent-job")

        evict_fn = mock_timer.call_args[0][1]
        evict_fn()  # must not raise KeyError


# ---------------------------------------------------------------------------
# P10 — rfp_name stored on AnalysisRun
# ---------------------------------------------------------------------------

class TestP10RfpName:
    """AnalysisRun must store a human-readable label (rfp_name) derived
    from the bundle so runs are identifiable without looking up the UUID.
    """

    def test_analysis_run_accepts_rfp_name(self):
        """AnalysisRun model must have an rfp_name column."""
        from db.models import AnalysisRun
        run = AnalysisRun(
            job_id="rfp-test-001",
            bundle_id="lms",
            status="done",
            rfp_name="LMS Platform Evaluation",
        )
        assert run.rfp_name == "LMS Platform Evaluation"

    def test_persist_run_sets_rfp_name_from_bundle_label(self):
        """_persist_run must auto-populate rfp_name from the bundle label."""
        from api.main import _persist_run
        mock_session = MagicMock()

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-rfp-001", "lms", _analysis_result("job-rfp-001"))

        run = mock_session.add.call_args[0][0]
        assert run.rfp_name is not None, (
            "rfp_name must be set — 'LMS' is the label for bundle 'lms'"
        )
        assert run.rfp_name == "LMS"

    def test_rfp_name_none_for_unknown_bundle(self):
        """Unknown bundle_id must not crash — rfp_name falls back to None."""
        from api.main import _persist_run
        mock_session = MagicMock()

        result = _analysis_result("job-unknown")
        result = result.model_copy(update={"bundle_id": "unknown_bundle"})

        with patch("api.main.get_db_session", return_value=mock_session):
            _persist_run("job-unknown", "unknown_bundle", result)

        run = mock_session.add.call_args[0][0]
        assert run.rfp_name is None


# ---------------------------------------------------------------------------
# P5 — GET /jobs/{job_id} returns from in-memory store when available
# P6 — GET /jobs/{job_id} falls back to DB when job is not in memory
# P7 — GET /jobs/{job_id} returns 404 when found in neither
# ---------------------------------------------------------------------------

class TestP5P6P7GetJobEndpoint:
    """Tests for the GET /jobs/{job_id} endpoint using FastAPI's test client."""

    def _client(self):
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def test_returns_result_from_memory(self):
        """P5: job is still in _jobs — no DB call needed."""
        from api.main import _jobs
        job_id = "mem-job-001"
        result = _analysis_result(job_id)
        _jobs[job_id] = {
            "status": "done",
            "events": [],
            "result": result.model_dump(),
            "error": None,
        }

        try:
            response = self._client().get(f"/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert data["status"] == "done"
            assert len(data["proposals"]) == 2
        finally:
            _jobs.pop(job_id, None)

    def test_falls_back_to_db_when_not_in_memory(self):
        """P6: job not in _jobs — endpoint queries DB and reconstructs AnalysisResult."""
        from api.main import _jobs
        from db.models import AnalysisRun
        job_id = "db-job-001"
        result = _analysis_result(job_id)

        mock_run = AnalysisRun(
            job_id=job_id,
            bundle_id="lms",
            status="done",
            memo=result.memo,
            error=None,
            proposals=[p.model_dump() for p in result.proposals],
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_run

        _jobs.pop(job_id, None)  # ensure not in memory

        with patch("api.main.get_db_session", return_value=mock_session):
            response = self._client().get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "done"
        assert data["memo"] == result.memo

    def test_returns_404_when_not_in_memory_or_db(self):
        """P7: job exists nowhere — must return 404, not 500."""
        from api.main import _jobs
        job_id = "missing-job-999"
        _jobs.pop(job_id, None)

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch("api.main.get_db_session", return_value=mock_session):
            response = self._client().get(f"/jobs/{job_id}")

        assert response.status_code == 404

    def test_returns_404_when_db_unavailable_and_not_in_memory(self):
        """No DATABASE_URL and job not in memory — must 404 cleanly."""
        from api.main import _jobs
        job_id = "no-db-job-999"
        _jobs.pop(job_id, None)

        with patch("api.main.get_db_session", return_value=None):
            response = self._client().get(f"/jobs/{job_id}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# P11 — GET /jobs/{job_id}/progress — polling progress endpoint
# ---------------------------------------------------------------------------

class TestP11ProgressEndpoint:
    """Tests for the GET /jobs/{job_id}/progress endpoint used by polling clients.

    This endpoint replaces the SSE stream for clients that cannot maintain a
    long-lived connection (e.g. App Runner terminates SSE at 120s). It returns
    the current stage and partial data at any point during the pipeline run.
    """

    def _client(self):
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def _inject_job(self, job_id: str, status: str, events: list, result=None, error=None):
        from api.main import _jobs
        _jobs[job_id] = {
            "status": status,
            "events": events,
            "result": result,
            "error": error,
        }

    def test_returns_404_for_unknown_job(self):
        """Unknown job_id must return 404."""
        from api.main import _jobs
        job_id = "unknown-progress-job"
        _jobs.pop(job_id, None)
        response = self._client().get(f"/jobs/{job_id}/progress")
        assert response.status_code == 404

    def test_returns_pending_stage_when_no_events(self):
        """A job that just started has no events — stage must be 'pending'."""
        job_id = "progress-pending-001"
        self._inject_job(job_id, "pending", [])
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["stage"] == "pending"
            assert data["vendors"] == []
            assert data["total_risks"] is None
            assert data.get("result") is None
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

    def test_returns_current_stage_from_events(self):
        """Stage is derived from the most recent event type in the events list."""
        job_id = "progress-stage-001"
        events = [
            {"type": "extracting", "data": {"vendors": ["canvas.txt", "blackboard.txt"]}},
            {"type": "risk", "data": {"status": "risk"}},
        ]
        self._inject_job(job_id, "pending", events)
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            assert response.status_code == 200
            data = response.json()
            assert data["stage"] == "risk"
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

    def test_returns_vendor_names_from_extracting_event(self):
        """Vendor names must be extracted from the 'extracting' event payload."""
        job_id = "progress-vendors-001"
        events = [
            {"type": "extracting", "data": {"vendors": ["canvas.txt", "blackboard.txt"]}},
        ]
        self._inject_job(job_id, "pending", events)
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            data = response.json()
            assert data["vendors"] == ["canvas.txt", "blackboard.txt"]
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

    def test_returns_total_risks_from_scoring_event(self):
        """total_risks must be populated once the scoring event is emitted."""
        job_id = "progress-risks-001"
        events = [
            {"type": "extracting", "data": {"vendors": ["canvas.txt"]}},
            {"type": "risk", "data": {"status": "risk"}},
            {"type": "scoring", "data": {"status": "scoring", "total_risks": 7}},
        ]
        self._inject_job(job_id, "pending", events)
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            data = response.json()
            assert data["total_risks"] == 7
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

    def test_includes_result_when_job_done(self):
        """When job is done, the response must include the full result payload."""
        job_id = "progress-done-001"
        result = _analysis_result(job_id).model_dump()
        events = [
            {"type": "extracting", "data": {"vendors": ["canvas.txt"]}},
            {"type": "done", "data": result},
        ]
        self._inject_job(job_id, "done", events, result=result)
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            data = response.json()
            assert data["status"] == "done"
            assert data["stage"] == "done"
            assert data["result"] is not None
            assert data["result"]["job_id"] == job_id
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

    def test_result_absent_when_job_pending(self):
        """No 'result' key in response body while job is still running."""
        job_id = "progress-noresult-001"
        self._inject_job(job_id, "pending", [{"type": "extracting", "data": {"vendors": []}}])
        try:
            response = self._client().get(f"/jobs/{job_id}/progress")
            data = response.json()
            assert data.get("result") is None
        finally:
            from api.main import _jobs; _jobs.pop(job_id, None)

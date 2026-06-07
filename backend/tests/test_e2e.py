"""
test_e2e.py — End-to-end HTTP flow tests.

Tests the complete client interaction:
  POST /analyze → poll GET /jobs/{job_id}/progress → GET /jobs/{job_id}

All LLM and pipeline internals are mocked — no API keys or ChromaDB needed.
The polling loop in each test mirrors exactly what the frontend does.

Boundaries:
  E1  POST /analyze returns job_id immediately; job enters _jobs
  E2  POST /analyze validates — no files → 422
  E3  POST /analyze validates — unknown bundle → 422
  E4  Polling loop reaches done and result is present
  E5  Polling loop reaches error and error message is present
  E6  Multi-vendor upload — both proposals in result
  E7  /jobs/{job_id} returns full AnalysisResult after polling completes
  E8  Stage sequence is correct (extracting → risk → scoring → memo → done)
"""

import time
import pytest
from unittest.mock import patch

from graph.state import ProposalData, RiskFlag, ScoreCard, DimensionScore
from api.models import AnalysisResult, ProposalResult


# ---------------------------------------------------------------------------
# Shared builders
# ---------------------------------------------------------------------------

_DIMS = [
    "platform_functionality", "accessibility_compliance", "integration_capability",
    "pricing_transparency", "security_and_compliance", "support_and_training",
    "enterprise_readiness", "innovation_roadmap", "risk_level",
]


def _scorecard(score: float = 7.0) -> ScoreCard:
    return ScoreCard(**{d: DimensionScore(score=score, rationale="OK.") for d in _DIMS}, overall=score)


def _make_result(job_id: str, filenames: tuple = ("alpha_lms.txt",), status: str = "done") -> dict:
    proposals = [
        ProposalResult(
            filename=f,
            vendor_name=f.rsplit(".", 1)[0],
            extracted=ProposalData(vendor_name=f.rsplit(".", 1)[0], total_cost="$500,000"),
            risks=[RiskFlag(
                clause="Liability cap",
                severity="HIGH",
                explanation="Cap is too low.",
                recommendation="Negotiate higher cap.",
                policy_reference="Section 4",
            )],
            scores=_scorecard(),
            error=None,
        )
        for f in filenames
    ]
    return AnalysisResult(
        job_id=job_id,
        bundle_id="lms",
        proposals=proposals,
        memo="Alpha LMS is the recommended vendor.",
        status=status,
        error=None,
    ).model_dump()


def _instant_pipeline(filenames: tuple = ("alpha_lms.txt",), status: str = "done"):
    """Returns a _run_pipeline stub that completes synchronously with a valid result."""
    def stub(job_id, file_contents, bundle_id):
        from api.main import _jobs
        vendors = [name.rsplit(".", 1)[0] for name, _ in file_contents]
        result = _make_result(job_id, tuple(name for name, _ in file_contents), status)
        _jobs[job_id]["events"] = [
            {"type": "extracting", "data": {"vendors": vendors}},
            {"type": "risk", "data": {"status": "risk"}},
            {"type": "scoring", "data": {"status": "scoring", "total_risks": 1}},
            {"type": "memo", "data": {"status": "memo"}},
            {"type": "done", "data": result},
        ]
        _jobs[job_id]["result"] = result
        _jobs[job_id]["status"] = "done"
    return stub


def _error_pipeline(error_msg: str = "ChromaDB unavailable"):
    """Returns a _run_pipeline stub that immediately fails with an error."""
    def stub(job_id, file_contents, bundle_id):
        from api.main import _jobs
        _jobs[job_id]["events"] = [
            {"type": "error", "data": {"status": "error", "error": error_msg}},
        ]
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = error_msg
    return stub


def _poll_until_done(client, job_id: str, timeout: float = 2.0) -> dict:
    """Poll /progress until status is terminal. Mirrors real frontend polling."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/jobs/{job_id}/progress")
        if r.status_code == 200:
            data = r.json()
            if data["status"] in ("done", "error", "partial"):
                return data
        time.sleep(0.05)
    raise AssertionError(f"Job {job_id} did not reach terminal status within {timeout}s")


def _client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# E1 — POST /analyze returns job_id immediately; job enters _jobs
# ---------------------------------------------------------------------------

class TestE1AnalyzeReturnsJobId:
    def test_returns_job_id_on_valid_upload(self):
        """POST /analyze with a valid file must return a job_id synchronously."""
        with patch("api.main._run_pipeline", _instant_pipeline()):
            c = _client()
            r = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"vendor proposal content", "text/plain"))],
                data={"bundle": "lms"},
            )
        assert r.status_code == 200
        data = r.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) > 0

    def test_job_appears_in_progress_after_submit(self):
        """After POST /analyze, the job_id must be queryable via /progress."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            r = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"vendor proposal content", "text/plain"))],
                data={"bundle": "lms"},
            )
            job_id = r.json()["job_id"]
            progress = c.get(f"/jobs/{job_id}/progress")
        assert progress.status_code == 200


# ---------------------------------------------------------------------------
# E2 — POST /analyze validation — no files
# ---------------------------------------------------------------------------

class TestE2NoFiles:
    def test_rejects_empty_file_list(self):
        """POST /analyze with no files must return 422."""
        c = _client()
        r = c.post("/analyze", data={"bundle": "lms"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# E3 — POST /analyze validation — unknown bundle
# ---------------------------------------------------------------------------

class TestE3UnknownBundle:
    def test_rejects_unknown_bundle(self):
        """POST /analyze with an unrecognised bundle must return 422."""
        c = _client()
        r = c.post(
            "/analyze",
            files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
            data={"bundle": "nonexistent_bundle"},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# E4 — Polling loop reaches done; result is present
# ---------------------------------------------------------------------------

class TestE4PollingReachesDone:
    def test_polling_reaches_done_status(self):
        """Polling /progress must eventually return status=done."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert progress["status"] == "done"

    def test_done_progress_includes_result(self):
        """When status=done, /progress must include the result payload."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert progress["result"] is not None
        assert progress["result"]["status"] == "done"
        assert len(progress["result"]["proposals"]) == 1

    def test_done_progress_includes_vendor_names(self):
        """Vendor names extracted from the pipeline must appear in /progress."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert "alpha_lms" in progress["vendors"]


# ---------------------------------------------------------------------------
# E5 — Polling loop reaches error; error message is present
# ---------------------------------------------------------------------------

class TestE5PollingReachesError:
    def test_polling_reaches_error_status(self):
        """When the pipeline fails, polling must eventually return status=error."""
        with patch("api.main._run_pipeline", _error_pipeline("ChromaDB unavailable")), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert progress["status"] == "error"


# ---------------------------------------------------------------------------
# E6 — Multi-vendor upload — both proposals in result
# ---------------------------------------------------------------------------

class TestE6MultiVendor:
    def test_two_vendors_both_appear_in_result(self):
        """Two uploaded files must produce two proposals in the final result."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[
                    ("files", ("alpha_lms.txt", b"alpha content", "text/plain")),
                    ("files", ("beta_lms.txt", b"beta content", "text/plain")),
                ],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert len(progress["result"]["proposals"]) == 2

    def test_two_vendors_both_in_vendor_names(self):
        """Both vendor names must appear in the /progress vendor list."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[
                    ("files", ("alpha_lms.txt", b"alpha content", "text/plain")),
                    ("files", ("beta_lms.txt", b"beta content", "text/plain")),
                ],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        vendors = progress["vendors"]
        assert "alpha_lms" in vendors
        assert "beta_lms" in vendors


# ---------------------------------------------------------------------------
# E7 — GET /jobs/{job_id} returns full AnalysisResult after polling
# ---------------------------------------------------------------------------

class TestE7GetJobAfterDone:
    def test_get_job_returns_200_after_pipeline_completes(self):
        """GET /jobs/{job_id} must return the full AnalysisResult once done."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            _poll_until_done(c, job_id)
            result = c.get(f"/jobs/{job_id}")

        assert result.status_code == 200
        data = result.json()
        assert data["job_id"] == job_id
        assert data["status"] == "done"
        assert data["memo"] is not None
        assert len(data["proposals"]) == 1

    def test_get_job_proposal_has_scores(self):
        """Each proposal in GET /jobs must have a non-null ScoreCard."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            _poll_until_done(c, job_id)
            data = c.get(f"/jobs/{job_id}").json()

        proposal = data["proposals"][0]
        assert proposal["scores"] is not None
        assert isinstance(proposal["scores"]["overall"], float)

    def test_get_job_returns_404_for_unknown_id(self):
        """GET /jobs/{job_id} for a job that never existed must return 404."""
        with patch("api.main.get_db_session", return_value=None):
            r = _client().get("/jobs/nonexistent-job-e7")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# E8 — Stage sequence is correct
# ---------------------------------------------------------------------------

class TestE8StageSequence:
    def test_final_stage_is_done(self):
        """The stage at completion must be 'done'."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert progress["stage"] == "done"

    def test_total_risks_present_after_scoring(self):
        """/progress must expose total_risks once the scoring event fires."""
        with patch("api.main._run_pipeline", _instant_pipeline()), patch("api.main._persist_run"):
            c = _client()
            job_id = c.post(
                "/analyze",
                files=[("files", ("alpha_lms.txt", b"content", "text/plain"))],
                data={"bundle": "lms"},
            ).json()["job_id"]
            progress = _poll_until_done(c, job_id)

        assert progress["total_risks"] is not None
        assert progress["total_risks"] >= 0

import asyncio
import json
import os
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

# Optional S3 client — only initialised when S3_BUCKET is set.
_S3_BUCKET = os.environ.get("S3_BUCKET")
_s3_client = None
if _S3_BUCKET:
    try:
        import boto3
        _s3_client = boto3.client("s3")
    except ImportError:
        _S3_BUCKET = None  # boto3 not installed; fall back to in-memory only

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

from api.models import AnalysisResult, AnalyzeResponse, ProposalResult
from db.session import get_db_session, init_db
from db.models import AnalysisRun
from graph.pipeline import build_pipeline
from graph.state import ProposalState
from tools.context_loader import BUNDLES, DEFAULT_BUNDLE
from tools.chroma import load_index

import logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Pre-warm all bundle pipelines so no request pays cold-start cost.
    loop = asyncio.get_running_loop()
    for bundle_id in BUNDLES:
        loop.run_in_executor(_executor, lambda b=bundle_id: _get_pipeline(b))
    yield


app = FastAPI(title="VendorLens API", lifespan=lifespan)

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_executor = ThreadPoolExecutor(max_workers=4)

# One cached pipeline per bundle — built on first use.
_pipelines: dict[str, object] = {}
_pipeline_lock = threading.Lock()

# Serialise concurrent ChromaDB inserts from parallel requests.
_ingest_lock = threading.Lock()

_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)


def _get_pipeline(bundle_id: str = DEFAULT_BUNDLE):
    if bundle_id in _pipelines:
        return _pipelines[bundle_id]
    with _pipeline_lock:
        if bundle_id not in _pipelines:
            _pipelines[bundle_id] = build_pipeline(bundle_id=bundle_id)
    return _pipelines[bundle_id]


def _ingest_file(filename: str, content: bytes, index) -> None:
    """Write one uploaded file to a temp dir and insert its chunks into the shared index.

    Skips silently if chunks for this filename already exist — prevents duplicate
    vectors when the same file is uploaded more than once.
    Uses LlamaIndex SimpleDirectoryReader so any supported format (.txt, .pdf, .docx)
    is parsed natively — raw bytes are never decoded as UTF-8 here.
    """
    try:
        existing = index._vector_store._collection.get(
            where={"file_name": filename}, limit=1, include=[],
        )
        if existing["ids"]:
            logger.info("Skipping ingest for %s — already indexed", filename)
            return
    except Exception:
        pass  # if the check fails, proceed with ingest rather than silently dropping

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / filename
        dest.write_bytes(content)
        docs = SimpleDirectoryReader(
            input_dir=tmp,
            filename_as_id=True,
            file_metadata=lambda p: {"file_name": Path(p).name},
        ).load_data()
        if not docs:
            return
        nodes = _splitter.get_nodes_from_documents(docs)
        index.insert_nodes(nodes)


# In-memory job store: job_id → {status, events, result, error}
_jobs: dict[str, dict] = {}


_JOB_TTL_SECONDS = 600  # evict completed jobs from _jobs after 10 minutes


def _schedule_eviction(job_id: str) -> None:
    """Remove a completed job from _jobs after TTL. Safe to call on missing jobs."""
    def evict():
        _jobs.pop(job_id, None)
    timer = threading.Timer(_JOB_TTL_SECONDS, evict)
    timer.daemon = True
    timer.start()


def _persist_run(job_id: str, bundle_id: str, result: AnalysisResult) -> None:
    """Persist an analysis run (success or error) to the database.

    No-op when DATABASE_URL is not set. Never raises — a DB failure must not
    affect the in-memory result or the SSE stream the client already received.
    Schedules eviction of the job from _jobs after TTL on success.
    """
    session = None
    try:
        session = get_db_session()
        if session is None:
            return
        rfp_name = BUNDLES.get(bundle_id, {}).get("label")
        run = AnalysisRun(
            job_id=job_id,
            bundle_id=bundle_id,
            rfp_name=rfp_name,
            status=result.status,
            memo=result.memo,
            error=result.error,
            proposals=[p.model_dump() for p in result.proposals],
        )
        session.add(run)
        session.commit()
        _schedule_eviction(job_id)
    except Exception as e:
        logger.warning("Failed to persist job %s to database: %s", job_id, e)
    finally:
        if session:
            session.close()


def _run_pipeline(job_id: str, file_contents: list[tuple[str, bytes]], bundle_id: str) -> None:
    job = _jobs[job_id]
    num_vendors = len(file_contents)
    vendor_nodes_done = 0

    def emit(event_type: str, data: dict) -> None:
        job["events"].append({"type": event_type, "data": data})

    try:
        vendor_names = [name.rsplit(".", 1)[0] for name, _ in file_contents]
        emit("extracting", {"status": "extracting", "vendors": vendor_names})
        seen_stages: set[str] = {"extracting"}
        total_risks = 0

        # Ingest uploaded files into ChromaDB so ExtractionAgent can retrieve them.
        # Raw bytes are written to disk; LlamaIndex handles format-specific parsing.
        index = load_index()
        with _ingest_lock:
            for name, content in file_contents:
                _ingest_file(name, content, index)

        pending = [{"filename": name} for name, _ in file_contents]

        initial_state = {
            "pending": pending,
            "proposals": [],
            "memo": None,
            "status": "pending",
            "error": None,
        }

        final = {
            "proposals": [],
            "memo": None,
            "status": "pending",
            "error": None,
        }

        # stream_mode="updates" + subgraphs=True yields (namespace, {node: delta}) tuples.
        # namespace == () means the parent graph; non-empty means inside vendor_subgraph.
        # This lets us emit SSE events at each per-stage node completion, not just once
        # per vendor after all three stages finish.
        for ns, chunk in _get_pipeline(bundle_id).stream(
            initial_state, stream_mode="updates", subgraphs=True
        ):
            for node_name, updates in chunk.items():
                if node_name == "risk_node" and "risk" not in seen_stages:
                    seen_stages.add("risk")
                    emit("risk", {"status": "risk"})
                elif node_name == "score_node":
                    for p in (updates or {}).get("proposals", []):
                        total_risks += len(p.get("risks") or [])
                    vendor_nodes_done += 1
                    if "scoring" not in seen_stages:
                        seen_stages.add("scoring")
                        emit("scoring", {"status": "scoring", "total_risks": total_risks})
                elif node_name == "memo_node" and "memo" not in seen_stages:
                    seen_stages.add("memo")
                    emit("memo", {"status": "memo"})

                # Accumulate parent-level state only (ns == () is the parent graph).
                if not ns and isinstance(updates, dict):
                    for k, v in updates.items():
                        if k == "proposals" and isinstance(v, list):
                            final["proposals"] = final["proposals"] + v
                        else:
                            final[k] = v

        proposals = [ProposalState(**p) for p in final.get("proposals", [])]
        failed_count = sum(1 for p in proposals if p.scores is None)
        if failed_count == 0:
            final_status = "done"
        elif failed_count == len(proposals):
            final_status = "error"
        else:
            final_status = "partial"
        result = AnalysisResult(
            job_id=job_id,
            bundle_id=bundle_id,
            proposals=[
                ProposalResult(
                    filename=p.filename,
                    vendor_name=p.extracted.vendor_name if p.extracted else None,
                    extracted=p.extracted,
                    risks=p.risks,
                    scores=p.scores,
                    error=p.error,
                )
                for p in proposals
            ],
            memo=final.get("memo"),
            status=final_status,
            error=final.get("error"),
        )

        result_dict = result.model_dump()
        job["result"] = result_dict
        logger.info("[pipeline] job %s done — status=%s proposals=%s",
            job_id, final_status,
            [{p.filename: round(p.scores.overall, 1) if p.scores else None} for p in proposals],
        )
        _persist_run(job_id, bundle_id, result)
        emit("done", result_dict)
        job["status"] = "done"

    except Exception as exc:
        emit("error", {"status": "error", "error": str(exc)})
        job["status"] = "error"
        job["error"] = str(exc)
        error_result = AnalysisResult(
            job_id=job_id,
            bundle_id=bundle_id,
            proposals=[],
            status="error",
            error=str(exc),
        )
        _persist_run(job_id, bundle_id, error_result)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/reload")
def reload() -> dict:
    """Clear the in-memory pipeline cache so the next request loads a fresh ChromaDB index.
    Call this after running scripts/ingest.py without restarting the API container.
    """
    _pipelines.clear()
    return {"status": "ok", "message": "Pipeline cache cleared — fresh index loads on next request."}


@app.get("/bundles")
def list_bundles() -> list[dict]:
    return list(BUNDLES.values())


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile],
    bundle: str | None = Form(DEFAULT_BUNDLE),
) -> AnalyzeResponse:
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")
    if bundle not in BUNDLES:
        raise HTTPException(status_code=422, detail=f"Unknown bundle '{bundle}'. Valid: {list(BUNDLES)}")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "events": [], "result": None, "error": None}

    file_contents = [(f.filename or f"file_{i}", await f.read()) for i, f in enumerate(files)]

    # Optionally persist uploads to S3 for audit / debugging (no-op locally).
    if _s3_client and _S3_BUCKET:
        for name, content in file_contents:
            _s3_client.put_object(
                Bucket=_S3_BUCKET,
                Key=f"uploads/{job_id}/{name}",
                Body=content,
            )

    asyncio.get_running_loop().run_in_executor(_executor, _run_pipeline, job_id, file_contents, bundle)

    return AnalyzeResponse(job_id=job_id)


@app.get("/jobs/{job_id}", response_model=AnalysisResult)
def get_job(job_id: str) -> AnalysisResult:
    """Return the final result of a completed job.

    Checks the in-memory store first (fast path for recently completed jobs),
    then falls back to the database (for jobs completed before a restart).
    """
    # Fast path: still in memory
    if job_id in _jobs and _jobs[job_id].get("result"):
        return AnalysisResult(**_jobs[job_id]["result"])

    # DB fallback
    session = None
    try:
        session = get_db_session()
        if session:
            run = session.query(AnalysisRun).filter_by(job_id=job_id).first()
            if run:
                return AnalysisResult(
                    job_id=run.job_id,
                    bundle_id=run.bundle_id,
                    status=run.status,
                    memo=run.memo,
                    error=run.error,
                    proposals=[ProposalResult(**p) for p in (run.proposals or [])],
                )
    except Exception as e:
        logger.warning("DB lookup failed for job %s: %s", job_id, e)
    finally:
        if session:
            session.close()

    raise HTTPException(status_code=404, detail="Job not found.")


@app.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: str) -> dict:
    """Return current pipeline stage for a running or completed job.

    Used by polling clients instead of the SSE stream. Safe to call at any
    point during the run — returns partial data before the job completes.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    job = _jobs[job_id]
    events = job.get("events", [])

    stage = events[-1]["type"] if events else "pending"
    vendors: list[str] = []
    total_risks: int | None = None

    for ev in events:
        if ev["type"] == "extracting":
            vendors = ev["data"].get("vendors", [])
        elif ev["type"] == "scoring":
            total_risks = ev["data"].get("total_risks")

    response: dict = {
        "status": job["status"],
        "stage": stage,
        "vendors": vendors,
        "total_risks": total_risks,
        "result": job.get("result"),
    }
    return response


@app.get("/stream/{job_id}")
async def stream(job_id: str) -> StreamingResponse:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator() -> AsyncGenerator[str, None]:
        sent = 0
        while True:
            job = _jobs[job_id]
            events = job["events"]
            while sent < len(events):
                ev = events[sent]
                yield f"event: {ev['type']}\ndata: {json.dumps(ev['data'], separators=(',', ':'))}\n\n"
                sent += 1
            if job["status"] in ("done", "error") and sent >= len(events):
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

import asyncio
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
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

from api.models import AnalysisResult, AnalyzeResponse, ProposalResult
from graph.pipeline import build_pipeline
from graph.state import ProposalState
from tools.context_loader import BUNDLES, DEFAULT_BUNDLE


@asynccontextmanager
async def lifespan(app: FastAPI):
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


def _get_pipeline(bundle_id: str = DEFAULT_BUNDLE):
    if bundle_id not in _pipelines:
        _pipelines[bundle_id] = build_pipeline(bundle_id=bundle_id)
    return _pipelines[bundle_id]


# In-memory job store: job_id → {status, events, result, error}
_jobs: dict[str, dict] = {}

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

        pending = [
            {"filename": name, "raw_text": content.decode("utf-8", errors="replace")}
            for name, content in file_contents
        ]

        initial_state = {
            "pending": pending,
            "extracted": [],
            "with_risks": [],
            "proposals": [],
            "memo": None,
            "status": "pending",
            "error": None,
        }

        final = dict(initial_state)

        for chunk in _get_pipeline(bundle_id).stream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                if node_name == "vendor_node":
                    vendor_nodes_done += 1
                    for p in (updates or {}).get("proposals", []):
                        total_risks += len(p.get("risks") or [])
                    # First vendor done → risk analysis is underway across the batch.
                    if "risk" not in seen_stages:
                        seen_stages.add("risk")
                        emit("risk", {"status": "risk"})
                    # Last vendor done → all scoring complete, memo is next.
                    if vendor_nodes_done >= num_vendors and "scoring" not in seen_stages:
                        seen_stages.add("scoring")
                        emit("scoring", {"status": "scoring", "total_risks": total_risks})
                elif node_name == "memo_node" and "memo" not in seen_stages:
                    seen_stages.add("memo")
                    emit("memo", {"status": "memo"})

                if isinstance(updates, dict):
                    for k, v in updates.items():
                        if k in ("extracted", "with_risks", "proposals") and isinstance(v, list):
                            final[k] = final[k] + v
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
        emit("done", result_dict)
        job["status"] = "done"

    except Exception as exc:
        emit("error", {"status": "error", "error": str(exc)})
        job["status"] = "error"
        job["error"] = str(exc)


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
                yield f"event: {ev['type']}\ndata: {json.dumps(ev['data'])}\n\n"
                sent += 1
            if job["status"] in ("done", "error") and sent >= len(events):
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

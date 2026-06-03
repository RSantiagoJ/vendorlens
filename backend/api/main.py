import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.models import AnalysisResult, AnalyzeResponse, ProposalResult
from graph.pipeline import build_pipeline
from graph.state import ProposalState

app = FastAPI(title="VendorLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline is expensive to boot (loads ChromaDB + all agents) — initialize once.
_pipeline = None
_executor = ThreadPoolExecutor(max_workers=4)


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


# In-memory job store: job_id → {status, events, result, error}
# Each event: {type: str, data: dict}
_jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pipeline runner (sync — called from ThreadPoolExecutor)
# ---------------------------------------------------------------------------

# Map node names to the SSE event emitted the first time that node fires.
_NODE_EVENT = {
    "extraction_node": "extracting",
    "risk_node": "risk",
    "scoring_node": "scoring",
    "memo_node": "memo",
}


def _run_pipeline(job_id: str, file_contents: list[tuple[str, bytes]]) -> None:
    job = _jobs[job_id]

    def emit(event_type: str, data: dict) -> None:
        job["events"].append({"type": event_type, "data": data})

    try:
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

        # Accumulate the final state from per-node update chunks.
        final: dict = {k: v for k, v in initial_state.items()}
        seen_stages: set[str] = set()

        for chunk in _get_pipeline().stream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                # Emit a progress event the first time each stage fires.
                stage_event = _NODE_EVENT.get(node_name)
                if stage_event and stage_event not in seen_stages:
                    seen_stages.add(stage_event)
                    emit(stage_event, {"status": stage_event})

                # Merge updates into final state; operator.add fields accumulate.
                if isinstance(updates, dict):
                    for k, v in updates.items():
                        if k in ("extracted", "with_risks", "proposals") and isinstance(v, list):
                            final[k] = final[k] + v
                        else:
                            final[k] = v

        proposals = [ProposalState(**p) for p in final.get("proposals", [])]
        result = AnalysisResult(
            job_id=job_id,
            proposals=[
                ProposalResult(
                    filename=p.filename,
                    vendor_name=p.extracted.vendor_name if p.extracted else None,
                    extracted=p.extracted,
                    risks=p.risks,
                    scores=p.scores,
                )
                for p in proposals
            ],
            memo=final.get("memo"),
            status="done",
            error=final.get("error"),
        )

        job["result"] = result.model_dump()
        job["status"] = "done"
        emit("done", result.model_dump())

    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)
        emit("error", {"status": "error", "error": str(exc)})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(files: list[UploadFile]) -> AnalyzeResponse:
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "events": [], "result": None, "error": None}

    # Read file bytes eagerly — UploadFile is not thread-safe across await boundaries.
    file_contents = [(f.filename or f"file_{i}", await f.read()) for i, f in enumerate(files)]

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, _run_pipeline, job_id, file_contents)

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

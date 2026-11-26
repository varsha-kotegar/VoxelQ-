"""
Phase 5 — VoxelQ FastAPI service (with persistence)

Run from inference/ (one level above app/):
    uvicorn app.main:app --reload --port 8000

Endpoints:
    POST /videos/start              -> {job_id}
    GET  /videos/{job_id}/status     -> live status (in-memory, fast)
    GET  /videos/{job_id}/metrics    -> historical metrics from Postgres
    WS   /videos/{job_id}/stream     -> sends cached snapshot immediately on
                                         connect (Redis), then live updates
"""

import asyncio
import os
import queue
import threading
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.job_runner import run_job
from app.db import init_db, get_session
from app.models import Metric
from app import cache

app = FastAPI(title="VoxelQ")

_extra_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://voxel-q.vercel.app",
        *_extra_origins,
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs_status: dict = {}
jobs_queues: dict = {}


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}



class StartJobRequest(BaseModel):
    source: str
    polygon: list
    imgsz: int = 640
    conf: float = 0.35
    iou: float = 0.5
    debounce_seconds: float = 0.5
    window_seconds: float = 10.0
    low_capacity: int = 5
    high_capacity: int = 15


@app.post("/videos/start")
def start_video(req: StartJobRequest):
    # Check if any job is currently running
    for jid, info in jobs_status.items():
        if info.get("state") == "running":
            raise HTTPException(
                status_code=400,
                detail="A video processing job is already running. Parallel jobs are disabled to prevent memory overflow."
            )

    job_id = str(uuid.uuid4())
    metrics_queue: "queue.Queue" = queue.Queue()
    jobs_queues[job_id] = metrics_queue

    thread = threading.Thread(
        target=run_job,
        kwargs=dict(
            job_id=job_id,
            source=req.source,
            polygon_points=[tuple(p) for p in req.polygon],
            metrics_queue=metrics_queue,
            status_store=jobs_status,
            imgsz=req.imgsz,
            conf=req.conf,
            iou=req.iou,
            debounce_seconds=req.debounce_seconds,
            window_seconds=req.window_seconds,
            low_capacity=req.low_capacity,
            high_capacity=req.high_capacity,
        ),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id}


@app.get("/videos/{job_id}/status")
def get_status(job_id: str):
    if job_id not in jobs_status:
        return {"error": "unknown job_id"}
    return jobs_status[job_id]


@app.get("/videos/{job_id}/metrics")
def get_metrics(job_id: str, limit: int = 500):
    """Historical metrics from Postgres — works even after server restart,
    as long as the job_id existed before."""
    db = get_session()
    try:
        rows = (
            db.query(Metric)
            .filter(Metric.job_id == job_id)
            .order_by(Metric.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "occupancy": row.occupancy,
                "avg_occupancy": row.avg_occupancy,
                "arrival_rate_per_min": row.arrival_rate_per_min,
                "wait_time_seconds": row.wait_time_seconds,
                "density_band": row.density_band,
            }
            for row in rows
        ]
    finally:
        db.close()


@app.websocket("/videos/{job_id}/stream")
async def stream_video(websocket: WebSocket, job_id: str):
    await websocket.accept()

    # Send whatever we have cached immediately — client doesn't have to wait
    # for the next live frame just to see current state.
    snapshot = cache.get_snapshot(job_id)
    if snapshot:
        await websocket.send_json({"event": "snapshot", **snapshot})

    status = jobs_status.get(job_id)
    is_active = status and status.get("state") in ("pending", "running")

    if job_id not in jobs_queues or not is_active:
        # Job may be from a previous server run or already completed — no live queue,
        # but we already sent the cached snapshot above if one existed.
        await websocket.send_json({"event": "done", "note": "job not active; snapshot only"})
        await websocket.close()
        return

    q = jobs_queues[job_id]
    try:
        while True:
            try:
                payload = q.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

            await websocket.send_json(payload)

            if payload.get("event") in ("done", "error"):
                break

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
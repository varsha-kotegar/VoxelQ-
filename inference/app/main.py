"""
Phase 4 — VoxelQ FastAPI service

Run from inference/ (one level above app/):
    uvicorn app.main:app --reload --port 8000

Endpoints:
    POST /videos/start          -> {job_id}
    GET  /videos/{job_id}/status -> current status + last metrics
    WS   /videos/{job_id}/stream -> live metrics, one JSON message per frame
"""

import queue
import threading
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.job_runner import run_job

app = FastAPI(title="VoxelQ")

# In-memory job state (fine for local/portfolio use; Phase 5 moves durable
# history to Postgres — this stays as the *live* coordination layer, with
# Redis taking over this role once we containerize in Phase 7).
jobs_status: dict = {}
jobs_queues: dict = {}


class StartJobRequest(BaseModel):
    source: str                      # path to video file
    polygon: list                    # [[x1,y1],[x2,y2],...]
    imgsz: int = 640
    conf: float = 0.35
    iou: float = 0.5
    debounce_seconds: float = 0.5
    window_seconds: float = 10.0
    low_capacity: int = 5
    high_capacity: int = 15


@app.post("/videos/start")
def start_video(req: StartJobRequest):
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


@app.websocket("/videos/{job_id}/stream")
async def stream_video(websocket: WebSocket, job_id: str):
    await websocket.accept()

    if job_id not in jobs_queues:
        await websocket.send_json({"event": "error", "message": "unknown job_id"})
        await websocket.close()
        return

    q = jobs_queues[job_id]
    try:
        while True:
            try:
                # non-blocking poll of the thread-safe queue, so we don't
                # block the asyncio event loop waiting on a sync queue.
                payload = q.get_nowait()
            except queue.Empty:
                await _sleep(0.05)
                continue

            await websocket.send_json(payload)

            if payload.get("event") in ("done", "error"):
                break

    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()


async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)

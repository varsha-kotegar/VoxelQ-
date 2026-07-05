"""
Phase 4 — job runner
Wraps the Phase 1-3 pipeline (detector + zone + arrival_filter + estimator)
into a single function that runs in a background THREAD (not asyncio task —
ultralytics inference is synchronous/blocking, so it needs a real OS thread
so it doesn't block FastAPI's event loop).

Communicates with the FastAPI layer via a thread-safe queue.Queue.
"""

import queue
import time
import traceback
from datetime import datetime, timezone

import cv2
from ultralytics import YOLO

from app.zone import Zone
from app.arrival_filter import ArrivalFilter
from app.estimator import WaitTimeEstimator

PERSON_CLASS_ID = 0


def run_job(
    job_id: str,
    source: str,
    polygon_points: list,
    metrics_queue: "queue.Queue",
    status_store: dict,
    imgsz: int = 640,
    conf: float = 0.35,
    iou: float = 0.5,
    debounce_seconds: float = 0.5,
    window_seconds: float = 10.0,
    low_capacity: int = 5,
    high_capacity: int = 15,
):
    """
    Runs synchronously in a background thread. Pushes one metrics dict per
    frame onto metrics_queue. Updates status_store[job_id] throughout so
    GET /videos/{id}/status has something to report even without connecting
    to the WebSocket.
    """
    status_store[job_id] = {"state": "running", "error": None, "last_metrics": None}

    try:
        cap = cv2.VideoCapture(source)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        cap.release()

        model = YOLO("yolov8n.pt")
        zone = Zone(polygon_points)
        arrival_filter = ArrivalFilter(fps=fps, debounce_seconds=debounce_seconds)
        estimator = WaitTimeEstimator(window_seconds=window_seconds, fps=fps,
                                       low_capacity=low_capacity, high_capacity=high_capacity)

        results = model.track(
            source=source, classes=[PERSON_CLASS_ID], imgsz=imgsz, conf=conf, iou=iou,
            tracker="bytetrack.yaml", persist=True, stream=True,
        )

        for r in results:
            track_boxes = {}
            if r.boxes is not None and r.boxes.id is not None:
                ids = r.boxes.id.int().tolist()
                xyxy = r.boxes.xyxy.tolist()
                for tid, box in zip(ids, xyxy):
                    track_boxes[tid] = tuple(box)

            zone_state = zone.update(track_boxes)
            filter_state = arrival_filter.update(zone_state["members"])
            metrics = estimator.update(
                raw_occupancy=zone_state["count"],
                confirmed_enters_this_frame=len(filter_state["confirmed_enters"]),
            )

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "occupancy": zone_state["count"],
                "avg_occupancy": metrics["avg_occupancy"],
                "density_band": metrics["density_band"],
                "arrival_rate_per_min": metrics["arrival_rate_per_min"],
                "wait_time_seconds": metrics["wait_time_seconds"],
            }

            metrics_queue.put(payload)
            status_store[job_id]["last_metrics"] = payload

        status_store[job_id]["state"] = "completed"
        metrics_queue.put({"event": "done"})

    except Exception as e:
        status_store[job_id]["state"] = "error"
        status_store[job_id]["error"] = str(e)
        metrics_queue.put({"event": "error", "message": str(e)})
        traceback.print_exc()

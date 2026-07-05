"""
Phase 5 — job runner with write-through persistence
Same pipeline as Phase 4, now also:
  1. Creates/updates the VideoJob row (lifecycle: pending -> running -> completed/error)
  2. Writes each Metric row to Postgres
  3. Writes the latest snapshot to Redis
  4. Still pushes to the in-memory queue for live WebSocket broadcast

Each background thread gets its OWN DB session (SQLAlchemy sessions are not
thread-safe to share across threads).
"""

import queue
import traceback
from datetime import datetime, timezone

import cv2
from ultralytics import YOLO

from app.zone import Zone
from app.arrival_filter import ArrivalFilter
from app.estimator import WaitTimeEstimator
from app.db import get_session
from app.models import VideoJob, Metric
from app import cache

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
    status_store[job_id] = {"state": "running", "error": None, "last_metrics": None}
    db = get_session()

    try:
        job_row = VideoJob(id=job_id, source=source, status="running",
                            started_at=datetime.now(timezone.utc))
        db.add(job_row)
        db.commit()

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

            # --- write-through: Redis (live) + Postgres (history) + queue (broadcast) ---
            cache.set_snapshot(job_id, payload)

            db.add(Metric(
                job_id=job_id,
                occupancy=payload["occupancy"],
                avg_occupancy=payload["avg_occupancy"],
                arrival_rate_per_min=payload["arrival_rate_per_min"],
                wait_time_seconds=payload["wait_time_seconds"],
                density_band=payload["density_band"],
            ))
            db.commit()

            metrics_queue.put(payload)
            status_store[job_id]["last_metrics"] = payload

        job_row.status = "completed"
        job_row.completed_at = datetime.now(timezone.utc)
        db.commit()

        status_store[job_id]["state"] = "completed"
        metrics_queue.put({"event": "done"})

    except Exception as e:
        db.rollback()
        try:
            job_row.status = "error"
            job_row.error_message = str(e)
            db.commit()
        except Exception:
            pass
        status_store[job_id]["state"] = "error"
        status_store[job_id]["error"] = str(e)
        metrics_queue.put({"event": "error", "message": str(e)})
        traceback.print_exc()

    finally:
        db.close()
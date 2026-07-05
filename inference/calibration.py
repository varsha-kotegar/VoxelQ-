"""
Phase 8 — Calibration
Compares model occupancy against manually-annotated ground truth at
specific frame numbers, reports MAE and MAPE per video.

Workflow:
1. Run the annotated video output from Phase 2 (test_zone.py) or scrub
   through the raw clip.
2. Pick 5-10 frame numbers, pause, and COUNT people in your zone by eye.
3. Fill in calibration_config.json with {frame_number: your_manual_count}.
4. Run this script.

Usage:
    python calibration.py --config calibration_config.json
"""

import argparse
import json
import cv2
from ultralytics import YOLO
from app.zone import Zone

PERSON_CLASS_ID = 0


def calibrate_clip(source: str, polygon: list, manual_counts: dict, imgsz: int, conf: float, iou: float):
    """manual_counts: {frame_number(int): actual_count(int)}"""
    model = YOLO("yolov8n.pt")
    zone = Zone(polygon)

    manual_counts = {int(k): v for k, v in manual_counts.items()}
    max_frame_needed = max(manual_counts.keys())

    results = model.track(
        source=source, classes=[PERSON_CLASS_ID], imgsz=imgsz, conf=conf, iou=iou,
        tracker="bytetrack.yaml", persist=True, stream=True,
    )

    rows = []
    frame_num = 0
    for r in results:
        frame_num += 1
        track_boxes = {}
        if r.boxes is not None and r.boxes.id is not None:
            ids = r.boxes.id.int().tolist()
            xyxy = r.boxes.xyxy.tolist()
            for tid, box in zip(ids, xyxy):
                track_boxes[tid] = tuple(box)

        zone_state = zone.update(track_boxes)

        if frame_num in manual_counts:
            actual = manual_counts[frame_num]
            predicted = zone_state["count"]
            abs_error = abs(predicted - actual)
            pct_error = (abs_error / actual * 100) if actual > 0 else None
            rows.append({
                "frame": frame_num, "actual": actual, "predicted": predicted,
                "abs_error": abs_error, "pct_error": pct_error,
            })

        if frame_num >= max_frame_needed:
            break

    return rows


def summarize(rows: list, label: str):
    print(f"\n=== {label} ===")
    print(f"{'frame':>6} {'actual':>7} {'predicted':>10} {'abs_err':>8} {'pct_err':>8}")
    for r in rows:
        pct = f"{r['pct_error']:.1f}%" if r["pct_error"] is not None else "n/a"
        print(f"{r['frame']:>6} {r['actual']:>7} {r['predicted']:>10} {r['abs_error']:>8} {pct:>8}")

    if not rows:
        print("No rows to summarize.")
        return

    mae = sum(r["abs_error"] for r in rows) / len(rows)
    pct_errors = [r["pct_error"] for r in rows if r["pct_error"] is not None]
    mape = sum(pct_errors) / len(pct_errors) if pct_errors else None

    print(f"\nMAE:  {mae:.2f} people")
    print(f"MAPE: {mape:.1f}%" if mape is not None else "MAPE: n/a (all actual=0 cases)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to calibration_config.json")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    for clip_name, clip_config in config.items():
        rows = calibrate_clip(
            source=clip_config["source"],
            polygon=[tuple(p) for p in clip_config["polygon"]],
            manual_counts=clip_config["manual_counts"],
            imgsz=clip_config.get("imgsz", 640),
            conf=clip_config.get("conf", 0.35),
            iou=clip_config.get("iou", 0.5),
        )
        summarize(rows, label=clip_name)
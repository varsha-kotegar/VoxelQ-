"""
Phase 3 — VoxelQ full pipeline test
Detector + Tracker (Phase 1) -> Zone (Phase 2) -> ArrivalFilter + Estimator (Phase 3)
Prints live occupancy / arrival rate / wait time / density band per frame,
saves annotated video with overlay.

Usage:
    python test_estimator.py --source sample_videos/clip1.mp4 --output out/clip1_estimate.mp4 \
        --polygon "100,400 500,400 500,700 100,700" --imgsz 1280 --conf 0.25 \
        --window_seconds 10 --low_capacity 10 --high_capacity 25
"""

import argparse
import os
import cv2
from ultralytics import YOLO
from zone import Zone
from arrival_filter import ArrivalFilter
from estimator import WaitTimeEstimator

PERSON_CLASS_ID = 0


def parse_polygon(polygon_str: str):
    points = []
    for pair in polygon_str.strip().split(" "):
        x, y = pair.split(",")
        points.append((int(x), int(y)))
    return points


def run(source, output, polygon_points, imgsz, conf, iou, window_seconds, low_capacity, high_capacity, debounce_seconds):
    os.makedirs(os.path.dirname(output), exist_ok=True)

    cap = cv2.VideoCapture(source)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    model = YOLO("yolov8n.pt")
    zone = Zone(polygon_points)
    arrival_filter = ArrivalFilter(fps=fps, debounce_seconds=debounce_seconds)
    estimator = WaitTimeEstimator(window_seconds=window_seconds, fps=fps,
                                   low_capacity=low_capacity, high_capacity=high_capacity)

    writer = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    results = model.track(
        source=source, classes=[PERSON_CLASS_ID], imgsz=imgsz, conf=conf, iou=iou,
        tracker="bytetrack.yaml", persist=True, stream=True,
    )

    frame_num = 0
    for r in results:
        frame_num += 1
        frame = r.orig_img.copy()

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

        # draw
        zone.draw(frame)
        for tid, (x1, y1, x2, y2) in track_boxes.items():
            in_zone = tid in zone_state["members"]
            color = (0, 255, 0) if in_zone else (200, 200, 200)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, str(tid), (int(x1), int(y1) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        band_color = {"Low": (0, 200, 0), "Medium": (0, 200, 255), "High": (0, 0, 255)}[metrics["density_band"]]
        wait_str = f"{metrics['wait_time_seconds']}s" if metrics["wait_time_seconds"] is not None else "N/A"
        cv2.putText(frame, f"Occupancy: {metrics['avg_occupancy']}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(frame, f"Density: {metrics['density_band']}", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, band_color, 2)
        cv2.putText(frame, f"Est. wait: {wait_str}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

        writer.write(frame)

        print(f"frame {frame_num:>5} | occ(avg): {metrics['avg_occupancy']:>5} | "
              f"arrivals/min: {metrics['arrival_rate_per_min']:>6} | "
              f"wait: {wait_str:>8} | density: {metrics['density_band']}")

    writer.release()
    print(f"\nDone. Annotated video saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--polygon", required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--debounce_seconds", type=float, default=0.5,
                         help="Hysteresis threshold to confirm zone entries/exits")
    parser.add_argument("--window_seconds", type=float, default=10.0,
                         help="Rolling window for L/lambda. Your clips are ~10s, so a 60s "
                              "default window would never fill — override this per clip length.")
    parser.add_argument("--low_capacity", type=int, default=5)
    parser.add_argument("--high_capacity", type=int, default=15)
    args = parser.parse_args()

    poly = parse_polygon(args.polygon)
    run(args.source, args.output, poly, args.imgsz, args.conf, args.iou,
        args.window_seconds, args.low_capacity, args.high_capacity, args.debounce_seconds)

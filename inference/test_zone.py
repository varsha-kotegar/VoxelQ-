"""
Phase 2 — VoxelQ zone integration test
Runs YOLOv8n + ByteTrack (from Phase 1) and feeds each frame's track boxes
into Zone.update() to get live queue-zone counts + entered/exited IDs.
Saves an annotated video with the zone polygon drawn + live count overlay.

Usage:
    python test_zone.py --source sample_videos/clip1.mp4 --output out/clip1_zone.mp4 \
        --polygon "100,400 500,400 500,700 100,700" --imgsz 1280 --conf 0.25
"""

import argparse
import os
import cv2
from ultralytics import YOLO
from zone import Zone

PERSON_CLASS_ID = 0


def parse_polygon(polygon_str: str):
    """'x1,y1 x2,y2 x3,y3 ...' -> [(x1,y1), (x2,y2), ...]"""
    points = []
    for pair in polygon_str.strip().split(" "):
        x, y = pair.split(",")
        points.append((int(x), int(y)))
    return points


def run(source: str, output: str, polygon_points, imgsz: int, conf: float, iou: float):
    os.makedirs(os.path.dirname(output), exist_ok=True)

    model = YOLO("yolov8n.pt")
    zone = Zone(polygon_points, name="queue_zone")

    cap = cv2.VideoCapture(source)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    writer = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    results = model.track(
        source=source,
        classes=[PERSON_CLASS_ID],
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        tracker="bytetrack.yaml",
        persist=True,
        stream=True,
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

        # draw everything
        zone.draw(frame)
        for tid, (x1, y1, x2, y2) in track_boxes.items():
            in_zone = tid in zone_state["members"]
            color = (0, 255, 0) if in_zone else (200, 200, 200)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, str(tid), (int(x1), int(y1) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.putText(frame, f"Zone count: {zone_state['count']}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

        writer.write(frame)

        log = f"frame {frame_num:>5} | zone count: {zone_state['count']:>2}"
        if zone_state["entered"]:
            log += f" | ENTERED: {zone_state['entered']}"
        if zone_state["exited"]:
            log += f" | EXITED: {zone_state['exited']}"
        print(log)

    writer.release()
    print(f"\nDone. Annotated video saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--polygon", required=True,
                         help='Polygon as "x1,y1 x2,y2 x3,y3 ..." (get these from pick_points.py)')
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--iou", type=float, default=0.5)
    args = parser.parse_args()

    poly = parse_polygon(args.polygon)
    run(args.source, args.output, poly, args.imgsz, args.conf, args.iou)

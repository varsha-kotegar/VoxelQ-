import argparse
import os
from ultralytics import YOLO

PERSON_CLASS_ID = 0  # COCO class 0 = "person"


def run(source: str, output: str, conf: float, iou: float, imgsz: int):
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # yolov8n.pt auto-downloads on first run (needs internet once)
    model = YOLO("yolov8n.pt")

    print(f"Running tracking on: {source}")
    print(f"conf={conf}, iou={iou}, imgsz={imgsz}\n")

    results = model.track(
        source=source,
        classes=[PERSON_CLASS_ID],   # only track people, ignore everything else
        conf=conf,
        iou=iou,
        imgsz=imgsz,                 # custom image resolution for detection
        tracker="bytetrack.yaml",    # built into ultralytics, no extra install
        persist=True,                # keep track IDs consistent across frames
        save=True,                   # writes annotated video to runs/track/
        project="out",
        name=os.path.splitext(os.path.basename(output))[0],
        exist_ok=True,
        stream=True,                 # process frame-by-frame so we can log counts
    )

    frame_num = 0
    for r in results:
        frame_num += 1
        track_ids = []
        if r.boxes is not None and r.boxes.id is not None:
            track_ids = r.boxes.id.int().tolist()

        count = len(track_ids)
        print(f"frame {frame_num:>5} | people in frame: {count:>2} | track IDs: {track_ids}")

    print(f"\nDone. Annotated video saved under out/{os.path.splitext(os.path.basename(output))[0]}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to input video clip")
    parser.add_argument("--output", required=True, help="Path for annotated output (used for naming)")
    parser.add_argument("--conf", type=float, default=0.35, help="Detection confidence threshold")
    parser.add_argument("--iou", type=float, default=0.5, help="IoU threshold for NMS")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution for model inference")
    args = parser.parse_args()

    run(args.source, args.output, args.conf, args.iou, args.imgsz)

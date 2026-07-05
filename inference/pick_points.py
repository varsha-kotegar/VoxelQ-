"""
Helper — pick zone polygon points by clicking on the first frame of a video.
Left-click to add a point, right-click to undo last point, press 'q' or ESC
when done. Prints the polygon list to paste into test_zone.py.

Usage:
    python pick_points.py --source sample_videos/clip1.mp4
"""

import argparse
import cv2
import numpy as np

points = []


def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Added point: ({x}, {y})")
    elif event == cv2.EVENT_RBUTTONDOWN and points:
        removed = points.pop()
        print(f"Removed point: {removed}")


def main(source: str):
    cap = cv2.VideoCapture(source)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print(f"Could not read a frame from {source}")
        return

    window = "Click zone points | left-click=add, right-click=undo, q/ESC=done"
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_click)

    while True:
        display = frame.copy()
        for i, p in enumerate(points):
            cv2.circle(display, p, 5, (0, 0, 255), -1)
            cv2.putText(display, str(i), (p[0] + 8, p[1]), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
        if len(points) > 1:
            cv2.polylines(display, [np.array(points, dtype=np.int32)],
                          isClosed=True, color=(0, 255, 255), thickness=2)

        cv2.imshow(window, display)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q") or key == 27:
            break

    cv2.destroyAllWindows()
    print("\nFinal polygon points (paste into test_zone.py):")
    print(points)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to video clip")
    args = parser.parse_args()
    main(args.source)

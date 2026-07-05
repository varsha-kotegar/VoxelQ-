from typing import Dict, List, Tuple, Set
import cv2
import numpy as np


class Zone:
    def __init__(self, polygon_points: List[Tuple[int, int]], name: str = "queue_zone"):
        """
        polygon_points: list of (x, y) pixel coords, in order (clockwise or
        counter-clockwise, doesn't matter, just don't cross yourself).
        """
        self.name = name
        self.polygon = np.array(polygon_points, dtype=np.int32)
        self.previous_members: Set[int] = set()

    @staticmethod
    def bbox_to_anchor(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
        """Bottom-center of bbox = approximate foot position."""
        return ((x1 + x2) / 2.0, y2)

    def _point_in_zone(self, point: Tuple[float, float]) -> bool:
        # cv2.pointPolygonTest is O(n) in polygon vertices, trivial cost per
        # track at typical frame rates (we're checking ~10-40 points/frame
        # against a polygon of ~4-8 vertices — negligible vs. inference cost).
        result = cv2.pointPolygonTest(self.polygon, point, False)
        return result >= 0

    def update(self, track_boxes: Dict[int, Tuple[float, float, float, float]]) -> dict:
        """
        track_boxes: {track_id: (x1, y1, x2, y2)} for the current frame,
        as produced by detector.py / test_track.py.

        Returns:
            {
              "count": int,                # people currently in zone
              "entered": [track_id, ...],   # newly inside this frame
              "exited": [track_id, ...],    # left this frame
              "members": {track_id, ...},   # current members (set)
            }
        """
        current_members: Set[int] = set()
        for track_id, box in track_boxes.items():
            anchor = self.bbox_to_anchor(*box)
            if self._point_in_zone(anchor):
                current_members.add(track_id)

        entered = current_members - self.previous_members
        exited = self.previous_members - current_members

        self.previous_members = current_members

        return {
            "count": len(current_members),
            "entered": sorted(entered),
            "exited": sorted(exited),
            "members": current_members,
        }

    def draw(self, frame: np.ndarray, color=(0, 255, 255), thickness: int = 2) -> np.ndarray:
        """Overlay the polygon on a frame for visual debugging."""
        cv2.polylines(frame, [self.polygon], isClosed=True, color=color, thickness=thickness)
        return frame

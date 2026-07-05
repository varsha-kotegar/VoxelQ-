"""
Phase 3 — VoxelQ estimator
Rolling-window Little's Law: W = L / lambda

L      = average zone occupancy over the window (use RAW zone count —
         Phase 2 confirmed this is already stable, no filtering needed)
lambda = confirmed arrivals in the window / window duration (seconds)
         (use FILTERED arrivals from arrival_filter.py — raw arrivals
         are inflated by boundary jitter)
W      = estimated average wait time in the zone, in seconds

Density banding is relative to a configurable max-capacity for the zone,
since raw people-count doesn't mean the same thing for a small canteen
counter vs. a wide hall — you set what "high" means per camera/zone.
"""

from collections import deque
from typing import Optional


class WaitTimeEstimator:
    def __init__(self, window_seconds: float = 60.0, fps: float = 25.0,
                 low_capacity: int = 5, high_capacity: int = 15):
        """
        window_seconds: rolling window for both L and lambda. Longer window
            = smoother but slower to react to real changes. 60s is a
            reasonable start for queue dynamics; tune per your footage length.
        low_capacity / high_capacity: occupancy thresholds for density band.
            e.g. <5 people = Low, 5-15 = Medium, >15 = High. SET THESE
            based on what you actually see as "empty" vs "packed" in your
            specific clip/zone — there's no universal number, pixel count
            isn't real-world density without camera calibration, so this
            is an explicit, documented assumption, not a hidden one.
        """
        self.window_frames = max(1, round(fps * window_seconds))
        self.fps = fps
        self.window_seconds = window_seconds
        self.low_capacity = low_capacity
        self.high_capacity = high_capacity

        self.occupancy_history = deque(maxlen=self.window_frames)
        self.arrival_history = deque(maxlen=self.window_frames)  # 1 if arrival(s) this frame else 0, summed below
        self.total_arrivals_in_window = deque(maxlen=self.window_frames)

    def update(self, raw_occupancy: int, confirmed_enters_this_frame: int) -> dict:
        self.occupancy_history.append(raw_occupancy)
        self.total_arrivals_in_window.append(confirmed_enters_this_frame)

        avg_occupancy = sum(self.occupancy_history) / len(self.occupancy_history)

        # actual elapsed window (in case we haven't filled window_frames yet)
        elapsed_seconds = len(self.occupancy_history) / self.fps
        total_arrivals = sum(self.total_arrivals_in_window)
        arrival_rate_per_sec = total_arrivals / elapsed_seconds if elapsed_seconds > 0 else 0.0

        wait_time_seconds: Optional[float] = None
        if arrival_rate_per_sec > 0:
            wait_time_seconds = avg_occupancy / arrival_rate_per_sec

        density_band = self._density_band(avg_occupancy)

        return {
            "avg_occupancy": round(avg_occupancy, 2),
            "arrival_rate_per_min": round(arrival_rate_per_sec * 60, 2),
            "wait_time_seconds": round(wait_time_seconds, 1) if wait_time_seconds is not None else None,
            "density_band": density_band,
        }

    def _density_band(self, avg_occupancy: float) -> str:
        if avg_occupancy < self.low_capacity:
            return "Low"
        elif avg_occupancy <= self.high_capacity:
            return "Medium"
        else:
            return "High"

"""
Phase 3 — Arrival filter (hysteresis / debounce)
Fixes the boundary-jitter problem from Phase 2: raw zone membership flickers
frame-to-frame near the polygon edge, producing false ENTERED/EXITED events.

Fix: a track must remain continuously inside (or outside) the zone for
`debounce_frames` consecutive frames before we confirm it as a real
arrival (or departure). This is a per-track state machine, not a global
smoothing trick, so it works correctly even with many people crossing
at different times.

Note: occupancy count itself does NOT need this filter (Phase 2 confirmed
it's already stable) — only entered/exited events do, since those are
what feed the arrival rate (lambda) in Little's Law.
"""

from typing import Set, Dict, List


class ArrivalFilter:
    def __init__(self, fps: float, debounce_seconds: float = 0.5):
        """
        debounce_seconds: how long a track must stay on one side of the
        boundary before we trust the transition. 0.5s is a reasonable
        start — tune up if you still see rapid double-events, tune down
        if genuine quick arrivals get missed.
        """
        self.debounce_frames = max(1, round(fps * debounce_seconds))
        self.pending_enter: Dict[int, int] = {}   # track_id -> consecutive frames inside (not yet confirmed)
        self.pending_exit: Dict[int, int] = {}    # track_id -> consecutive frames outside (not yet confirmed)
        self.confirmed_inside: Set[int] = set()

    def update(self, current_members: Set[int]) -> dict:
        """
        current_members: raw zone membership this frame (from zone.update()["members"]).

        Returns:
            {
              "confirmed_enters": [track_id, ...],  # real arrivals this frame
              "confirmed_exits": [track_id, ...],    # real departures this frame
              "confirmed_count": int,                 # confirmed-inside count (lags raw count slightly)
            }
        """
        confirmed_enters: List[int] = []
        confirmed_exits: List[int] = []

        all_relevant_ids = (
            set(self.pending_enter) | set(self.pending_exit)
            | self.confirmed_inside | current_members
        )

        for tid in all_relevant_ids:
            is_in_now = tid in current_members

            if is_in_now:
                self.pending_exit.pop(tid, None)
                if tid not in self.confirmed_inside:
                    streak = self.pending_enter.get(tid, 0) + 1
                    self.pending_enter[tid] = streak
                    if streak >= self.debounce_frames:
                        self.confirmed_inside.add(tid)
                        del self.pending_enter[tid]
                        confirmed_enters.append(tid)
            else:
                self.pending_enter.pop(tid, None)
                if tid in self.confirmed_inside:
                    streak = self.pending_exit.get(tid, 0) + 1
                    self.pending_exit[tid] = streak
                    if streak >= self.debounce_frames:
                        self.confirmed_inside.discard(tid)
                        del self.pending_exit[tid]
                        confirmed_exits.append(tid)

        return {
            "confirmed_enters": confirmed_enters,
            "confirmed_exits": confirmed_exits,
            "confirmed_count": len(self.confirmed_inside),
        }

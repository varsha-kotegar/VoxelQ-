"""
Run from inference/:
    pytest tests/test_arrival_filter.py -v
"""
from app.arrival_filter import ArrivalFilter


def test_debounce_frames_computed_from_fps_and_seconds():
    f = ArrivalFilter(fps=30, debounce_seconds=0.5)
    assert f.debounce_frames == 15


def test_sustained_entry_confirms_after_debounce_period():
    f = ArrivalFilter(fps=10, debounce_seconds=0.5)  # debounce_frames = 5
    enters_total = []

    for _ in range(4):
        result = f.update({1})  # track 1 inside, frames 1-4
        enters_total += result["confirmed_enters"]
    assert enters_total == []  # not yet confirmed (need 5 frames)

    result = f.update({1})  # frame 5 -> confirmed
    assert result["confirmed_enters"] == [1]
    assert result["confirmed_count"] == 1


def test_boundary_jitter_does_not_produce_false_arrivals():
    """This is the exact bug found in Phase 2: a track flickering in/out of
    the zone every frame should NOT repeatedly count as arrivals."""
    f = ArrivalFilter(fps=10, debounce_seconds=0.5)  # debounce_frames = 5
    total_confirmed_enters = 0

    for i in range(20):
        members = {1} if i % 2 == 0 else set()  # flickers every frame
        result = f.update(members)
        total_confirmed_enters += len(result["confirmed_enters"])

    assert total_confirmed_enters == 0  # never stayed in long enough to confirm


def test_sustained_exit_confirms_after_debounce_period():
    f = ArrivalFilter(fps=10, debounce_seconds=0.5)  # debounce_frames = 5

    for _ in range(5):
        f.update({1})  # confirm entry
    assert f.confirmed_inside == {1}

    exits_total = []
    for _ in range(4):
        result = f.update(set())  # track leaves, frames 1-4 of exit debounce
        exits_total += result["confirmed_exits"]
    assert exits_total == []

    result = f.update(set())  # frame 5 -> confirmed exit
    assert result["confirmed_exits"] == [1]
    assert f.confirmed_inside == set()


def test_multiple_tracks_tracked_independently():
    f = ArrivalFilter(fps=10, debounce_seconds=0.3)  # debounce_frames = 3
    for _ in range(3):
        result = f.update({1, 2})
    assert set(result["confirmed_enters"]) == {1, 2}
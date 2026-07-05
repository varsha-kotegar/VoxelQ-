"""
Run from inference/:
    pytest tests/test_zone.py -v
"""
from app.zone import Zone

# simple square zone: (100,100) to (200,200)
SQUARE = [(100, 100), (200, 100), (200, 200), (100, 200)]


def test_point_inside_zone_is_detected():
    zone = Zone(SQUARE)
    # bbox fully inside the square -> anchor (bottom-center) at (150, 190)
    result = zone.update({1: (140, 150, 160, 190)})
    assert result["count"] == 1
    assert 1 in result["members"]


def test_point_outside_zone_is_excluded():
    zone = Zone(SQUARE)
    result = zone.update({1: (0, 0, 20, 20)})  # anchor at (10, 20), well outside
    assert result["count"] == 0
    assert 1 not in result["members"]


def test_bbox_to_anchor_uses_bottom_center():
    x1, y1, x2, y2 = 100, 50, 200, 150
    anchor = Zone.bbox_to_anchor(x1, y1, x2, y2)
    assert anchor == (150.0, 150.0)  # (mid-x, bottom-y) not box center


def test_entering_and_exiting_detected_across_frames():
    zone = Zone(SQUARE)

    # frame 1: track 1 outside
    r1 = zone.update({1: (0, 0, 20, 20)})
    assert r1["entered"] == []
    assert r1["exited"] == []

    # frame 2: track 1 moves inside
    r2 = zone.update({1: (140, 150, 160, 190)})
    assert r2["entered"] == [1]
    assert r2["count"] == 1

    # frame 3: track 1 moves back outside
    r3 = zone.update({1: (0, 0, 20, 20)})
    assert r3["exited"] == [1]
    assert r3["count"] == 0


def test_multiple_tracks_independent():
    zone = Zone(SQUARE)
    result = zone.update({
        1: (140, 150, 160, 190),  # inside
        2: (0, 0, 20, 20),         # outside
    })
    assert result["count"] == 1
    assert result["members"] == {1}
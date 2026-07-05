"""
Run from inference/:
    pytest tests/test_estimator.py -v
"""
from app.estimator import WaitTimeEstimator


def test_avg_occupancy_is_rolling_mean():
    e = WaitTimeEstimator(window_seconds=10, fps=1, low_capacity=5, high_capacity=15)
    e.update(raw_occupancy=2, confirmed_enters_this_frame=0)
    e.update(raw_occupancy=4, confirmed_enters_this_frame=0)
    result = e.update(raw_occupancy=6, confirmed_enters_this_frame=0)
    assert result["avg_occupancy"] == 4.0  # mean(2, 4, 6)


def test_wait_time_is_none_when_no_arrivals_yet():
    e = WaitTimeEstimator(window_seconds=10, fps=1)
    result = e.update(raw_occupancy=5, confirmed_enters_this_frame=0)
    assert result["wait_time_seconds"] is None  # avoids division by zero


def test_wait_time_follows_littles_law():
    # fps=1 -> each update() call = 1 second elapsed
    e = WaitTimeEstimator(window_seconds=10, fps=1)
    e.update(raw_occupancy=10, confirmed_enters_this_frame=1)  # 1 arrival @ t=1s
    result = e.update(raw_occupancy=10, confirmed_enters_this_frame=0)  # t=2s, no new arrivals

    # avg_occupancy = 10, total_arrivals = 1, elapsed = 2s -> lambda = 0.5/s
    # W = L / lambda = 10 / 0.5 = 20s
    assert result["avg_occupancy"] == 10.0
    assert result["wait_time_seconds"] == 20.0


def test_higher_occupancy_produces_higher_wait_time_at_same_arrival_rate():
    e_low = WaitTimeEstimator(window_seconds=10, fps=1)
    e_high = WaitTimeEstimator(window_seconds=10, fps=1)

    e_low.update(raw_occupancy=5, confirmed_enters_this_frame=1)
    r_low = e_low.update(raw_occupancy=5, confirmed_enters_this_frame=0)

    e_high.update(raw_occupancy=20, confirmed_enters_this_frame=1)
    r_high = e_high.update(raw_occupancy=20, confirmed_enters_this_frame=0)

    assert r_high["wait_time_seconds"] > r_low["wait_time_seconds"]


def test_higher_arrival_rate_produces_lower_wait_time_at_same_occupancy():
    e_slow = WaitTimeEstimator(window_seconds=10, fps=1)
    e_fast = WaitTimeEstimator(window_seconds=10, fps=1)

    e_slow.update(raw_occupancy=10, confirmed_enters_this_frame=1)
    r_slow = e_slow.update(raw_occupancy=10, confirmed_enters_this_frame=0)

    e_fast.update(raw_occupancy=10, confirmed_enters_this_frame=1)
    r_fast = e_fast.update(raw_occupancy=10, confirmed_enters_this_frame=1)  # 2x arrivals

    assert r_fast["wait_time_seconds"] < r_slow["wait_time_seconds"]


def test_density_band_thresholds():
    e = WaitTimeEstimator(window_seconds=10, fps=1, low_capacity=5, high_capacity=15)

    r_low = e.update(raw_occupancy=2, confirmed_enters_this_frame=0)
    assert r_low["density_band"] == "Low"

    e2 = WaitTimeEstimator(window_seconds=10, fps=1, low_capacity=5, high_capacity=15)
    r_med = e2.update(raw_occupancy=10, confirmed_enters_this_frame=0)
    assert r_med["density_band"] == "Medium"

    e3 = WaitTimeEstimator(window_seconds=10, fps=1, low_capacity=5, high_capacity=15)
    r_high = e3.update(raw_occupancy=20, confirmed_enters_this_frame=0)
    assert r_high["density_band"] == "High"
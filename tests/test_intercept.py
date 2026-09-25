import math

import pytest

from fielder_intercept.intercept import (
    chase_time,
    find_catch,
    intercept_angle,
    rank_fielders,
    step_towards,
)


def test_stationary_ball_time_is_distance_over_speed():
    angle, point, t = intercept_angle(10, 0, 0, 0, 0, 0, 5)
    assert t == pytest.approx(2.0)
    assert point == pytest.approx((10.0, 0.0))
    assert angle == pytest.approx(0.0)


def test_ball_running_away_faster_than_fielder_is_uncatchable():
    assert intercept_angle(10, 0, 10, 0, 0, 0, 5) == (None, None, None)


def test_ball_coming_toward_fielder_meets_in_the_middle():
    angle, point, t = intercept_angle(10, 0, -10, 0, 0, 0, 5)
    # closing speed 15 over 10 units -> 2/3 s; fielder covers 5 * 2/3
    assert t == pytest.approx(2 / 3)
    assert point[0] == pytest.approx(10 / 3)
    assert point[1] == pytest.approx(0.0)
    assert math.hypot(*point) == pytest.approx(5 * t)


def test_equal_speeds_take_linear_branch():
    # a == 0 when ball speed == fielder speed; ball at (10,0) heading back at 5
    angle, point, t = intercept_angle(10, 0, -5, 0, 0, 0, 5)
    assert t == pytest.approx(1.0)
    assert point == pytest.approx((5.0, 0.0))


def test_equal_speeds_ball_running_away_is_uncatchable():
    assert intercept_angle(10, 0, 5, 0, 0, 0, 5) == (None, None, None)


def test_facing_angle_points_at_intercept():
    angle, point, t = intercept_angle(0, 10, 0, 0, 0, 0, 5)
    assert angle == pytest.approx(90.0)
    angle, point, t = intercept_angle(-10, 0, 0, 0, 0, 0, 5)
    assert angle == pytest.approx(180.0)


def test_intercept_point_lies_on_ball_path():
    ball = (3.0, -4.0)
    vel = (2.0, 1.5)
    angle, point, t = intercept_angle(*ball, *vel, 8.0, 6.0, 7.0)
    assert t is not None and t > 0
    assert point[0] == pytest.approx(ball[0] + vel[0] * t)
    assert point[1] == pytest.approx(ball[1] + vel[1] * t)
    # fielder arrives exactly when the ball does
    assert math.hypot(point[0] - 8.0, point[1] - 6.0) == pytest.approx(7.0 * t)


def test_chase_time():
    assert chase_time(3, 4, 0, 0, 2.5) == pytest.approx(2.0)


def test_rank_fielders_orders_by_time_and_cuts_to_top_n():
    fielders = [(30, 0, 5), (2, 0, 5), (0, 8, 5), (-40, 0, 5)]
    ranked = rank_fielders((0, 0), (0, 0), fielders, top_n=3)
    assert [i for i, _, _ in ranked] == [1, 2, 0]
    times = [t for _, t, _ in ranked]
    assert times == sorted(times)
    assert times[0] == pytest.approx(0.4)


def test_rank_fielders_falls_back_to_chase_when_uncatchable():
    # ball flying away at 10 along +x; fielder behind it at speed 5 can't intercept
    ranked = rank_fielders((0, 0), (10, 0), [(-5, 0, 5)], top_n=None)
    index, t, point = ranked[0]
    assert index == 0
    assert point is None
    assert t == pytest.approx(1.0)


def test_step_towards_does_not_overshoot():
    assert step_towards((0, 0), (1, 0), speed=10, dt=1) == pytest.approx((1.0, 0.0))
    assert step_towards((0, 0), (10, 0), speed=4, dt=0.5) == pytest.approx((2.0, 0.0))
    assert step_towards((3, 3), (3, 3), speed=4, dt=0.5) == (3, 3)


def test_find_catch_uses_threshold():
    fielders = [(5, 5), (0.5, 0.2), (2, 2)]
    assert find_catch((0, 0), fielders, threshold=1.0) == 1
    assert find_catch((0, 0), fielders, threshold=0.1) is None

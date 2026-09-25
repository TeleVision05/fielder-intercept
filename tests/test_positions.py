import pytest

from fielder_intercept.positions import (
    BOUNDARY_DISTANCE,
    FIELD_SETS,
    POSITION_ANGLE_RADIUS,
    UNIT_CIRCLE_DEGREES,
    compute_position,
    polar_to_cartesian,
    side_of,
    unit_circle_positions,
)


def test_polar_to_cartesian_cardinal_points():
    assert polar_to_cartesian(0, 1.0, 10) == pytest.approx((10, 0))
    assert polar_to_cartesian(90, 1.0, 10) == pytest.approx((0, 10))
    assert polar_to_cartesian(180, 0.5, 10) == pytest.approx((-5, 0))
    assert polar_to_cartesian(270, 1.0, 10, center=(100, 100)) == pytest.approx((100, 90))


def test_compute_position_matches_table():
    assert compute_position("Point") == ("Point", 13.2, 0.0)
    assert compute_position("Wicket Keeper") == ("Wicket Keeper", 0.0, -6.6)
    name, x, y = compute_position("Deep Midwicket")
    assert (x**2 + y**2) ** 0.5 == pytest.approx(BOUNDARY_DISTANCE, abs=0.01)
    assert x < 0 and y > 0


def test_compute_position_scales_with_base_radius():
    _, x, y = compute_position("Point", base_radius=360)
    assert (x, y) == (216.0, 0.0)


def test_every_named_position_is_inside_the_boundary():
    for name in POSITION_ANGLE_RADIUS:
        _, x, y = compute_position(name)
        assert (x**2 + y**2) ** 0.5 <= BOUNDARY_DISTANCE + 0.01, name


def test_unit_circle_positions_are_evenly_spaced():
    positions = unit_circle_positions()
    assert len(positions) == 20
    assert UNIT_CIRCLE_DEGREES == list(range(0, 360, 18))
    assert positions[0] == ("0°", 15.0, 0.0)
    assert positions[5] == ("90°", 0.0, 15.0)
    for _, x, y in positions:
        assert (x**2 + y**2) ** 0.5 == pytest.approx(15, abs=0.01)


def test_field_sets_have_nine_fielders_except_unit_circle():
    for name, positions in FIELD_SETS.items():
        expected = 20 if name == "unit circle" else 9
        assert len(positions) == expected, name


def test_field_set_off_leg_balance():
    def count_off(set_name):
        return sum(1 for _, x, _ in FIELD_SETS[set_name] if side_of(x) == "OFF-SIDE")

    assert count_off("6-3 field") == 6
    assert count_off("7-2 field") == 7
    assert count_off("5-4 field") == 5


def test_side_of_splits_on_x_axis():
    assert side_of(*compute_position("Point")[1:]) == "OFF-SIDE"
    assert side_of(*compute_position("Cover")[1:]) == "OFF-SIDE"
    assert side_of(*compute_position("Square Leg")[1:]) == "LEG-SIDE"
    assert side_of(*compute_position("Bowler")[1:]) == "STRAIGHT"
    assert side_of(*compute_position("Wicket Keeper")[1:]) == "STRAIGHT"

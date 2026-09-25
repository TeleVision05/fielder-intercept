"""Fielding-position geometry shared by the 2D, 3D and matplotlib front-ends.

Coordinate convention, looking down on the ground with the batter at the
origin (this is the "unit circle" mapping the whole project is built on):

    0 deg   = Point            (square of the wicket, off side, +X)
    90 deg  = straight down the ground past the bowler        (+Y)
    180 deg = Square Leg       (leg side, -X)
    270 deg = Wicket Keeper    (behind the stumps, -Y)

Each position is an (angle_deg, radius_factor) pair where radius_factor is a
fraction of the boundary radius, so the same table drives a 22-unit
matplotlib field and a 360-pixel pygame field.
"""

from __future__ import annotations

import math

# Distance from the centre of the pitch to the boundary rope in the
# matplotlib simulation's units.
BOUNDARY_DISTANCE = 22

# 20 evenly spaced points at 18 degree increments, used both by the
# unit-circle plot and by the "unit circle" field set.
UNIT_CIRCLE_DEGREES = list(range(0, 360, 18))
UNIT_CIRCLE_RADIUS = 15

POSITION_ANGLE_RADIUS: dict[str, tuple[float, float]] = {
    "Wicket Keeper": (270, 0.3),
    "Slip (1st/2nd)": (300, 0.4),
    "Gully": (320, 0.5),
    "Deep Gully": (300, 1.0),
    "Point": (0, 0.6),
    "Deep Point": (0, 1.0),
    "Cover": (30, 0.6),
    "Extra Cover": (45, 0.7),
    "Mid-off": (60, 0.7),
    "Long-off": (60, 1.0),
    "Bowler": (90, 0.3),
    "Straight Hit Line": (90, 1.0),
    "Mid-on": (120, 0.7),
    "Long-on": (120, 1.0),
    "Midwicket": (150, 0.7),
    "Deep Midwicket": (150, 1.0),
    "Square Leg": (180, 0.6),
    "Deep Square Leg": (180, 1.0),
    "Fine Leg": (210, 1.0),
    "Short Fine Leg": (210, 0.5),
    "Leg Slip": (240, 0.3),
    "Cover Point": (350, 0.6),
    "Backward Point": (320, 0.6),
    "Deep Third": (330, 1.0),
}


def polar_to_cartesian(
    angle_deg: float,
    radius_factor: float,
    base_radius: float = 1.0,
    center: tuple[float, float] = (0.0, 0.0),
) -> tuple[float, float]:
    """Convert (angle, fraction-of-boundary) to (x, y) around ``center``."""
    angle_rad = math.radians(angle_deg)
    r = radius_factor * base_radius
    return center[0] + r * math.cos(angle_rad), center[1] + r * math.sin(angle_rad)


def compute_position(
    name: str, base_radius: float = BOUNDARY_DISTANCE
) -> tuple[str, float, float]:
    """Return ``(name, x, y)`` for a named fielding position, rounded to 2 dp."""
    angle_deg, radius_factor = POSITION_ANGLE_RADIUS[name]
    x, y = polar_to_cartesian(angle_deg, radius_factor, base_radius)
    return (name, round(x, 2), round(y, 2))


def unit_circle_positions(
    radius: float = UNIT_CIRCLE_RADIUS,
    degrees: list[int] | None = None,
) -> list[tuple[str, float, float]]:
    """Fielders spaced evenly around a ring, labelled by their angle."""
    degrees = UNIT_CIRCLE_DEGREES if degrees is None else degrees
    return [
        (
            f"{deg}°",
            round(radius * math.cos(math.radians(deg)), 2),
            round(radius * math.sin(math.radians(deg)), 2),
        )
        for deg in degrees
    ]


def side_of(x: float, y: float = 0.0, tolerance: float = 1e-9) -> str:
    """Classify a position as OFF-SIDE (+X), LEG-SIDE (-X) or STRAIGHT (x == 0).

    The original script tested ``y < 0``, which labelled Point and Cover as
    leg-side; under the convention documented at the top of this module the
    off/leg split is the X axis.
    """
    if x > tolerance:
        return "OFF-SIDE"
    if x < -tolerance:
        return "LEG-SIDE"
    return "STRAIGHT"


def _positions(*names: str) -> list[tuple[str, float, float]]:
    return [compute_position(name) for name in names]


FIELD_SETS: dict[str, list[tuple[str, float, float]]] = {
    # Off-side heavy: slips/gully/point/cover/extra cover + 3 leg-side.
    "6-3 field": _positions(
        "Slip (1st/2nd)", "Gully", "Point", "Deep Point", "Cover",
        "Extra Cover", "Square Leg", "Mid-on", "Deep Midwicket",
    ),
    # More off-side: adds mid-off, keeps only two leg-side.
    "7-2 field": _positions(
        "Slip (1st/2nd)", "Gully", "Point", "Deep Point", "Cover",
        "Extra Cover", "Mid-off", "Square Leg", "Deep Midwicket",
    ),
    # Balanced: 5 off-side, 4 leg-side.
    "5-4 field": _positions(
        "Point", "Deep Point", "Cover", "Extra Cover", "Mid-off",
        "Square Leg", "Mid-on", "Deep Midwicket", "Long-on",
    ),
    # Custom 9 positions in the order they were requested.
    "custom 9": _positions(
        "Long-off", "Extra Cover", "Cover", "Cover Point", "Backward Point",
        "Deep Gully", "Square Leg", "Deep Midwicket", "Mid-on",
    ),
    "unit circle": unit_circle_positions(),
}

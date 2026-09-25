"""Pure, display-free cricket fielding geometry and intercept math.

Nothing in this package imports pygame, matplotlib or ursina at module
import time, so it is safe to import from tests and headless scripts.
"""

from fielder_intercept.intercept import (
    chase_time,
    find_catch,
    intercept_angle,
    rank_fielders,
    step_towards,
)
from fielder_intercept.positions import (
    BOUNDARY_DISTANCE,
    FIELD_SETS,
    POSITION_ANGLE_RADIUS,
    UNIT_CIRCLE_DEGREES,
    UNIT_CIRCLE_RADIUS,
    compute_position,
    polar_to_cartesian,
    side_of,
    unit_circle_positions,
)

__all__ = [
    "BOUNDARY_DISTANCE",
    "FIELD_SETS",
    "POSITION_ANGLE_RADIUS",
    "UNIT_CIRCLE_DEGREES",
    "UNIT_CIRCLE_RADIUS",
    "chase_time",
    "compute_position",
    "find_catch",
    "intercept_angle",
    "polar_to_cartesian",
    "rank_fielders",
    "side_of",
    "step_towards",
    "unit_circle_positions",
]

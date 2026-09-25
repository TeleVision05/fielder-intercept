"""Time-to-ball and intercept-point math for a fielder chasing a moving ball.

All functions are pure and work on plain floats/tuples so they can be
unit-tested without any display.
"""

from __future__ import annotations

import math
from typing import Sequence

Point = tuple[float, float]
Intercept = tuple[float | None, Point | None, float | None]


def intercept_angle(
    ball_x: float,
    ball_y: float,
    ball_vx: float,
    ball_vy: float,
    fielder_x: float,
    fielder_y: float,
    fielder_speed: float,
) -> Intercept:
    """Earliest point a fielder running at constant speed can meet the ball.

    Solves ``|ball(t) - fielder| = fielder_speed * t`` for the smallest
    positive ``t``. Returns ``(facing_angle_deg, (ix, iy), t)`` or
    ``(None, None, None)`` when no interception is possible.
    """
    rx = ball_x - fielder_x
    ry = ball_y - fielder_y

    a = (ball_vx**2 + ball_vy**2) - fielder_speed**2
    b = 2 * (rx * ball_vx + ry * ball_vy)
    c = rx**2 + ry**2

    disc = b**2 - 4 * a * c
    if disc < 0:
        return None, None, None

    sqrt_disc = math.sqrt(disc)
    if a == 0:
        t1 = -c / b if b != 0 else None
        t2 = None
    else:
        t1 = (-b + sqrt_disc) / (2 * a)
        t2 = (-b - sqrt_disc) / (2 * a)

    t_candidates = [t for t in (t1, t2) if t is not None and t > 0]
    if not t_candidates:
        return None, None, None
    t = min(t_candidates)

    ix = ball_x + ball_vx * t
    iy = ball_y + ball_vy * t
    angle = math.degrees(math.atan2(iy - fielder_y, ix - fielder_x))
    return angle, (ix, iy), t


def chase_time(
    ball_x: float, ball_y: float, fielder_x: float, fielder_y: float, fielder_speed: float
) -> float:
    """Time to run straight to where the ball is *now* (fallback when no intercept)."""
    return math.hypot(ball_x - fielder_x, ball_y - fielder_y) / fielder_speed


def rank_fielders(
    ball_pos: Point,
    ball_vel: Point,
    fielders: Sequence[tuple[float, float, float]],
    top_n: int | None = 3,
) -> list[tuple[int, float, Point | None]]:
    """Rank fielders by how quickly they can reach the ball.

    ``fielders`` is a sequence of ``(x, y, speed)``. Each result is
    ``(index, time, intercept_point_or_None)``; ``None`` means the fielder
    cannot intercept and the time is a direct chase to the ball's current
    position. Sorted ascending by time and cut to ``top_n`` (``None`` keeps all).
    """
    ranked: list[tuple[int, float, Point | None]] = []
    for i, (fx, fy, speed) in enumerate(fielders):
        _angle, point, t = intercept_angle(
            ball_pos[0], ball_pos[1], ball_vel[0], ball_vel[1], fx, fy, speed
        )
        if t is not None:
            ranked.append((i, t, point))
        else:
            ranked.append((i, chase_time(ball_pos[0], ball_pos[1], fx, fy, speed), None))
    ranked.sort(key=lambda item: item[1])
    return ranked if top_n is None else ranked[:top_n]


def step_towards(pos: Point, target: Point, speed: float, dt: float) -> Point:
    """Move ``pos`` toward ``target`` by at most ``speed * dt`` without overshooting."""
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return (pos[0], pos[1])
    step = min(length, speed * dt)
    return (pos[0] + dx / length * step, pos[1] + dy / length * step)


def find_catch(
    ball_pos: Point, fielder_positions: Sequence[Point], threshold: float = 1.0
) -> int | None:
    """Index of the first fielder within ``threshold`` of the ball, else ``None``."""
    for i, (fx, fy) in enumerate(fielder_positions):
        if math.hypot(ball_pos[0] - fx, ball_pos[1] - fy) < threshold:
            return i
    return None

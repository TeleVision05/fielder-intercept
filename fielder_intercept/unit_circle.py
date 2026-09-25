"""Unit-circle degree analysis behind the fielding-position mapping.

The pure helpers (``quadrant_label``, ``degree_rows``,
``format_degree_analysis``) never touch matplotlib; the plotting function
imports it lazily so this module stays importable headless.
"""

from __future__ import annotations

import math

from fielder_intercept.positions import UNIT_CIRCLE_DEGREES

DEGREES = UNIT_CIRCLE_DEGREES

_REFERENCE_ANGLES = [
    0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330,
]


def quadrant_label(deg: float) -> str:
    """Name the quadrant (I-IV) or axis a degree measure lands on."""
    if deg == 0 or deg == 360:
        return "Positive X-axis"
    if deg == 90:
        return "Positive Y-axis"
    if deg == 180:
        return "Negative X-axis"
    if deg == 270:
        return "Negative Y-axis"
    if 0 < deg < 90:
        return "I"
    if 90 < deg < 180:
        return "II"
    if 180 < deg < 270:
        return "III"
    if 270 < deg < 360:
        return "IV"
    return "?"


def degree_rows(degrees: list[int]) -> list[tuple[int, float, float, float, str]]:
    """``(deg, radians, cos, sin, quadrant)`` for each degree."""
    rows = []
    for deg in degrees:
        rad = math.radians(deg)
        rows.append((deg, rad, math.cos(rad), math.sin(rad), quadrant_label(deg)))
    return rows


def format_degree_analysis(degrees: list[int]) -> str:
    """Render the analysis table as text (what the CLI prints)."""
    lines = ["=== UNIT CIRCLE DEGREE ANALYSIS ===", ""]
    lines.append("Degree | Radians | X (cos) | Y (sin) | Quadrant")
    lines.append("-" * 50)
    for deg, rad, x, y, quadrant in degree_rows(degrees):
        lines.append(f"{deg:6d} | {rad:7.4f} | {x:7.4f} | {y:7.4f} | {quadrant}")
    lines.append("")
    lines.append(f"Total points: {len(degrees)}")
    if len(degrees) >= 2:
        increment = degrees[1] - degrees[0]
        lines.append(f"Angle increment: {increment}°")
        lines.append(
            f"Full circle coverage: {degrees[-1] + increment}° (should be 360°)"
        )
    return "\n".join(lines)


def plot_unit_circle_with_degrees(degrees: list[int]):
    """Plot the unit circle with the given degrees marked. Returns ``(fig, ax)``."""
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 10))

    theta = np.linspace(0, 2 * np.pi, 1000)
    ax.plot(np.cos(theta), np.sin(theta), "k-", linewidth=2, label="Unit Circle")

    rows = degree_rows(degrees)
    x_coords = [row[2] for row in rows]
    y_coords = [row[3] for row in rows]
    ax.scatter(x_coords, y_coords, c="red", s=100, zorder=5, label="Degree Points")

    for i, (deg, x, y) in enumerate(zip(degrees, x_coords, y_coords)):
        offset = 0.15
        ax.annotate(
            f"{deg}°",
            (x * (1 + offset), y * (1 + offset)),
            ha="center", va="center", fontsize=10, fontweight="bold",
        )
        if i % 5 == 0:
            coord_offset = 0.25
            ax.annotate(
                f"({x:.3f}, {y:.3f})",
                (x * (1 + coord_offset), y * (1 + coord_offset)),
                ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
            )

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.7)
    ax.axvline(x=0, color="gray", linestyle="--", alpha=0.7)
    ax.set_xlabel("X (cos θ)", fontsize=12)
    ax.set_ylabel("Y (sin θ)", fontsize=12)
    ax.set_title(
        "Unit Circle with Specified Degrees\n(20 points at 18° intervals)",
        fontsize=14, fontweight="bold",
    )
    ax.set_aspect("equal")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")

    for angle in _REFERENCE_ANGLES:
        if angle not in degrees:
            rad = math.radians(angle)
            ax.plot(
                [0, 1.1 * math.cos(rad)], [0, 1.1 * math.sin(rad)],
                "gray", linestyle=":", alpha=0.5, linewidth=1,
            )

    plt.tight_layout()
    return fig, ax

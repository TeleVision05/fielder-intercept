import math
import sys

import pytest

from fielder_intercept.unit_circle import (
    DEGREES,
    degree_rows,
    format_degree_analysis,
    quadrant_label,
)


@pytest.mark.parametrize(
    "deg, expected",
    [
        (0, "Positive X-axis"),
        (90, "Positive Y-axis"),
        (180, "Negative X-axis"),
        (270, "Negative Y-axis"),
        (18, "I"),
        (126, "II"),
        (234, "III"),
        (342, "IV"),
        (400, "?"),
    ],
)
def test_quadrant_label(deg, expected):
    assert quadrant_label(deg) == expected


def test_degree_rows_are_on_the_unit_circle():
    rows = degree_rows(DEGREES)
    assert len(rows) == 20
    for deg, rad, x, y, _ in rows:
        assert rad == pytest.approx(math.radians(deg))
        assert x**2 + y**2 == pytest.approx(1.0)


def test_format_degree_analysis_text():
    text = format_degree_analysis(DEGREES)
    assert "Total points: 20" in text
    assert "Angle increment: 18°" in text
    assert "Full circle coverage: 360°" in text
    assert "   270 |  4.7124 | -0.0000 | -1.0000 | Negative Y-axis" in text


def test_package_import_does_not_pull_in_display_libraries():
    import fielder_intercept  # noqa: F401
    import fielder_intercept.unit_circle  # noqa: F401

    for name in ("matplotlib", "pygame", "ursina"):
        assert name not in sys.modules, f"{name} was imported at package import time"

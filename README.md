# fielder-intercept

Cricket fielder intercept simulation. The core question it explores: given a
ball leaving the bat with some velocity and a ring of fielders with known
positions and running speeds, which fielders can reach the ball, where, and
how soon? The intercept math is a pure module; three throwaway front-ends
(matplotlib, pygame, ursina) sit on top of it.

**Status: experimental.** The intercept/geometry package is tested and works
headless. The matplotlib animation runs (verified headless for 30 frames).
The pygame 2D game compiles and its position mapping is exercised, but it has
not been played end to end in this repo. The ursina 3D prototype is untested.

## Layout

```
fielder_intercept/       pure, display-free package (import this from tests)
  positions.py           position table, polar->cartesian, field sets, off/leg side
  intercept.py           intercept_angle, chase_time, rank_fielders, step_towards, find_catch
  unit_circle.py         degree/quadrant analysis + lazy matplotlib plot
main.py                  matplotlib animation: top-3 fielders chase a random ball
cricket.py               pygame top-down 2D "cricket MVP" (bowl / aim / hit / field)
cricket3d.py             ursina 3D prototype of the same loop (untested)
unit_circle.py           prints the 20-point unit-circle table and plots it
tests/                   offline pytest suite
```

## Coordinate convention

Everything is built on one "unit circle" mapping with the batter at the
origin: 0 deg = Point (+X, off side), 90 deg = straight past the bowler (+Y),
180 deg = Square Leg (-X, leg side), 270 deg = Wicket Keeper (-Y). Each named
position is an `(angle_deg, radius_factor)` pair, with the radius given as a
fraction of the boundary, so the same table drives a 22-unit matplotlib
field and a 360-pixel pygame field.

## Install

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`ursina` (only needed for `cricket3d.py`) pulls in panda3d; drop it from
`requirements.txt` if you only want the 2D tools. Python 3.10+.

## Configure

There is nothing to configure. No environment variables, no API keys, no
config files. Simulation constants (boundary radius, fielder speed ranges,
catch radius, frame rate) are module-level constants at the top of each
script.

## Run

```sh
python main.py          # matplotlib animation with field-set buttons
python cricket.py       # pygame game: Space = run-up, arrows = aim, Enter = hit
python cricket3d.py     # ursina 3D prototype: Space / Enter / WASD / C
python unit_circle.py   # prints the degree table, shows the plot, offers to save
```

Each script opens a window; none of them touch a display at import time.

## Test

```sh
python -m pytest
```

Tests cover the intercept quadratic (stationary ball, ball running away,
head-on, equal-speed linear branch), the fielder ranking and fallback chase,
the position table and field-set off/leg counts, and the unit-circle table.
They never open a window or hit the network. A guard test asserts that
importing the package does not import matplotlib, pygame or ursina.

## Data & secrets

No data files, weights or credentials are used or expected. The only thing
the scripts can write is `unit_circle_degrees.png` (opt-in prompt in
`unit_circle.py`), which is gitignored. `venv/` is gitignored.

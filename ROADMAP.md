# Roadmap

## Current state (2026-09-25)

What works, and how it was verified:

- `fielder_intercept.intercept.intercept_angle` solves the constant-speed
  pursuit quadratic and returns the earliest positive intercept. Verified by
  `tests/test_intercept.py` (32 tests total across the suite, all passing
  under Python 3.13 / pytest 9.1).
- `rank_fielders` picks the N fastest fielders and falls back to a straight
  chase when no intercept exists, matching the original `main.py` loop.
- `fielder_intercept.positions` holds the single position table and the five
  field sets (6-3, 7-2, 5-4, custom 9, unit circle). Off/leg counts of the
  named sets are asserted in tests.
- `main.py` (matplotlib) runs headless for 30 frames with `MPLBACKEND=Agg`
  and produced a catch; the interactive window path (`plt.show`, buttons)
  is unchanged from the original but was not clicked through here.
- `cricket.py` (pygame) byte-compiles and its `polar_to_cartesian` pixel
  mapping matches the original formula (Point -> (666, 450), Wicket Keeper
  -> (450, 342)). Gameplay not exercised in this repo.
- `cricket3d.py` (ursina) byte-compiles only. Left byte-for-byte as found.

Fixed while importing:

- `cricket.py` had an exact copy of `main.py` pasted after its `__main__`
  guard (lines 389-812). Removed; `main.py` is the only matplotlib sim.
- `Fielder.get_side()` tested `y < 0`, which labelled Point and Cover as
  leg-side. `side_of()` now splits on the X axis per the documented
  convention and returns `STRAIGHT` for x == 0 (Bowler, Wicket Keeper).
- Fielder movement in `main.py` no longer overshoots the target
  (`step_towards` clamps to the remaining distance).

## Known gaps

- `intercept_angle` assumes the ball moves at constant velocity. `main.py`
  wobbles the velocity every 15 frames, so intercept points drift and the
  top-3 selection can flip between fielders frame to frame.
- The pygame `Fielder.move_towards` and ursina `Fielder3D.move_towards` run
  straight at the ball's current position; neither front-end uses the
  intercept solver yet. Only `main.py` does.
- `cricket3d.py` and `cricket.py` each carry their own copy of the position
  table with different radii and names (`"Slip"` vs `"Slip (1st/2nd)"`).
  `cricket.py` now imports the shared table; `cricket3d.py` does not.
- `main.py` uses `blit=True`, so title changes ("CAUGHT by ...") only show
  on the next full redraw.
- `FuncAnimation(frames=100)` repeats from frame 0 after 100 frames while
  simulation state persists, so the wobble cadence restarts mid-play.
- Fielder speeds in `main.py` are re-randomised on every Restart
  (`reset_position`), so runs are not reproducible; there is no seed control.
- No CLI arguments anywhere: field set, seed, and ball velocity are
  hard-coded or random.
- `cricket3d.py` creates the Ursina app at import time (required by how
  ursina discovers module-level `update`/`input`), so it cannot be imported
  headless.

## Milestones

### M1: Deterministic, scriptable simulation core
- [ ] Add a `Simulation` class in the package that steps ball + fielders
      without matplotlib (state in, state out).
- [ ] Accept a `random.Random` seed so a run is reproducible.
- [ ] Add a `--field-set` / `--seed` / `--frames` CLI to `main.py`.
- Done when: `python main.py --seed 1 --headless` prints the same catch
  result on two runs and a test asserts it.

### M2: Use the intercept solver in every front-end
- [ ] Replace pygame `Fielder.move_towards(ball)` with `rank_fielders` +
      `step_towards` toward the intercept point.
- [ ] Same for `cricket3d.py` (project to the ground plane, ignore y).
- Done when: both games import from `fielder_intercept.intercept` and a
  fielder visibly cuts the ball off rather than trailing it.

### M3: One position table for all three front-ends
- [ ] Add per-front-end scale/units (metres vs pixels vs sim units) to
      `positions.py` and delete the duplicate tables in `cricket3d.py`.
- [ ] Reconcile the position names (`"Slip"` vs `"Slip (1st/2nd)"`).
- Done when: `grep -n "Wicket Keeper" *.py` finds the tuple in exactly one
  file and all tests still pass.

### M4: Better fielder model
- [ ] Add acceleration / reaction time to the intercept solve instead of
      instant constant speed.
- [ ] Add a catch probability that depends on ball height and closing speed
      instead of a fixed radius.
- Done when: a test shows a fielder starting from rest reaches the ball
  later than the constant-speed solve predicts.

### M5: Evaluate field sets
- [ ] Run N random deliveries per field set headless and report catch,
      boundary and dot-ball rates.
- [ ] Write results to a CSV (gitignored) and summarise in the README.
- Done when: `python -m fielder_intercept.evaluate --n 1000` prints a table
  comparing the five field sets.

## Won't do / out of scope

- Realistic bat-ball physics, bowler variations, or a full match engine.
- Networked or multiplayer play.
- Packaging for PyPI; this is a personal sandbox.
- Rewriting `cricket3d.py` on a different engine.

## Open questions

- Should the unit-circle 20-fielder set stay? It is a geometry sanity check,
  not a legal field (11 players max), and it inflates every "all field sets"
  test with a special case.
- Is the matplotlib animation the long-term front-end, or should the
  pygame game absorb the intercept logic and `main.py` become a headless
  evaluator only?
- What running speed range is realistic? `main.py` uses 4-6 units/s on a
  22-unit boundary; `cricket3d.py` uses 8 m/s on a 70 m boundary. They are
  not calibrated against each other or real data.

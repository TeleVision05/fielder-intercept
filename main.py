"""Top-down matplotlib animation of fielders intercepting a ball.

A ball leaves the pitch centre with a random velocity and wobbles as it
travels; every frame the three fielders with the shortest computed
intercept time run toward their intercept point (or straight at the ball
if no intercept is possible). Buttons switch between field sets.

Run with ``python main.py``. Opens a window; no display is touched at
import time, so the module can be imported headless.
"""

from __future__ import annotations

import random

from fielder_intercept.intercept import find_catch, rank_fielders, step_towards
from fielder_intercept.positions import BOUNDARY_DISTANCE, FIELD_SETS, side_of

FIELD_SIZE = 50
DT = 0.1
CATCH_RADIUS = 1.0
MAX_BALL_SPEED = 8
WOBBLE_EVERY = 15
TOP_N = 3
FRAMES = 100
INTERVAL_MS = 100
DEFAULT_FIELD_SET = "6-3 field"

BUTTONS = [
    ("Restart", [0.70, 0.02, 0.08, 0.04], None),
    ("6-3", [0.79, 0.02, 0.07, 0.04], "6-3 field"),
    ("7-2", [0.87, 0.02, 0.07, 0.04], "7-2 field"),
    ("5-4", [0.95, 0.02, 0.07, 0.04], "5-4 field"),
    ("Unit Circle", [0.70, 0.08, 0.12, 0.04], "unit circle"),
    ("Custom 9", [0.84, 0.08, 0.12, 0.04], "custom 9"),
]


class Fielder:
    def __init__(self, name: str, x: float, y: float, speed: float | None = None):
        self.name = name
        self.original_pos = [x, y]
        self.current_pos = [x, y]
        self.speed = speed if speed else random.uniform(4, 6)
        self.dot = None

    def reset_position(self) -> None:
        self.current_pos = self.original_pos.copy()
        self.speed = random.uniform(4, 6)

    def get_side(self) -> str:
        return side_of(*self.original_pos)


def random_ball_velocity() -> list[float]:
    return [
        random.uniform(-MAX_BALL_SPEED, MAX_BALL_SPEED),
        random.uniform(-MAX_BALL_SPEED, MAX_BALL_SPEED),
    ]


class FieldSimulation:
    def __init__(self, field_set: str = DEFAULT_FIELD_SET):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button

        self.plt = plt
        self.field_set = field_set
        self.fielders: list[Fielder] = []
        self.ball_pos = [0.0, 0.0]
        self.ball_vel = random_ball_velocity()
        self.ball_caught = False
        self.caught_by: str | None = None

        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(-FIELD_SIZE / 2, FIELD_SIZE / 2)
        self.ax.set_ylim(-FIELD_SIZE / 2, FIELD_SIZE / 2)
        self.ax.set_aspect("equal")
        self.ax.add_patch(
            plt.Circle((0, 0), BOUNDARY_DISTANCE, fill=False, color="green", linewidth=2)
        )
        self.ax.plot(0, 0, "s", color="brown", markersize=8, label="Pitch")
        (self.ball_dot,) = self.ax.plot([], [], "ro", markersize=10, label="Ball")
        self.ax.legend()

        self._buttons = []
        for label, rect, target_set in BUTTONS:
            button = Button(plt.axes(rect), label)
            if target_set is None:
                button.on_clicked(lambda _event: self.reset_simulation())
            else:
                button.on_clicked(lambda _event, s=target_set: self.change_field_set(s))
            self._buttons.append(button)

        self.change_field_set(field_set)

    # -- state -------------------------------------------------------------

    def change_field_set(self, set_name: str) -> None:
        self.field_set = set_name
        self.ball_caught = False
        self.caught_by = None
        for fielder in self.fielders:
            if fielder.dot is not None:
                fielder.dot.remove()
        self.fielders = [Fielder(name, x, y) for name, x, y in FIELD_SETS[set_name]]
        for fielder in self.fielders:
            (fielder.dot,) = self.ax.plot([], [], "bo", markersize=6)
        self._print_positions()
        self.ax.set_title(f"Cricket Field Simulation - {set_name.title()} Field")

    def reset_simulation(self) -> None:
        self.ball_pos = [0.0, 0.0]
        self.ball_vel = random_ball_velocity()
        self.ball_caught = False
        self.caught_by = None
        for fielder in self.fielders:
            fielder.reset_position()
        self.ax.set_title(f"Cricket Field Simulation - {self.field_set.title()} Field")

    def _print_positions(self) -> None:
        print(f"\n=== {self.field_set.upper()} FIELD SET ===")
        print("Fielder positions:")
        for i, fielder in enumerate(self.fielders):
            x, y = fielder.original_pos
            print(f"  {i + 1}. {fielder.name}: ({x:3.0f}, {y:3.0f}) - {fielder.get_side()}")

    # -- animation ---------------------------------------------------------

    def artists(self):
        return [self.ball_dot] + [f.dot for f in self.fielders]

    def init(self):
        self.ball_dot.set_data([], [])
        for fielder in self.fielders:
            fielder.dot.set_data([], [])
        return self.artists()

    def _redraw(self):
        self.ball_dot.set_data([self.ball_pos[0]], [self.ball_pos[1]])
        for fielder in self.fielders:
            fielder.dot.set_data([fielder.current_pos[0]], [fielder.current_pos[1]])
        return self.artists()

    def update(self, frame: int):
        if not self.ball_caught:
            if (self.ball_pos[0] ** 2 + self.ball_pos[1] ** 2) ** 0.5 >= BOUNDARY_DISTANCE:
                self.ball_caught = True
                self.caught_by = "BOUNDARY"
                self.ax.set_title("BOUNDARY! Ball hit the boundary. Click Restart for new simulation")
            else:
                idx = find_catch(
                    self.ball_pos, [f.current_pos for f in self.fielders], CATCH_RADIUS
                )
                if idx is not None:
                    self.ball_caught = True
                    self.caught_by = self.fielders[idx].name
                    self.ax.set_title(
                        f"CAUGHT by {self.caught_by}! Click Restart for new simulation"
                    )
        if self.ball_caught:
            return self._redraw()

        if frame % WOBBLE_EVERY == 0:
            for axis in (0, 1):
                self.ball_vel[axis] += random.uniform(-0.3, 0.3)
                self.ball_vel[axis] = max(-MAX_BALL_SPEED, min(MAX_BALL_SPEED, self.ball_vel[axis]))
        self.ball_pos[0] += self.ball_vel[0] * DT
        self.ball_pos[1] += self.ball_vel[1] * DT

        ranked = rank_fielders(
            self.ball_pos,
            self.ball_vel,
            [(f.current_pos[0], f.current_pos[1], f.speed) for f in self.fielders],
            top_n=TOP_N,
        )
        for index, _time, point in ranked:
            fielder = self.fielders[index]
            target = point if point is not None else tuple(self.ball_pos)
            fielder.current_pos = list(
                step_towards(tuple(fielder.current_pos), target, fielder.speed, DT)
            )
        return self._redraw()

    def run(self) -> None:
        import matplotlib.animation as animation

        self.ani = animation.FuncAnimation(
            self.fig, self.update, frames=FRAMES, init_func=self.init,
            interval=INTERVAL_MS, blit=True,
        )
        self.plt.show()


def main() -> None:
    FieldSimulation().run()


if __name__ == "__main__":
    main()

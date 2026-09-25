"""Playable top-down 2D cricket MVP (pygame).

Space starts the bowler's run-up, arrow keys aim, Enter swings. Fielders
run straight at the ball and catch it when it is low and close. Run with
``python cricket.py``; the window is only created inside ``Game()``.
"""

import math
import random
import pygame

WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 60
BOUNDARY_RADIUS_PX = 360
PITCH_HALF_LENGTH = 40

GREEN = (22, 92, 45)
DARK_GREEN = (16, 70, 34)
WHITE = (240, 240, 240)
BROWN = (140, 90, 50)
RED = (200, 40, 40)
BLUE = (50, 120, 220)
YELLOW = (245, 210, 60)

from fielder_intercept.positions import POSITION_ANGLE_RADIUS
from fielder_intercept.positions import polar_to_cartesian as _polar_offset


def polar_to_cartesian(angle_deg, radius_factor):
	"""Pixel position for (angle, fraction-of-boundary) around the screen centre."""
	ox, oy = _polar_offset(angle_deg, radius_factor, BOUNDARY_RADIUS_PX)
	return CENTER[0] + int(ox), CENTER[1] + int(oy)


class Ball:
	def __init__(self):
		self.x, self.y = CENTER
		self.vx, self.vy = 0.0, 0.0
		self.radius = 6
		self.in_air = False
		# simple vertical dimension for arc
		self.z = 0.0
		self.vz = 0.0
		self.gravity = -0.55
		self.bounced = False
		self.spinx = 0.0
		self.spiny = 0.0
		self.boundary_scored = None  # None|4|6
		self.edged = False

	def bowl(self):
		bx, by = polar_to_cartesian(*POSITION_ANGLE_RADIUS["Bowler"])
		self.x, self.y = bx, by
		dx = CENTER[0] - self.x
		dy = CENTER[1] - self.y
		length = math.hypot(dx, dy) or 1
		# slightly slower base speed; add natural swing/seam laterally
		speed = 7.0
		self.vx = speed * (dx / length)
		self.vy = speed * (dy / length)
		self.vz = 6.0
		self.z = 0.0
		self.bounced = False
		self.in_air = True
		self.boundary_scored = None
		# random swing/seam influences (tiny)
		self.spinx = random.uniform(-0.025, 0.025)
		self.spiny = random.uniform(-0.025, 0.025)

	def hit(self, angle_deg, power):
		self.x, self.y = CENTER
		angle_rad = math.radians(angle_deg)
		# base speed tuned down to reduce auto-sixes
		# tune base speed lower to limit effortless big hits
		speed = 10.0 * power
		self.vx = speed * math.cos(angle_rad)
		self.vy = speed * math.sin(angle_rad)
		# default loft minimal to avoid frequent sixes
		self.vz = 5.5 * power
		self.z = 0.0
		self.bounced = False
		self.in_air = True
		# give some spin to curve ball flight
		self.spinx = 0.02 * math.sin(angle_rad)
		self.spiny = -0.02 * math.cos(angle_rad)
		self.boundary_scored = None
		# reset edged state
		self.edged = False

	def update(self):
		if not self.in_air:
			return
		# apply spin as slight curve
		self.vx += self.spinx
		self.vy += self.spiny
		self.x += self.vx
		self.y += self.vy
		# air drag
		self.vx *= 0.996
		self.vy *= 0.996
		# vertical motion and bounce on pitch (more energy loss)
		self.vz += self.gravity
		self.z += self.vz
		if self.z <= 0 and not self.bounced:
			self.z = 0
			self.vz = -self.vz * 0.45
			self.vx *= 0.92
			self.vy *= 0.92
			self.bounced = True
		# boundary check
		dist = math.hypot(self.x - CENTER[0], self.y - CENTER[1])
		if dist >= BOUNDARY_RADIUS_PX:
			# 6 only if never bounced and still clearly aerial
			self.boundary_scored = 6 if (not self.bounced and self.z > 6.0) else 4
			self.in_air = False
		# consider ball dead when it slows down on ground after bounce
		speed = math.hypot(self.vx, self.vy)
		if self.z <= 0 and self.bounced and speed < 0.2:
			self.in_air = False

	def draw(self, surf):
		# shadow (clamp z to non-negative to avoid oversized shadow)
		z_clamped = max(0.0, self.z)
		shadow_r = max(2, int(self.radius * (1 - min(1, z_clamped / 20))))
		pygame.draw.circle(surf, (40, 40, 40), (int(self.x)+2, int(self.y)+2), shadow_r)
		# vertical projection
		py = int(self.y - z_clamped)
		# simple perspective: ball appears smaller farther from camera (larger y)
		depth_scale = max(0.6, 1.15 - (self.y - (CENTER[1]-BOUNDARY_RADIUS_PX)) / (BOUNDARY_RADIUS_PX * 2))
		r = max(2, int(self.radius * depth_scale))
		pygame.draw.circle(surf, RED, (int(self.x), py), r)

class Bat:
	def __init__(self):
		self.swinging = False
		self.swing_t = 0.0
		self.swing_speed = 0.18  # per frame
		self.contact_window_start = 0.45
		self.contact_window_end = 0.6

	def start_swing(self):
		if not self.swinging:
			self.swinging = True
			self.swing_t = 0.0

	def update(self):
		if self.swinging:
			self.swing_t += self.swing_speed
			if self.swing_t >= 1.0:
				self.swinging = False

	def can_contact(self) -> bool:
		return self.contact_window_start <= self.swing_t <= self.contact_window_end

class Bowler:
	def __init__(self):
		self.start_angle = POSITION_ANGLE_RADIUS["Bowler"][0]
		self.start_rf = 0.7
		self.release_rf = POSITION_ANGLE_RADIUS["Bowler"][1]
		self.t = 0.0
		self.speed = 0.02

	def reset(self):
		self.t = 0.0

	def update(self):
		self.t = min(1.0, self.t + self.speed)

	def pos(self):
		rf = self.start_rf * (1 - self.t) + self.release_rf * self.t
		return polar_to_cartesian(self.start_angle, rf)

	def draw(self, surf):
		x, y = self.pos()
		pygame.draw.circle(surf, WHITE, (x, y), 10)


class Fielder:
	def __init__(self, name):
		self.name = name
		angle, rf = POSITION_ANGLE_RADIUS[name]
		self.x, self.y = polar_to_cartesian(angle, rf)
		self.speed = 2.2

	def move_towards(self, tx, ty):
		dx, dy = tx - self.x, ty - self.y
		length = math.hypot(dx, dy)
		if length > 1e-3:
			self.x += (dx / length) * self.speed
			self.y += (dy / length) * self.speed

	def draw(self, surf):
		pygame.draw.circle(surf, BLUE, (int(self.x), int(self.y)), 8)


class Game:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Cricket 2D MVP")
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		self.clock = pygame.time.Clock()
		self.font = pygame.font.SysFont("Arial", 18)
		self.running = True
		self.ball = Ball()
		self.bowler = Bowler()
		self.bat = Bat()
		self.fielders = [
			Fielder("Wicket Keeper"), Fielder("Slip (1st/2nd)"), Fielder("Gully"), Fielder("Cover"), Fielder("Extra Cover"),
			Fielder("Point"), Fielder("Square Leg"), Fielder("Mid-on"), Fielder("Mid-off"),
			Fielder("Deep Midwicket"), Fielder("Long-off")
		]
		self.bat_angle = 0
		self.score = 0
		self.wickets = 0
		self.balls_in_over = 0
		self.overs = 0
		self.last_power = 0.0
		self.message = "Space: Start run-up | Arrows: Aim | Enter: Hit (hold for loft)"
		self.state = "IDLE"  # IDLE -> RUNUP -> FLIGHT/HIT -> FIELDING -> DEAD

	def update(self):
		# update bat swing animation
		self.bat.update()
		if self.state == "RUNUP":
			self.bowler.update()
			# carry the ball with bowler during run-up
			bx, by = self.bowler.pos()
			self.ball.x, self.ball.y = bx, by
			if self.bowler.t >= 1.0:
				self.ball.bowl()
				self.state = "FLIGHT"
				self.message = "Ball in flight. Enter to hit"
		elif self.state in ("FLIGHT", "HIT"):
			self.ball.update()
			if self.ball.in_air:
				# move all fielders a bit toward ball
				for f in self.fielders:
					f.move_towards(self.ball.x, self.ball.y)
					# catch if close and ball is low
					if self.ball.z < 4 and math.hypot(f.x - self.ball.x, f.y - self.ball.y) < 12:
						self.state = "DEAD"
						self._end_ball(caught=True)
						self.ball.in_air = False
						break
				# wicket keeper quick catch/stop behind stumps for edges/misses
				wk = next((f for f in self.fielders if f.name == "Wicket Keeper"), None)
				if wk and self.ball.z < 3 and math.hypot(wk.x - self.ball.x, wk.y - self.ball.y) < 16:
					self.state = "DEAD"
					self._end_ball(caught=True)
					self.ball.in_air = False
			else:
				self.state = "DEAD"
				self._end_ball()

	def draw_field(self):
		self.screen.fill(DARK_GREEN)
		pygame.draw.circle(self.screen, GREEN, CENTER, BOUNDARY_RADIUS_PX)
		pygame.draw.circle(self.screen, WHITE, CENTER, BOUNDARY_RADIUS_PX, 3)
		pygame.draw.rect(self.screen, BROWN, (CENTER[0] - 6, CENTER[1] - PITCH_HALF_LENGTH, 12, PITCH_HALF_LENGTH * 2))
		wk_x, wk_y = polar_to_cartesian(POSITION_ANGLE_RADIUS["Wicket Keeper"][0], 0.02)
		bw_x, bw_y = polar_to_cartesian(POSITION_ANGLE_RADIUS["Bowler"][0], 0.02)
		pygame.draw.circle(self.screen, WHITE, (wk_x, wk_y), 4)
		pygame.draw.circle(self.screen, WHITE, (bw_x, bw_y), 4)
		# bowler avatar
		self.bowler.draw(self.screen)

	def draw(self):
		self.draw_field()
		for f in self.fielders:
			f.draw(self.screen)
		self.ball.draw(self.screen)
		hud = self.font.render(f"{self.overs}.{self.balls_in_over}  Score: {self.score}/{self.wickets}  State: {self.state}  Power: {self.last_power:.2f}", True, WHITE)
		self.screen.blit(hud, (20, 20))
		msg = self.font.render(self.message, True, YELLOW)
		self.screen.blit(msg, (20, HEIGHT - 40))

	def handle_input(self):
		keys = pygame.key.get_pressed()
		# aiming via arrow keys for hit direction (used at hit time)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					if self.state in ("IDLE", "DEAD"):
						self.reset()
						self.state = "RUNUP"
						self.message = "Bowler running in... Enter to attempt shot"
				elif event.key == pygame.K_RETURN:
					if self.state == "FLIGHT":
						# compute angle from arrow keys at hit moment
						kx = (1 if keys[pygame.K_RIGHT] else 0) + (-1 if keys[pygame.K_LEFT] else 0)
						ky = (1 if keys[pygame.K_DOWN] else 0) + (-1 if keys[pygame.K_UP] else 0)
						if kx == 0 and ky == 0:
							# default straight back past bowler
							angle = 90
						else:
							angle = (math.degrees(math.atan2(ky, kx)) + 360) % 360
						# Only allow contact within bat swing window
						if not self.bat.can_contact():
							# swing and miss; let ball continue, likely to keeper
							self.bat.start_swing()
							break
						self.bat.start_swing()
						# timing mapped using a sweet spot window around the stumps
						d = math.hypot(self.ball.x - CENTER[0], self.ball.y - CENTER[1])
						sweet = 18.0  # tighter ideal contact distance (px)
						max_miss = 200.0  # beyond this timing is very poor
						if d <= sweet:
							timing_score = 1.0
						else:
							timing_score = max(0.0, 1.0 - (d - sweet) / (max_miss - sweet))
						# base power ranges from 0.25 to 1.0 depending on timing
						power = 0.2 + 0.7 * timing_score
						# loft boost only if Down held AND good timing
						if keys[pygame.K_DOWN] and timing_score > 0.7:
							power = min(1.0, power + 0.1)
						# edges: if mistimed (d > 150), deflect towards slips/keeper and cut power
						if d > 150:
							self.ball.edged = True
							angle = (angle * 0.2 + 315 * 0.8) % 360
							power *= 0.6
						self.ball.hit(angle, power)
						self.last_power = power
						self.state = "HIT"
						self.message = f"Hit! Power {power:.2f}"

	def _end_ball(self, caught: bool = False):
		# boundary scoring
		if self.ball.boundary_scored is not None:
			self.score += self.ball.boundary_scored
			self.message = f"{self.ball.boundary_scored} runs! Space for next ball"
		else:
			if caught:
				self.wickets += 1
				self.message = "Caught! Space for next ball"
			else:
				# simple running: award 1 run if ball travelled > quarter field and not caught
				travel = math.hypot(self.ball.x - CENTER[0], self.ball.y - CENTER[1])
				self.score += 1 if travel > BOUNDARY_RADIUS_PX * 0.25 else 0
				self.message = ("1 run! Space for next ball" if travel > BOUNDARY_RADIUS_PX * 0.25 else "Dot ball. Space for next ball")
		# increment over/ball count
		self.balls_in_over += 1
		if self.balls_in_over >= 6:
			self.overs += 1
			self.balls_in_over = 0

	def reset(self):
		self.ball = Ball()
		self.bowler.reset()
		# reset some fielders slightly
		for f in self.fielders:
			angle, rf = POSITION_ANGLE_RADIUS[f.name]
			f.x, f.y = polar_to_cartesian(angle, rf)

	def run(self):
		while self.running:
			self.clock.tick(FPS)
			self.handle_input()
			self.update()
			self.draw()
			pygame.display.flip()
		pygame.quit()


if __name__ == "__main__":
	Game().run()

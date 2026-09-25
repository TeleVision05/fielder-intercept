from ursina import *
import math, random

app = Ursina()
window.title = 'Cricket 3D (Prototype)'
camera.fov = 80

# Scene
# Units (meters)
PITCH_LENGTH = 20.12
BOUNDARY_RADIUS = 70.0

ground = Entity(model='plane', scale=(160,1,160), color=color.rgb(22,92,45), texture='white_cube', texture_scale=(80,80))
pitch = Entity(model='cube', scale=(3.0,0.05,PITCH_LENGTH), position=(0,0.03,0), color=color.rgb(140,90,50))
boundary = Entity(model=Circle(resolution=96, mode='line'), scale=BOUNDARY_RADIUS, rotation_x=90, color=color.azure)
# Initial camera behind batter, looking down the pitch
camera.position = (0, 3.0, -8.0)
camera.look_at((0,1.4,2))

# Entities
ball = Entity(model='sphere', color=color.red, scale=0.4, position=(0,1,0))
ball_v = Vec3(0,0,0)
ball_spin = Vec3(0,0,0)
ball_gravity = Vec3(0,-9.8,0)
# Physics tuning
GROUND_Y = 0.5
RESTITUTION = 0.55   # vertical energy retained on bounce
GROUND_FRICTION = 0.90  # horizontal loss on bounce
ROLLING_FRICTION = 0.985  # per-frame rolling slowdown
STOP_SPEED = 0.6
ball_bounced = False

bowler_start = Vec3(0,0,-30)
bowler_release = Vec3(0,0,-10)
bowler = Entity(model='cube', scale=(0.6,1.8,0.6), color=color.white, position=bowler_start)
runup_t = 0.0

bat_pivot = Entity(position=(0,1,1))
bat = Entity(parent=bat_pivot, model='cube', scale=(0.2,0.8,2.2), origin=(0,-0.5,-1.0), color=color.yellow)
swinging = False
swing_t = 0.0
swing_speed = 4.0

state = 'IDLE'
ball_live = False
camera_flip = False  # press 'c' to flip camera to the other side

# Fielders (3D) using unit circle mapping at realistic depths
FIELDER_SPEED = 8.0  # m/s

def polar_to_ground(angle_deg: float, radius_m: float) -> Vec3:
	ang = math.radians(angle_deg)
	x = radius_m * math.cos(ang)
	z = radius_m * math.sin(ang)
	return Vec3(x, 0, z)

# Angle map (0° = +X off-side, 90° = straight past bowler +Z)
POSITION_ANGLE_RADIUS = {
	"Wicket Keeper": (270, 2.0),
	"Slip": (300, 8.0),
	"Gully": (320, 12.0),
	"Point": (0, 18.0),
	"Deep Point": (0, BOUNDARY_RADIUS),
	"Cover": (30, 18.0),
	"Extra Cover": (45, 22.0),
	"Mid-off": (60, 22.0),
	"Long-off": (60, BOUNDARY_RADIUS),
	"Mid-on": (120, 22.0),
	"Long-on": (120, BOUNDARY_RADIUS),
	"Midwicket": (150, 22.0),
	"Deep Midwicket": (150, BOUNDARY_RADIUS),
	"Square Leg": (180, 18.0),
	"Deep Square Leg": (180, BOUNDARY_RADIUS),
}

class Fielder3D:
	def __init__(self, name: str):
		self.name = name
		angle, radius = POSITION_ANGLE_RADIUS[name]
		pos = polar_to_ground(angle, radius)
		self.base_position = pos
		self.entity = Entity(model='cube', color=color.azure, scale=(0.6,1.8,0.6), position=self.base_position)
		self.speed = FIELDER_SPEED

	def move_towards(self, target: Vec3, dt: float):
		d = target - self.entity.position
		d.y = 0
		L = d.length()
		if L > 1e-3:
			step = min(L, self.speed * dt)
			self.entity.position += d.normalized() * step

	def reset(self):
		self.entity.position = self.base_position

fielders = [
	Fielder3D("Wicket Keeper"), Fielder3D("Slip"), Fielder3D("Gully"), Fielder3D("Point"), Fielder3D("Deep Point"),
	Fielder3D("Cover"), Fielder3D("Extra Cover"), Fielder3D("Mid-off"), Fielder3D("Mid-on"), Fielder3D("Deep Midwicket"),
]

# Scoring HUD
score = 0
wickets = 0
balls_in_over = 0
overs = 0
hud = Text(text='0.0  0/0', origin=(-.5, .5), position=(-.85, .45), scale=1.2)
info = Text(text='Space: run-up  Enter: swing  WASD: aim', origin=(-.5, .5), position=(-.85, .4), scale=.9)


def increment_score(boundary: bool = False, caught: bool = False):
	global score, wickets, balls_in_over, overs
	if boundary:
		score += 4
	elif caught:
		wickets += 1
	else:
		# award a single for now when play ends not by boundary/catch
		score += 1
	balls_in_over += 1
	if balls_in_over >= 6:
		overs += 1
		balls_in_over = 0
	hud.text = f"{overs}.{balls_in_over}  {score}/{wickets}"


def reset_ball():
	global ball_v, ball_spin, ball_bounced, runup_t, ball_live, state
	ball.position = Vec3(0,1,0)
	ball_v = Vec3(0,0,0)
	ball_spin = Vec3(0,0,0)
	ball_bounced = False
	runup_t = 0.0
	bowler.position = bowler_start
	ball_live = False
	state = 'IDLE'
	# Reset fielders to their base positions
	for f in fielders:
		f.reset()


def bowl():
	global ball_v, ball_spin, ball_live, state
	ball.position = bowler_release
	dir_vec = (Vec3(0,1,1) - ball.position).normalized()
	ball_v = dir_vec * 28
	ball_spin = Vec3(0, random.uniform(-2,2), random.uniform(-2,2))
	ball_live = True
	state = 'FLIGHT'


def hit_ball():
	global ball_v, ball_spin, state
	to_ball = ball.position - bat_pivot.world_position
	if to_ball.length() < 2.2:
		dir_local = Vec3(held_keys['d']-held_keys['a'], 0, held_keys['w']-held_keys['s'])
		if dir_local.length() == 0:
			dir_local = Vec3(0,0,1)
		dir_world = (bat_pivot.right * dir_local.x + bat_pivot.forward * dir_local.z).normalized()
		power = 24
		ball_v = dir_world * power + Vec3(0,9,0)
		ball_spin = Vec3(0, random.uniform(-3,3), random.uniform(-3,3))
		state = 'HIT'


def input(key):
	global swinging, swing_t, state, camera_flip
	if key == 'space':
		if state in ('IDLE','DEAD'):
			reset_ball()
		state = 'RUNUP'
	elif key == 'enter':
		if state == 'FLIGHT':
			swinging = True
			swing_t = 0.0
	elif key == 'c':
		camera_flip = not camera_flip


def update():
	global runup_t, swinging, swing_t, ball_v, ball_spin, ball_bounced, ball_live, state
	# Run-up
	if state == 'RUNUP':
		runup_t = min(1.0, runup_t + time.dt*0.6)
		bowler.position = lerp(bowler_start, bowler_release, runup_t)
		ball.position = bowler.position + Vec3(0,1.2,0)
		if runup_t >= 1.0:
			bowl()
	# Swing
	if swinging:
		swing_t += time.dt * swing_speed
		bat_pivot.rotation_y = -60 + min(1.0, swing_t) * 120
		if 0.3 < swing_t < 0.6 and state == 'FLIGHT':
			hit_ball()
		if swing_t >= 1.0:
			swinging = False
	# Ball physics
	if ball_live:
		# Integrate
		ball_v += ball_spin * 0.01
		ball_v += ball_gravity * time.dt
		ball.position += ball_v * time.dt
		# Ground collision and bounce (repeatable)
		if ball.position.y <= GROUND_Y and ball_v.y < 0:
			ball.position = Vec3(ball.position.x, GROUND_Y, ball.position.z)
			ball_v.y = -ball_v.y * RESTITUTION
			ball_v.x *= GROUND_FRICTION
			ball_v.z *= GROUND_FRICTION
			ball_bounced = True
		# Clamp to ground plane
		if ball.position.y < GROUND_Y:
			ball.position = Vec3(ball.position.x, GROUND_Y, ball.position.z)
			if abs(ball_v.y) < 0.1:
				ball_v.y = 0
		# Rolling friction after bounce when on ground
		if ball_bounced and ball.position.y <= GROUND_Y + 1e-3:
			ball_v.x *= ROLLING_FRICTION
			ball_v.z *= ROLLING_FRICTION
			# Stop when slow
			if Vec2(ball_v.x, ball_v.z).length() < STOP_SPEED and abs(ball_v.y) < 0.1:
				ball_live = False
				state = 'DEAD'
		# Fielders move to intercept and catch if close and ball low
		target = ball.position
		for f in fielders:
			f.move_towards(Vec3(target.x, 0, target.z), time.dt)
			if ball.position.y < 1.6 and (f.entity.position - Vec3(ball.position.x,0,ball.position.z)).length() < 1.2:
				ball_live = False
				state = 'DEAD'
				increment_score(caught=True)
				break
		# Boundary stop at realistic radius
		if Vec3(ball.position.x,0,ball.position.z).length() >= BOUNDARY_RADIUS:
			ball_live = False
			state = 'DEAD'
			increment_score(boundary=True)
	# Aim at ball
	bat_pivot.look_at(ball.position)
	# Keep camera behind the batter following their pivot, toggleable with 'c'
	cam_target = bat_pivot.world_position
	z_off = -8.0 if not camera_flip else 8.0
	look_ahead = 6.0 if not camera_flip else -6.0
	camera.position = cam_target + Vec3(0, 2.2, z_off)
	camera.rotation_z = 0
	camera.look_at(cam_target + Vec3(0, 1.2, look_ahead))


app.run()



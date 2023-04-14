import random
import sys
import time
from enum import Enum
from enum import auto
from typing import Union, Tuple

import pygame
import pymunk
import pymunk.pygame_util
from pymunk import Vec2d
from pygame.locals import RESIZABLE

"""
Ideas
- stochastic golf
  where you knock several hundred golf balls in order to see how many you need to reach the hole

Improvements
- modularize the entities and behaviors
  entities: make it possible to spawn balls from arbitrary locations
  behaviors: make it possible to attach player-movement to the balls, or the bricks
- Camera system
  HOWTO https://www.phind.com/search?cache=3dd266e2-5e53-4944-889f-4e84ba9141ff
"""

PYGAME_COLOR_WHITE = pygame.Color("white")
FONT_COLOR = PYGAME_COLOR_WHITE
WIDTH, HEIGHT = 1200, 600
DEFAULT_POSITION = 100, 300
DEFAULT_DIRECTION = 1000, 600
DIRECTION_TILT_RANGE_TUPLE = (-300, 300)
DRAW_FPS = True
TARGET_FPS = 120
COLLISION_TYPES = {
    "ball": 1,
    "brick": 2,
    "wall": 3,
}
BALL_ELASTICITY = 0.7
BRICK_ELASTICITY = 0.0000001
CULL_PERIOD_SEC = 1.0
CULL_POSITION = 10 * WIDTH  # NOTE: Removes any physics bodies positioned outside this coordinate (x or y)
DEBUG_LOG = False
DEBUG_CAPTURE_STATE = False
RANDOMIZE_BALL_SIZE = False
MOVE_DAMPEN_FACTOR = 0.9


class EventState(Enum):
    Mute = auto()
    MoveDown = auto()
    MoveRight = auto()
    MoveLeft = auto()
    MoveUp = auto()
    Run = auto()
    Stop = auto()
    Restart = auto()
    SpawnBall = auto()
    SpawnBricks = auto()
    Debug = auto()


DEFAULT_DRAWABLE_COLOR = pygame.color.THECOLORS.get("magenta")


class Drawable:
    def __init__(self, position=(0, 0)):
        self.position = position

    def draw(self, surface: pygame.Surface):
        pygame.draw.line(surface, DEFAULT_DRAWABLE_COLOR,
                         (self.position[0] - 10, self.position[1] - 10),
                         (self.position[0] + 10, self.position[1] + 10))
        pygame.draw.line(surface, DEFAULT_DRAWABLE_COLOR,
                         (self.position[0] + 10, self.position[1] - 10),
                         (self.position[0] - 10, self.position[1] + 10))


class Player(Drawable):
    def __init__(self, position=(0, 0)):
        super().__init__(position)


space = None
state = []
drawables = []
sfx = {}
ball_count = 0
player = Player()
DEFAULT_MUTE = False


class BlindSound:
    mute = DEFAULT_MUTE

    def __init__(self, filename):
        self.sound = None
        try:
            self.sound = pygame.mixer.Sound(filename)
        except FileNotFoundError:
            print(f"BlindSound: unable to load file: {filename}")
            pass

    def play(self, loops=0, maxtime=0, fade_ms=0):
        if self.mute is True:
            return
        if self.sound is not None:
            self.sound.play(loops, maxtime, fade_ms)

    def set_volume(self, value):
        if self.sound is not None:
            self.sound.set_volume(value)


def load_sfx():
    pygame.mixer.set_num_channels(32)

    global sfx
    sfx = {
        "brick": {
            "impact": [
                BlindSound("sfx/brick_sounds/impact/brick_impact_01.mp3"),
                BlindSound("sfx/brick_sounds/impact/brick_impact_03.mp3")
            ],
            "scrape": [
                BlindSound("sfx/brick_sounds/scrape/brick_scrape_02.mp3"),
            ]
        },
        "ball": {
            "bounce": [
                BlindSound("sfx/ball_sounds/bounce/rubber_ball_bounce_cement_04.wav"),
            ],
            "catch": [
                BlindSound("sfx/ball_sounds/catch/rubber_ball_catch_03.mp3"),
            ]
        }
    }

    sfx["brick"]["scrape"][0].set_volume(0.5)


def setup_level(space):
    """
    Populate with initial components
    :param space:
    """
    remove_balls_bricks(space)

    player.position = DEFAULT_POSITION
    drawables.append(player)

    fire_ball(space, player.position)

    # Spawn bricks

    one_brick = False
    if one_brick:
        brick_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        brick_body.position = 400, 300

        brick_shape = pymunk.Poly.create_box(brick_body, (20, 10))
        brick_shape.color = pygame.Color("brown")
        brick_shape.mass = 1

        space.add(brick_body, brick_shape)
    else:
        spawn_bricks(space)

    handle_brick_brick = space.add_collision_handler(COLLISION_TYPES["brick"], COLLISION_TYPES["brick"])
    handle_brick_brick.begin = brick_brick_collide

    handle_brick_ball = space.add_collision_handler(COLLISION_TYPES["brick"], COLLISION_TYPES["ball"])
    handle_brick_ball.begin = brick_ball_collide

    spawn_walls(space)


def spawn_ball(space: pymunk.Space, position: Union[Vec2d, Tuple[float, float]], direction):
    ball_body = pymunk.Body(1, float("inf"))
    ball_body.position = position

    ball_shape = create_ball_shape(ball_body, 5)

    ball_body.apply_impulse_at_local_point(Vec2d(*direction), (1, 1))

    space.add(ball_body, ball_shape)

    sfx["ball"]["catch"][0].play()

    global ball_count
    ball_count += 1


def create_ball_shape(ball_body, radius):
    ball_shape = pymunk.Circle(ball_body, radius)
    ball_shape.color = pygame.Color("pink")
    ball_shape.elasticity = BALL_ELASTICITY
    ball_shape.collision_type = COLLISION_TYPES["ball"]
    return ball_shape


def spawn_walls(space):
    line_radius = 20
    wall_left = 50
    wall_right = WIDTH - 50
    wall_top = 50
    wall_bottom = HEIGHT - 50
    static_lines = [
        pymunk.Segment(space.static_body, (wall_left, wall_bottom - 25),
                       (wall_right, wall_bottom + 25), line_radius),  # Bottom
        pymunk.Segment(space.static_body, (wall_left, wall_top),
                       (wall_right, wall_top), line_radius),  # Bottom
    ]
    for line in static_lines:
        line.color = pygame.Color("orange")
        line.elasticity = 1.0
        line.friction = 0.62
        line.collision_type = COLLISION_TYPES["wall"]
    space.add(*static_lines)
    handle_wall_ball = space.add_collision_handler(COLLISION_TYPES["wall"], COLLISION_TYPES["ball"])
    handle_wall_ball.begin = wall_ball_collide
    handle_wall_ball = space.add_collision_handler(COLLISION_TYPES["wall"], COLLISION_TYPES["brick"])
    handle_wall_ball.begin = wall_brick_collide


def spawn_bricks(space):
    brick_w = 40
    brick_height = 20
    brick_pad = 2

    for x in range(6, 8):
        x = x * (brick_w + brick_pad) + 100 + brick_height
        for y in range(0, 4):
            y = y * (brick_height + brick_pad) + 100 + brick_height
            brick_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
            brick_body.position = x, y
            brick_shape = pymunk.Poly.create_box(brick_body, (brick_w, brick_height))
            brick_shape.color = pygame.Color("brown")
            brick_shape.group = 1
            brick_shape.collision_type = COLLISION_TYPES["brick"]
            brick_shape.mass = 1
            brick_shape.elasticity = BRICK_ELASTICITY
            brick_shape.friction = 0.62
            space.add(brick_body, brick_shape)


def remove_balls_bricks(space):
    for s in space.shapes[:]:
        if s.body.body_type == pymunk.Body.DYNAMIC:
            space.remove(s.body, s)


def brick_brick_collide(arbiter, space, data):
    if arbiter.shapes[0].body.kinetic_energy > 40000:
        c = sfx["brick"]["impact"][0].play()
    elif arbiter.shapes[0].body.kinetic_energy > 10000:
        c = sfx["brick"]["impact"][1].play()
    elif arbiter.shapes[0].body.kinetic_energy > 500:
        c = sfx["brick"]["scrape"][0].play()
    return True


def brick_ball_collide(arbiter, space, data):
    if arbiter.shapes[1].body.kinetic_energy > 40000:
        c = sfx["ball"]["bounce"][0].play()
    return True


def wall_ball_collide(arbiter, space, data):
    if arbiter.shapes[1].body.kinetic_energy > 100000:
        c = sfx["ball"]["bounce"][0].play()
    return True


def wall_brick_collide(arbiter, space, data):
    if arbiter.shapes[1].body.kinetic_energy > 100000:
        c = sfx["brick"]["impact"][0].play()
    elif arbiter.shapes[1].body.kinetic_energy > 500:
        c = sfx["brick"]["scrape"][0].play()
    return True


def fire_ball(space, position):
    tilt = random.randrange(*DIRECTION_TILT_RANGE_TUPLE)
    ball_direction = (DEFAULT_DIRECTION[0], DEFAULT_DIRECTION[1] + tilt)
    if position is None:
        position = DEFAULT_POSITION
    spawn_ball(
        space,
        position,
        ball_direction,
    )


def draw_hud(clock, font, screen):
    if DRAW_FPS is True:
        blit_text(font, screen, "fps: " + str(clock.get_fps()), (0, 0))
    blit_text(font, screen, f"Balls: {ball_count}", (0, 15))

    blit_text(font, screen, "BRICK_KNOCKER", (WIDTH - 150, 0))
    blit_text(font, screen, "[K] to spawn more bricks, add [Shift] to spray", (5, HEIGHT - 50))
    blit_text(font, screen, "[Space] to spawn a ball, add [Shift] to spray. Arrows to move.", (5, HEIGHT - 35))
    blit_text(font, screen, "[R] to reset, [ESC] or [Q] to quit, [M] to mute", (5, HEIGHT - 20))


def draw_window(surface: pygame.Surface):
    for d in drawables:
        d.draw(surface)


def blit_text(font, screen, text, position):
    screen.blit(font.render(text, True, FONT_COLOR), position)


def cleanup_bodies(space):
    count = 0
    for s in space.shapes[:]:
        if s.body.body_type == pymunk.Body.DYNAMIC and (
                abs(s.body.position.y) > CULL_POSITION or abs(s.body.position.x > CULL_POSITION)
        ):
            space.remove(s.body, s)
            count += 1
    debug_print(f"Cleaned up {count} bodies")


def toggle_mute():
    BlindSound.mute = not BlindSound.mute


def debug_print(self, *args):
    if DEBUG_LOG:
        print(self, args)


def parse_events(running, space):
    """
    Extract events from user input. May return multiple events if non-terminal.

    :param running:
    :param space:
    :return: Terminal events as a single element list. Continuous events in a multiple element list.
    """
    result = []

    # Single events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return [EventState.Stop]  # Terminal
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                return [EventState.Stop]  # Terminal
            elif event.key == pygame.K_r:
                return [EventState.Restart]  # Terminal
            elif event.key == pygame.K_k:
                result.append(EventState.SpawnBricks)
            elif event.key == pygame.K_SPACE:
                result.append(EventState.SpawnBall)
            elif event.key == pygame.K_d:
                result.append(EventState.Debug)
            elif event.key == pygame.K_m:
                result.append(EventState.Mute)

    # Multi-events
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        result.append(EventState.MoveLeft)
    if keys[pygame.K_RIGHT]:
        result.append(EventState.MoveRight)
    if keys[pygame.K_UP]:
        result.append(EventState.MoveUp)
    if keys[pygame.K_DOWN]:
        result.append(EventState.MoveDown)

    mods = pygame.key.get_mods()
    if mods & pygame.KMOD_SHIFT:
        if keys[pygame.K_SPACE]:
            result.append(EventState.SpawnBall)
        if keys[pygame.K_k]:
            result.append(EventState.SpawnBricks)

    return result


def main():
    running = True

    # PyGame init
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)

    w, h = pygame.display.get_surface().get_size()

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)
    load_sfx()

    # Physics stuff
    space = pymunk.Space()
    space.gravity = (0, 900)
    space.damping = 0.5

    # pymunk.pygame_util.positive_y_is_up = True
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    global state

    # Start game
    setup_level(space)
    last_time_culled = 0.0
    move_dir = (0, 0)

    while running:
        # Cleanup any distant bodies
        current_time = time.thread_time()
        if (current_time - last_time_culled) > CULL_PERIOD_SEC:
            cleanup_bodies(space)
            last_time_culled = current_time

        # TIP: https://learnpython.com/blog/python-match-case-statement/
        events = parse_events(running, space)
        for event in events:
            match event:
                case EventState.Run:
                    pass
                case EventState.Restart:
                    setup_level(space)
                case EventState.Stop:
                    running = False
                case EventState.SpawnBall:
                    fire_ball(space, player.position)
                case EventState.SpawnBricks:
                    spawn_bricks(space)
                case EventState.Debug:
                    cleanup_bodies(space)
                case EventState.Mute:
                    toggle_mute()
                case EventState.MoveUp:
                    move_dir = move_dir[0] + 0, move_dir[1] - 1
                case EventState.MoveDown:
                    move_dir = move_dir[0] + 0, move_dir[1] + 1
                case EventState.MoveLeft:
                    move_dir = move_dir[0] - 1, move_dir[1] + 0
                case EventState.MoveRight:
                    move_dir = move_dir[0] + 1, move_dir[1] + 0

        # Move player
        player.position = (player.position[0] + move_dir[0], player.position[1] + move_dir[1])

        # Clear screen
        screen.fill(pygame.Color("darkgrey"))

        # Draw objects
        space.debug_draw(draw_options)
        draw_window(screen)

        if DEBUG_CAPTURE_STATE:
            state = []
            for x in space.shapes:
                s = "%s %s %s" % (x, x.body.position, x.body.velocity)
                state.append(s)

        # Update physics
        fps = TARGET_FPS
        dt = 1.0 / fps
        space.step(dt)

        move_dir = move_dir[0] * MOVE_DAMPEN_FACTOR, move_dir[1] * MOVE_DAMPEN_FACTOR

        # Update objects
        if RANDOMIZE_BALL_SIZE:
            def randomize_circle_radius(shape):
                new_radius = shape.radius + random.uniform(-0.4, 0.4)
                replace_shape(shape, create_ball_shape(shape.body, new_radius))
            circles = [shape for shape in space.shapes if isinstance(shape, pymunk.shapes.Circle)]
            list(map(randomize_circle_radius, circles))

        # Info and flip screen
        draw_hud(clock, font, screen)

        pygame.display.flip()
        clock.tick(fps)


def replace_shape(shape, with_shape):
    my_space = shape.space
    shape.space.remove(shape)
    shape.body = None
    my_space.add(with_shape)
    return with_shape


if __name__ == "__main__":
    sys.exit(main())

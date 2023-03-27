import random
import sys
from typing import NamedTuple, Union, Tuple, Callable
from enum import Enum
import time

import pygame

import pymunk
import pymunk.pygame_util
from pymunk import Vec2d

PYGAME_COLOR_WHITE = pygame.Color("white")
FONT_COLOR = PYGAME_COLOR_WHITE
WIDTH, HEIGHT = 600, 600
DEFAULT_POSITION = 100, 300
DEFAULT_DIRECTION = 1000, -600
DRAW_FPS = True
COLLISION_TYPES = {
    "ball": 1,
    "brick": 2,
}
BALL_ELASTICITY = 0.7
BRICK_ELASTICITY = 0.0000001
CULL_PERIOD_SEC = 1.0
CULL_POSITION = 10 * WIDTH  # NOTE: Removes any physics bodies positioned outside this coordinate (x or y)
DEBUG_LOG = False


class EventState(Enum):
    Run = 1
    Stop = 2
    Restart = 3
    SpawnBall = 4
    SpawnBricks = 5
    Debug = 10


space = None
state = []


# class Ball(pygame.sprite.Sprite):
#     def __init__(self, body, shape, position, direction):
#         super().__init__()
#         global space
#
#         self.body = body
#         self.shape = shape
#
#         self.body.position = position
#
#         self.shape.color = pygame.Color("green")
#         self.shape.elasticity = BALL_ELASTICITY
#         # self.shape.friction
#         self.shape.collision_type = COLLISION_TYPES["ball"]
#
#         self.body.apply_impulse_at_local_point(Vec2d(*direction))
#
#         space.add(self.body, self.shape)


def spawn_ball(space: pymunk.Space, position: Union[Vec2d, Tuple[float, float]], direction):
    ball_body = pymunk.Body(1, float("inf"))
    ball_body.position = position

    ball_shape = pymunk.Circle(ball_body, 5)
    ball_shape.color = pygame.Color("green")
    ball_shape.elasticity = BALL_ELASTICITY
    ball_shape.collision_type = COLLISION_TYPES["ball"]

    ball_body.apply_impulse_at_local_point(Vec2d(*direction), (1, 1))

    space.add(ball_body, ball_shape)


def setup_level(space, player_body=None):
    """
    Populate with initial components
    :param space:
    :param player_body:
    """
    # Remove balls and bricks
    for s in space.shapes[:]:
        if s.body.body_type == pymunk.Body.DYNAMIC:
            space.remove(s.body, s)

    # Spawn a ball for the player to have something to play with

    fire_ball(player_body, space)

    # Spawn bricks

    # Brick drop
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

    # # Make bricks be removed when hit by ball
    # def remove_brick(arbiter, space, data):
    #     brick_shape = arbiter.shapes[0]
    #     space.remove(brick_shape, brick_shape.body)
    #
    # h = space.add_collision_handler(collision_types["brick"], collision_types["ball"])
    # h.separate = remove_brick

    # Game area
    # walls
    line_radius = 20
    static_lines = [
        pymunk.Segment(space.static_body, (50, 50), (550, 50), line_radius),  # Top
        # pymunk.Segment(space.static_body, (550, 550), (550, 50), line_radius), # Right
        # pymunk.Segment(space.static_body, (50, 550), (50, 50), line_radius), # Left
        pymunk.Segment(space.static_body, (50, 550), (550, 550), line_radius),  # Bottom

    ]
    for line in static_lines:
        line.color = pygame.Color("orange")
        line.elasticity = 1.0
        line.friction = 0.62

    space.add(*static_lines)


def fire_ball(player_body, space):
    tilt = random.randrange(-200, 200)
    ball_direction = (DEFAULT_DIRECTION[0], DEFAULT_DIRECTION[1] + tilt)
    spawn_ball(
        space,
        DEFAULT_POSITION if player_body is None else player_body.position + (0, 40),
        ball_direction,
    )


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


def draw_hud(clock, font, screen):
    if DRAW_FPS is True:
        blit_text(font, screen, "fps: " + str(clock.get_fps()), (0, 0))

    blit_text(font, screen, "BRICK_KNOCKER", (WIDTH - 150, 0))
    blit_text(font, screen, "[K] to spawn more bricks, add [Shift] to spray", (5, HEIGHT - 50))
    blit_text(font, screen, "[Space] to spawn a ball, add [Shift] to spray", (5, HEIGHT - 35))
    blit_text(font, screen, "[R] to reset, [ESC] or [Q] to quit", (5, HEIGHT - 20))


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
    if DEBUG_LOG:
        print(f"Cleaned up {count} bodies")


def parse_events(player_body, running, space):
    """
    Extract events from user input. May return multiple events if non-terminal.

    :param player_body:
    :param running:
    :param space:
    :return: Terminal events as a single element list. Continuous events in a multiple element list.
    """
    result = []

    # Single events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return [EventState.Stop]  # Terminal
        elif event.type == pygame.KEYDOWN and (
                event.key in [pygame.K_ESCAPE, pygame.K_q]
        ):
            return [EventState.Stop]  # Terminal
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            return [EventState.Restart]  # Terminal
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_k:
            result.append(EventState.SpawnBricks)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            result.append(EventState.SpawnBall)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            result.append(EventState.Debug)

    # Multi-events
    mods = pygame.key.get_mods()
    if mods & pygame.KMOD_SHIFT:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            result.append(EventState.SpawnBall)
        if keys[pygame.K_k]:
            result.append(EventState.SpawnBricks)

    return result


def main():
    running = True

    # PyGame init
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)

    # Physics stuff
    space = pymunk.Space()
    space.gravity = (0, -900)
    space.damping = 0.5

    pymunk.pygame_util.positive_y_is_up = True
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # ### Player ship
    # player_body = pymunk.Body(500, float("inf"))
    player_body = None
    # player_body.position = 300, 100
    #
    # player_shape = pymunk.Segment(player_body, (-50, 0), (50, 0), 8)
    # player_shape.color = pygame.Color("red")
    # player_shape.elasticity = 1.0
    # player_shape.collision_type = collision_types["player"]

    # def pre_solve(arbiter, space, data):
    #     # We want to update the collision normal to make the bounce direction
    #     # dependent of where on the paddle the ball hits. Note that this
    #     # calculation isn't perfect, but just a quick example.
    #     set_ = arbiter.contact_point_set
    #     if len(set_.points) > 0:
    #         player_shape = arbiter.shapes[0]
    #         width = (player_shape.b - player_shape.a).x
    #         delta = (player_shape.body.position - set_.points[0].point_a).x
    #         normal = Vec2d(0, 1).rotated(delta / width / 2)
    #         set_.normal = normal
    #         set_.points[0].distance = 0
    #     arbiter.contact_point_set = set_
    #     return True
    #
    # h = space.add_collision_handler(collision_types["player"], collision_types["ball"])
    # h.pre_solve = pre_solve

    # # restrict movement of player to a straigt line
    # move_joint = pymunk.GrooveJoint(
    #     space.static_body, player_body, (100, 100), (500, 100), (0, 0)
    # )
    # space.add(player_body, player_shape, move_joint)
    global state
    # Start game
    # setup_level(space, player_body)
    setup_level(space)
    last_time_culled = 0.0

    while running:
        # Cleanup any distant bodies
        current_time = time.thread_time()
        if (current_time - last_time_culled) > CULL_PERIOD_SEC:
            cleanup_bodies(space)
            last_time_culled = current_time

        # TIP: https://learnpython.com/blog/python-match-case-statement/
        events = parse_events(player_body, running, space)
        for event in events:
            match event:
                case EventState.Run:
                    pass
                case EventState.Restart:
                    setup_level(space, None)
                case EventState.Stop:
                    running = False
                case EventState.SpawnBall:
                    fire_ball(player_body, space)
                case EventState.SpawnBricks:
                    spawn_bricks(space)
                case EventState.Debug:
                    cleanup_bodies(space)

        ### Clear screen
        screen.fill(pygame.Color("darkgrey"))

        ### Draw objects
        space.debug_draw(draw_options)

        ###
        state = []
        for x in space.shapes:
            s = "%s %s %s" % (x, x.body.position, x.body.velocity)
            state.append(s)

        ### Update physics
        fps = 60
        dt = 1.0 / fps
        space.step(dt)

        ### Info and flip screen
        draw_hud(clock, font, screen)

        pygame.display.flip()
        clock.tick(fps)


if __name__ == "__main__":
    sys.exit(main())

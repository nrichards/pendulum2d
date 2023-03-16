"""
IDEAS
On collision
  draw a line?
  explode any red ball?
"""

import random

import pygame
import pygame.freetype
import pymunk
from typing import Any


pygame.init()
pygame.font.init()

# Environment
DISPLAY_SIZE = 600, 600
display = pygame.display.set_mode(DISPLAY_SIZE)
DISPLAY_COLOR = (255, 255, 255)
clock = pygame.time.Clock()
space = pymunk.Space()
FPS = 60
BALL_RADIUS = 10
BALL_POOL_COLLISION_TYPE = 1
BALL_SPECIAL_COLLISION_TYPE = 2
BALL_COLOR = (255, 0, 0)
BALL_COLORS = {BALL_SPECIAL_COLLISION_TYPE: (0, 0, 255)}
GAME_FONT = pygame.freetype.SysFont("None", 24)
hit_count = 0

# Rules
BIVM = BALL_INITIAL_VELOCITY_MAGNITUDE = 80
HIT_COUNT_TO_EXPLODE = 10
COUNT_BALL_DROPPED = 200
BALL_ELASTICITY_DEFAULT = 1
BALL_ELASTICITY_BOOM = 2
BALL_DAMPENING_FACTOR = 0.9975


def convert_coordinates(point):
    return int(point[0]), DISPLAY_SIZE[0] - int(point[1])


class Ball:
    def __init__(self, x, y, collision_type):
        self.body = pymunk.Body()
        self.body.position = x, y
        self.body.velocity = random.uniform(-BIVM, BIVM), random.uniform(-BIVM, BIVM)

        def limit_velocity(body: pymunk.Body, gravity, damping, dt):
            pymunk.Body.update_velocity(body, gravity, damping, dt)
            body.velocity = body.velocity * BALL_DAMPENING_FACTOR
        self.body.velocity_func = limit_velocity

        self.shape = pymunk.Circle(self.body, BALL_RADIUS)
        self.shape.elasticity = BALL_ELASTICITY_DEFAULT
        self.shape.density = 1
        self.shape.collision_type = collision_type
        space.add(self.body, self.shape)

    def draw(self):
        pygame.draw.circle(display,
                           BALL_COLORS.setdefault(self.collision_type, BALL_COLOR),
                           convert_coordinates(self.body.position),
                           BALL_RADIUS)

    @property
    def collision_type(self):
        return self.shape.collision_type


class Pit:
    def __init__(self):
        min_dim = 5
        max_dim = DISPLAY_SIZE[0] - 5
        static_lines = [
            pymunk.Segment(space.static_body, (min_dim, min_dim), (min_dim, max_dim), 20),
            pymunk.Segment(space.static_body, (min_dim, min_dim), (max_dim, min_dim), 20),
            pymunk.Segment(space.static_body, (max_dim, max_dim), (min_dim, max_dim), 20),
            pymunk.Segment(space.static_body, (max_dim, max_dim), (max_dim, min_dim), 20),
        ]
        for line in static_lines:
            line.color = pygame.Color("lightgray")
            line.elasticity = 1.0

        space.add(*static_lines)


def collide_begin(arb: pymunk.Arbiter, handler_space: str, data: Any):
    global hit_count

    hit_count += 1
    if (hit_count % HIT_COUNT_TO_EXPLODE) == 0:
        begin_explode(data['special_ball'])
    return True


def collide_end(arb: pymunk.Arbiter, handler_space: str, data: Any):
    if data:
        end_explode(data['special_ball'])
    return True


def begin_explode(special_ball: Ball):
    special_ball.shape.elasticity = BALL_ELASTICITY_BOOM


def end_explode(special_ball: Ball):
    special_ball.shape.elasticity = BALL_ELASTICITY_DEFAULT


def game():
    Pit()

    balls = [Ball(random.randint(0, DISPLAY_SIZE[0]), random.randint(0, DISPLAY_SIZE[1]), BALL_POOL_COLLISION_TYPE)
             for _ in range(COUNT_BALL_DROPPED)]

    special_ball = Ball(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2, BALL_SPECIAL_COLLISION_TYPE)
    special_ball.shape.elasticity = 1
    balls.append(special_ball)
    handler = space.add_collision_handler(BALL_POOL_COLLISION_TYPE, BALL_SPECIAL_COLLISION_TYPE)
    handler.begin = lambda arbiter, game_space, data: collide_begin(arbiter, game_space, {
        "special_ball": special_ball
    })

    handler.separate = collide_end

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_b:
                    more_balls = [Ball(random.randint(0, DISPLAY_SIZE[0]), random.randint(0, DISPLAY_SIZE[1]),
                                       BALL_POOL_COLLISION_TYPE) for _ in range(COUNT_BALL_DROPPED)]
                    balls.extend(more_balls)

        display.fill(DISPLAY_COLOR)

        [ball.draw() for ball in balls]

        GAME_FONT.render_to(display, (40, 40), "More [B]alls", (0, 0, 0))
        GAME_FONT.render_to(display, (40, 60), "Hit Count: " + str(hit_count), (0, 0, 0))

        pygame.display.update()
        clock.tick(FPS)
        space.step(1 / FPS)


game()

pygame.quit()

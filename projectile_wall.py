import random

import pygame
import pygame.freetype
import pymunk

pygame.init()
pygame.font.init()

DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 600
display = pygame.display.set_mode((DISPLAY_WIDTH,DISPLAY_HEIGHT))
DISPLAY_COLOR = (255, 255, 255)
clock = pygame.time.Clock()
space = pymunk.Space()
FPS = 60
BALL_RADIUS = 10
BALL_COLOR = (255, 0, 0)
BALL_COLORS = {2: (0, 0, 255)}
BIVM = BALL_INITIAL_VELOCITY_MAGNITUDE = 400
GAME_FONT = pygame.freetype.SysFont("None", 24)

def convert_coordinates(point):
    return int(point[0]), DISPLAY_HEIGHT - int(point[1])

class Ball():
    def __init__(self, x, y, collision_type, up = 1):
        self.body = pymunk.Body()
        self.body.position = x, y
        self.body.velocity = random.uniform(-BIVM, BIVM), random.uniform(-BIVM, BIVM)
        # self.body.velocity = 0, up*100
        self.shape = pymunk.Circle(self.body, BALL_RADIUS)
        self.shape.elasticity = 1
        self.shape.density = 1
        self.shape.collision_type = collision_type
        space.add(self.body, self.shape)
    def draw(self):
        x, y = self.body.position
        pygame.draw.circle(display,
                           BALL_COLORS.setdefault(self.collision_type, BALL_COLOR),
                           convert_coordinates(self.body.position),
                           BALL_RADIUS)
    @property
    def collision_type(self):
        return self.shape.collision_type

def collide(arbiter, space, data):
    print("collide")
    return True

def create_balls():
    return Ball(100, 100, 1), Ball(100, 500, 2, -1)

def game():
    ball_pool_collision_type = 1
    balls = [Ball(random.randint(0, DISPLAY_WIDTH), random.randint(0, DISPLAY_HEIGHT), ball_pool_collision_type) for i in range(100) ]
    # ball, ball_2 = create_balls()
    #
    # handler = space.add_collision_handler(ball.collision_type, ball_2.collision_type)
    # handler.separate = collide
    ball_special_collision_type = 2
    balls.append(Ball(400, 400, ball_special_collision_type))
    handler = space.add_collision_handler(ball_pool_collision_type, ball_special_collision_type)
    handler.begin = collide
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    # ball, ball_2 = create_balls()
                    # balls = [Ball(random.randint(0, DISPLAY_WIDTH), random.randint(0, DISPLAY_HEIGHT), ct) for i in range(100)]
                    more_balls = [Ball(random.randint(0, DISPLAY_WIDTH), random.randint(0, DISPLAY_HEIGHT), ball_pool_collision_type) for i in range(100)]
                    balls.extend(more_balls)
        display.fill(DISPLAY_COLOR)

        GAME_FONT.render_to(display, (40, 40), "More [B]alls", (0, 0, 0))

        # ball.draw()
        # ball_2.draw()
        [ball.draw() for ball in balls]

        pygame.display.update()
        clock.tick(FPS)
        space.step(1/FPS)

game()
pygame.quit()

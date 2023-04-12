import pygame
import pymunk
import pymunk.pygame_util

pygame.init()

WIDTH = 600
HEIGHT = 800

display = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()
space = pymunk.Space()
space.gravity = (0, 300)
FPS = 120

def game():
    # The brick
    spawn_ball()

    # Walls
    line_radius = 20
    wall_left = 50
    wall_right = WIDTH - 50
    wall_bottom = 50
    wall_top = HEIGHT - 50
    static_lines = [
        pymunk.Segment(space.static_body, (wall_left, wall_top + 50),
                       (wall_right, wall_top), line_radius),  # Top
    ]
    for line in static_lines:
        line.color = pygame.Color("orange")
        line.elasticity = 1.0
        line.friction = 0.62
    space.add(*static_lines)

    # Utility
    options = pymunk.pygame_util.DrawOptions(display)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and (
                    event.key in [pygame.K_SPACE]):
                spawn_ball()
                
        # YOUR CODE HERE
        display.fill(pygame.Color("white"))
        space.debug_draw(options)
        pygame.display.update()
        clock.tick(FPS)
        space.step(1/FPS)


def spawn_ball():
    brick_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
    brick_body.position = 300, 100
    brick_shape = pymunk.Poly.create_box(brick_body, (20, 10))
    brick_shape.color = pygame.Color("pink")
    brick_shape.mass = 1
    space.add(brick_body, brick_shape)


game()
pygame.quit()

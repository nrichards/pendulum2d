# See "BROKEN" below, for issue. [pymunk 6.4.0, pygame 2.2.0, python 3.9 macos silicon.]
#   Should draw a box.
#   Instead, at the third frame, pymunk forgets the vertices (NaN) of brick_shape for debug_draw.
# May be https://github.com/viblo/pymunk/issues/183

import sys
import pygame
import pymunk
import pymunk.pygame_util


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()
    running = True
    font = pygame.font.SysFont("Arial", 16)

    space = pymunk.Space()

    # BROKEN
    #  Use DYNAMIC body_type to break:
    #   "pygame_util.py:return round(p[0]), surface.get_height() - round(p[1])"
    #   "ValueError: cannot convert float NaN to integer"
    #  Change to KINEMATIC to fix.
    brick_body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)

    brick_body.position = 400, 300
    brick_shape = pymunk.Poly.create_box(brick_body, (20, 10))
    brick_shape.color = pygame.Color("brown")
    brick_shape.mass = 1
    space.add(brick_body, brick_shape)

    pymunk.pygame_util.positive_y_is_up = True
    draw_options = pymunk.pygame_util.DrawOptions(screen) # ALT: Use SpaceDebugDrawOptions() to log nan,nan at frame 3
    draw_options.flags = pymunk.SpaceDebugDrawOptions.DRAW_SHAPES | pymunk.SpaceDebugDrawOptions.DRAW_COLLISION_POINTS
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and (
                    event.key in [pygame.K_ESCAPE, pygame.K_q]
            ):
                running = False

        screen.fill(pygame.Color("darkgrey"))

        # Draw stuff
        space.debug_draw(draw_options)

        # Update physics
        fps = 60
        dt = 1.0 / fps
        space.step(dt)

        screen.blit(
            font.render("BRICK_KNOCKER. [Q]uit", True, pygame.Color("white")),
            (0, 0),
        )
        pygame.display.flip()
        clock.tick(fps)


if __name__ == "__main__":
    sys.exit(main())

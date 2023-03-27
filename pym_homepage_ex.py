import pymunk               # Import pymunk..
import pymunk.pygame_util

import pygame
pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()

pymunk.pygame_util.positive_y_is_up = True

space = pymunk.Space()      # Create a Space which contain the simulation
# space.gravity = 0,-981      # Set its gravity
space.gravity = 0,-20      # Set its gravity

body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)        # Create a Body
body.position = 50,100      # Set the position of the body

poly = pymunk.Poly.create_box(body) # Create a box shape and attach to body
poly.mass = 10              # Set the mass on the shape
space.add(body, poly)       # Add both body and shape to the simulation

print_options = pymunk.SpaceDebugDrawOptions() # For easy printing

for _ in range(100):        # Run simulation 100 steps in total
    space.step(0.02)        # Step the simulation one step forward
    space.debug_draw(print_options) # Print the state of the simulation

draw_options = pymunk.pygame_util.DrawOptions(screen)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ### Clear screen
    screen.fill(pygame.Color("darkgrey"))
    space.debug_draw(draw_options)

    ### Update physics
    fps = 60
    dt = 1.0 / fps
    space.step(dt)

    pygame.display.flip()
    clock.tick(fps)

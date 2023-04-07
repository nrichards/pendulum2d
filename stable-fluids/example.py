import numpy as np
from PIL import Image
from scipy.special import erf
# NICK
import pygame
import time

from fluid import Fluid

# RESOLUTION = 500, 500
# RESOLUTION = 150, 150  # 50% of 60FPS budget
RESOLUTION = 100, 100  # 25%
# RESOLUTION = 50, 50  # 8%
DURATION = 200

INFLOW_PADDING = 50
INFLOW_DURATION = 60
INFLOW_RADIUS = 8
INFLOW_VELOCITY = 1
INFLOW_COUNT = 5

# NICK
pygame.init()
screen = pygame.display.set_mode((RESOLUTION[0], RESOLUTION[1]), pygame.RESIZABLE)
start_time = time.time()

print('Generating fluid solver, this may take some time.')
fluid = Fluid(RESOLUTION, 'dye')

center = np.floor_divide(RESOLUTION, 2)
r = np.min(center) - INFLOW_PADDING

points = np.linspace(-np.pi, np.pi, INFLOW_COUNT, endpoint=False)
points = tuple(np.array((np.cos(p), np.sin(p))) for p in points)
normals = tuple(-p for p in points)
points = tuple(r * p + center for p in points)

inflow_velocity = np.zeros_like(fluid.velocity)
inflow_dye = np.zeros(fluid.shape)
for p, n in zip(points, normals):
    mask = np.linalg.norm(fluid.indices - p[:, None, None], axis=0) <= INFLOW_RADIUS
    inflow_velocity[:, mask] += n[:, None] * INFLOW_VELOCITY
    inflow_dye[mask] = 1

end_time = time.time()
duration = end_time - start_time
print(f"FIRST duration {duration}")

frames = []
for f in range(DURATION):

    start_time = time.time()

    # print(f'Computing frame {f + 1} of {DURATION}.')
    if f <= INFLOW_DURATION:
        fluid.velocity += inflow_velocity
        fluid.dye += inflow_dye

    curl = fluid.step()[1]
    # Using the error function to make the contrast a bit higher.
    # Any other sigmoid function e.g. smoothstep would work.
    curl = (erf(curl * 2) + 1) / 4

    color = np.dstack((curl, np.ones(fluid.shape), fluid.dye))
    color = (np.clip(color, 0, 1) * 255).astype('uint8')
    frames.append(Image.fromarray(color, mode='HSV').convert('RGB'))

    # NICK
    pygame.event.get()
    image = frames[len(frames) - 1]
    py_image = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    screen.blit(py_image, (0, 0))

    end_time = time.time()
    duration = end_time - start_time
    print(f"duration {duration}")

    pygame.display.flip()

print('Saving simulation result.')
frames[0].save('example.gif', save_all=True, append_images=frames[1:], duration=20, loop=0)

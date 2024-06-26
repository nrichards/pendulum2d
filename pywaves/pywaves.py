#!python
# Dependencies: pygame
"""
/***************************************************************************
	Author			:Charles Brissac

	Email			:cdbrissac (at) gmail.com

	License			:Apache 2.0

 ***************************************************************************/
"""

import pygame
import math
from pygame.locals import *
from solver import *

DEBUG = True
WIN_X = 330
WIN_Y = 330

sf = 1000.

# http://graphics.cs.cmu.edu/nsp/course/15-464/Fall09/papers/StamFluidforGames.pdf
class PyWaves:

    def __init__(self):
        self.t_el = 0.0
        self.size = (N + 2) * (N + 2)
        pygame.display.init()
        self.screen = pygame.display.set_mode((WIN_X, WIN_Y))
        self.bkg = pygame.Surface(self.screen.get_size())
        self.bkg = self.bkg.convert()
        self.bkg.fill((155, 155, 155))
        pygame.display.flip()

        pygame.event.set_blocked(MOUSEMOTION)
        pygame.display.set_caption("PyWaves")
        self.clock = pygame.time.Clock()

        self.u = []
        self.v = []
        self.u_prev = []
        self.v_prev = []

        self.RUNNING = True
        self.run()

    def clear_data(self):
        for sidx in range(self.size):
            self.u[sidx] = 0.
            self.v[sidx] = 0.
            self.u_prev[sidx] = 0.
            self.v_prev[sidx] = 0.

    def allocate_data(self):
        for sidx in range(self.size):
            self.u.append(0.)
            self.v.append(0.)
            self.u_prev.append(0.)
            self.v_prev.append(0.)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == KEYDOWN and e.key == K_ESCAPE: return False
        return True

    def run(self):

        self.allocate_data()
        self.clear_data()

        while self.RUNNING:
            # raw_input()
            self.RUNNING = self.handle_events()
            self.u, self.v, self.u_prev, self.v_prev = velocity_step(self.u, self.v, self.u_prev, self.v_prev)
            self.t_el += dt
            self.update()

    def update(self):

        self.bkg.fill((155, 155, 155))
        self.screen.blit(self.bkg, (0, 0))

        self.render_grid(WIN_X, WIN_Y)

        pygame.display.flip()
        print("\r%03.1f" % self.t_el)

    def render_grid(self, WIN_X, WIN_Y):
        dx = WIN_X / (N + 2)
        dy = WIN_Y / (N + 2)
        vcolor = (0, 0, 255)
        for i in range(1, N):
            for j in range(1, N):
                xc = (i + 0.5) * dx
                yc = (j + 0.5) * dy
                pygame.draw.line(self.screen, vcolor, (xc, yc),
                                 (xc + sf * self.u[IX(i, j)], yc + sf * self.v[IX(i, j)]))


if __name__ == '__main__':
    x = PyWaves()

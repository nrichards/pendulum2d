import pygame
import pymunk

pygame.init()

display = pygame.display.set_mode((600,600))
clock = pygame.time.Clock()
space = pymunk.Space()
FPS = 60

def game():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        # YOUR CODE HERE
        pygame.display.update()
        clock.tick(FPS)
        space.step(1/FPS)

game()
pygame.quit()

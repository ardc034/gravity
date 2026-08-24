import pygame
from grav_eng import Body, update
from typing import List

WIDTH, HEIGHT = 1000, 800
FPS = 60

BLACK  = (10, 10, 12)
YELLOW = (253, 184, 19)
GREEN  = (27, 201, 53)
BLUE   = (67, 144, 198)
RED    = (220, 76, 70)
WHITE  = (240, 240, 240)

class System:
    '''System of bodies interacting (only) gravitationally'''

    def __init__(self, bodies: List[Body] = 
                 [Body(WIDTH / 2, HEIGHT / 2, 0.0, 0.0, 5000.0, 18, YELLOW)]):
        self.bodies = bodies

    def draw_system(self, surf: pygame.Surface):
        '''Draws the system on the screen'''
        surf.fill(BLACK)
        for body in self.bodies:
            body.draw(surf)

    def update_system(self):
        '''Updates locations and velocities of every body in the system'''
        update(self.bodies)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("circles go brrr")
    clock = pygame.time.Clock()

    planets = [
        Body(450, 400, 0, 40, 333000, 20, YELLOW),       # sun 1
        Body(550, 400, 0, -40, 333000, 20, YELLOW),       # sun 2
        #Body(500, 400, 0, 0, 666000, 40, YELLOW),
        Body(100, 400, 0, 40, 1, 6, BLUE),            # blue
        Body(700, 400, 0, -60, 1, 6, RED),             # red
        Body(500, 700, 40, 0, 1, 6, GREEN)
    ]

    sim_universe = System(planets)

    running = True
    paused = False
    while running:
        clock.tick(FPS)
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

        if not paused:
            sim_universe.update_system()
            sim_universe.draw_system(screen)
            pygame.display.flip()

    pygame.quit()
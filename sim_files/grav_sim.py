import pygame
from typing import List

from grav_eng import Body, update, handle_collisions
from grav_dia import *
from energy_graph import EnergyGraph


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

    def draw_system(self, surf: pygame.Surface, camera: Camera):
        '''Draws the system on the screen'''
        surf.fill(BLACK)
        for body in self.bodies:
            body.draw(surf, camera)

    def update_system(self):
        '''Updates locations and velocities of every body in the system'''
        update(self.bodies)
        self.bodies = handle_collisions(self.bodies)



class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.offset = np.array([0.0, 0.0])
        self.dragging = False
        self.last_mouse_pos = np.array([None])

    def wts(self, pos): # world to screen
        return (pos - self.offset) * self.zoom

    def stw(self, pos): # screen to world
        return (pos / self.zoom) + self.offset



if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("circles go brrr")
    clock = pygame.time.Clock()

    camera = Camera()
    energy_graph = EnergyGraph()
    
    planets = [
        #Body(100, 400, 0, 40, 1, 6, BLUE),            # blue
        Body(450, 400, 0, 45, 333000, 20, YELLOW),       # sun 1
        Body(550, 400, -20, -45, 333000, 20, BLUE),       # sun 2
        Body(100, 400, 0, 40, 1, 6, BLUE),            # blue
        Body(700, 400, 0, -60, 1, 6, RED),             # red
        Body(500, 700, 40, 0, 1, 6, GREEN)#,
        #Body(100, 100, 100, 100, 100, 3, WHITE)
    ]

    i_e = total_energy(planets)


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
            elif event.type == pygame.MOUSEWHEEL:
                #Zoom
                camera.zoom *= 1.1 ** event.y

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:   # left click
                    camera.dragging = True
                    camera.last_mouse_pos = np.array(pygame.mouse.get_pos(), dtype=float)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    camera.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if camera.dragging:
                    mouse_pos = np.array(event.pos, dtype=float)
                    camera.offset -= (mouse_pos - camera.last_mouse_pos) / camera.zoom
                    camera.last_mouse_pos = mouse_pos

        if not paused:
            sim_universe.update_system()

        sim_universe.draw_system(screen, camera)

        ke, pe = draw_panel(screen, sim_universe, i_e)
        total = ke + pe
        time = pygame.time.get_ticks() / 1000

        energy_graph.update(total, ke, pe, time)

        pygame.display.flip()

    pygame.quit()
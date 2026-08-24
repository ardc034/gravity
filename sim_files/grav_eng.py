import numpy as np
import pygame
from typing import List

G = 1.0
DT = 0.1

class Body:
    '''Celestial object '''

    def __init__(self, 
                 x: float = 0, 
                 y: float = 0, 
                 vx: float = 0, 
                 vy: float = 0, 
                 mass: float = 10.0, 
                 radius: int = 6, 
                 color: tuple = (240, 240, 240)
                 ) -> None:
        self.pos: np.ndarray = np.array([x, y], dtype=float)
        self.vel: np.ndarray = np.array([vx, vy], dtype=float)
        self.mass: float = mass
        self.radius: int = radius
        self.color: tuple = color

    def draw(self, surf: pygame.Surface, camera):
        '''Draws the body on the screen'''
        screen_pos = camera.wts(self.pos)
        pygame.draw.circle(surf, self.color, screen_pos.astype(int), int(self.radius * camera.zoom))


def update(bodies: List[Body]):
    '''Finds the net force vector on each body'''
    n = len(bodies)

    forces = [np.array([0.0, 0.0]) for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):

            pos_i = bodies[i].pos
            pos_j = bodies[j].pos

            dist = float(np.linalg.norm(pos_j - pos_i))

            if dist < 5:
                continue

            epsilon = 2.0 # Prevents infinite force at close distances
            mag = G * (bodies[i].mass * bodies[j].mass) / (dist**2 + epsilon**2)

            direction = (pos_j - pos_i) / dist

            f = mag * direction
            forces[i] += f
            forces[j] -= f
    for i, body in enumerate(bodies):
        a = forces[i] / body.mass
        body.vel += a * (DT / 2)
        body.pos += body.vel * DT
        body.vel += a * (DT / 2)


def handle_collisions(bodies: List[Body]) -> List[Body]:
    intact = [True] * len(bodies)

    for i in range(len(bodies)):
        if not intact[i]:
            continue
        for j in range(i+1, len(bodies)):
            if not intact[j]:
                continue

            pi = bodies[i].pos
            pj = bodies[j].pos
            ri = bodies[i].radius
            rj = bodies[j].radius

            dist = np.linalg.norm(pj-pi)

            if dist < (ri + rj):
                # then merge
                m1, m2 = bodies[i].mass, bodies[j].mass
                v1, v2 = bodies[i].vel, bodies[j].vel

                new_mass = m1 + m2
                new_vel = (m1 * v1 + m2 * v2) / new_mass
                new_pos = (m1 * pi + m2 * pj) / new_mass

                new_col = bodies[i].color if m1 > 2 else bodies[j].color

                bodies[i].mass = new_mass
                bodies[i].vel = new_vel
                bodies[i].pos = new_pos
                bodies[i].radius = int(np.cbrt(bodies[i].radius**3 + bodies[j].radius**3))
                bodies[i].color = new_col
                intact[j] = False

    return [bodies[i] for i in range(len(bodies)) if intact[i]]


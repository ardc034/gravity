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

    def draw(self, surf: pygame.Surface):
        '''Draws the body on the screen'''
        pygame.draw.circle(surf, 
                           self.color, 
                           [int(coord) for coord in self.pos], 
                           self.radius)

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

            epsilon = 20.0 # Prevents infinite force at close distances
            mag = G * (bodies[i].mass * bodies[j].mass) / (dist**2 + epsilon**2)

            direction = (pos_j - pos_i) / dist

            f = mag * direction
            forces[i] += f
            forces[j] -= f
    for i, body in enumerate(bodies):
        a = forces[i] / body.mass
        body.vel += a * DT
        body.pos += body.vel * DT
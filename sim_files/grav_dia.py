from grav_eng import Body
from grav_sim import System
import pygame
from typing import List
import numpy as np

def kinetic_energy(bodies: List[Body]) -> float:
    K = 0.0
    for b in bodies:
        K += 0.5 * b.mass * np.dot(b.vel, b.vel)
    return K

def potential_energy(bodies: List[Body], G: float = 1.0):
    U = 0.0
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            r = np.linalg.norm(bodies[j].pos - bodies[i].pos)
            if r > 0:
                U -= G * bodies[i].mass * bodies[j].mass / r
    return U

def total_energy(bodies: List[Body], G: float = 1.0):
    return kinetic_energy(bodies) + potential_energy(bodies, G)

def linear_momentum(bodies: List[Body]):
    p = np.array([0.0, 0.0])
    for b in bodies:
        p += b.mass * b.vel
    return p

def center_of_mass(bodies: List[Body]):
    total_mass = sum(b.mass for b in bodies)
    com = np.array([0.0, 0.0])
    for b in bodies:
        com += b.mass * b.pos
    return com / total_mass

def angular_momentum(bodies: List[Body]):
    com = center_of_mass(bodies)
    L = 0.0
    for b in bodies:
        r = b.pos - com
        # 2D cross product: r_x * v_y - r_y * v_x
        L += b.mass * (r[0] * b.vel[1] - r[1] * b.vel[0])
    return L

def maximum_velocity(bodies: List[Body]):
    return max(np.linalg.norm(b.vel) for b in bodies)

def energy_drift(bodies: List[Body], i_e: float, G: float = 1.0):
    cur = total_energy(bodies, G)
    return 100 * (cur - i_e) / i_e


def draw_panel(surf: pygame.Surface, system: System, i_e):
    font = pygame.font.SysFont("consolas", 18)

    bodies = system.bodies

    # diagnostics
    K = kinetic_energy(bodies)
    U = potential_energy(bodies)
    E = K + U
    p = linear_momentum(bodies)
    L = angular_momentum(bodies)
    com = center_of_mass(bodies)
    max_v = maximum_velocity(bodies)

    drift = (E - i_e) / i_e * 100
    lines = [
        f"Kinetic Energy:     {K:.3f}",
        f"Potential Energy:   {U:.3f}",
        f"Total Energy:       {E:.3f}",
        f"Energy Drift:       {drift:.3f} %",
        f"Linear Momentum:    ({p[0]:.3f}, {p[1]:.3f})",
        f"Angular Momentum:   {L:.3f}",
        f"Center of Mass:     ({com[0]:.1f}, {com[1]:.1f})",
        f"Max Velocity:       {max_v:.3f}"
    ]

    pygame.draw.rect(surf, (20, 20, 20), pygame.Rect(0, 0, 330, len(lines)*22 + 10))
    y = 5
    for line in lines:
        text = font.render(line, True, (240, 240, 240))
        surf.blit(text, (10, y))
        y += 22

    return K, U

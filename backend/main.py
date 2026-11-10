from __future__ import annotations

import math
import os
from typing import Annotated

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator


Vector2 = tuple[float, float]
Color = str


class BodyState(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    x: float
    y: float
    vx: float
    vy: float
    mass: Annotated[float, Field(gt=0, le=1_000_000_000)]
    radius: Annotated[float, Field(gt=0, le=500)]
    color: Color

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError("color must be a six-digit hex color")
        try:
            int(value[1:], 16)
        except ValueError as exc:
            raise ValueError("color must be a six-digit hex color") from exc
        return value


class SimulationRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    bodies: Annotated[list[BodyState], Field(min_length=1, max_length=100)]
    dt: Annotated[float, Field(gt=0, le=1)] = 0.1
    steps: Annotated[int, Field(ge=1, le=20)] = 1
    gravitational_constant: Annotated[float, Field(ge=0, le=100)] = 1.0
    reference_energy: float | None = None
    collisions: bool = True


class Diagnostics(BaseModel):
    kinetic_energy: float
    potential_energy: float
    total_energy: float
    energy_drift_percent: float
    linear_momentum: Vector2
    angular_momentum: float
    center_of_mass: Vector2
    maximum_velocity: float


class SimulationResponse(BaseModel):
    bodies: list[BodyState]
    elapsed_time: float
    diagnostics: Diagnostics


app = FastAPI(title="Gravity Simulator API", version="1.0.0")
allowed_origins = os.getenv(
    "GRAVITY_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _accelerations(
    bodies: list[BodyState], gravitational_constant: float
) -> list[Vector2]:
    accelerations = [[0.0, 0.0] for _ in bodies]
    softening_squared = 4.0
    for i, body_i in enumerate(bodies):
        for j in range(i + 1, len(bodies)):
            body_j = bodies[j]
            dx = body_j.x - body_i.x
            dy = body_j.y - body_i.y
            distance_squared = dx * dx + dy * dy
            distance = math.sqrt(distance_squared)
            if distance < 5:
                continue
            scale = gravitational_constant / (
                (distance_squared + softening_squared) * distance
            )
            accelerations[i][0] += scale * body_j.mass * dx
            accelerations[i][1] += scale * body_j.mass * dy
            accelerations[j][0] -= scale * body_i.mass * dx
            accelerations[j][1] -= scale * body_i.mass * dy
    return [(x, y) for x, y in accelerations]


def _merge_collisions(bodies: list[BodyState]) -> list[BodyState]:
    merged = list(bodies)
    index = 0
    while index < len(merged):
        current = merged[index]
        other_index = index + 1
        while other_index < len(merged):
            other = merged[other_index]
            distance = math.hypot(current.x - other.x, current.y - other.y)
            if distance >= current.radius + other.radius:
                other_index += 1
                continue

            total_mass = current.mass + other.mass
            color = current.color if current.mass > 2 else other.color
            current = BodyState(
                x=(current.mass * current.x + other.mass * other.x) / total_mass,
                y=(current.mass * current.y + other.mass * other.y) / total_mass,
                vx=(current.mass * current.vx + other.mass * other.vx) / total_mass,
                vy=(current.mass * current.vy + other.mass * other.vy) / total_mass,
                mass=total_mass,
                radius=(current.radius**3 + other.radius**3) ** (1 / 3),
                color=color,
            )
            merged[index] = current
            merged.pop(other_index)
        index += 1
    return merged


def _step(
    bodies: list[BodyState],
    dt: float,
    gravitational_constant: float,
    collisions: bool,
) -> list[BodyState]:
    accelerations = _accelerations(bodies, gravitational_constant)
    moved = [
        body.model_copy(
            update={
                "x": body.x + body.vx * dt + 0.5 * ax * dt * dt,
                "y": body.y + body.vy * dt + 0.5 * ay * dt * dt,
                "vx": body.vx + 0.5 * ax * dt,
                "vy": body.vy + 0.5 * ay * dt,
            }
        )
        for body, (ax, ay) in zip(bodies, accelerations)
    ]
    if collisions:
        moved = _merge_collisions(moved)

    next_accelerations = _accelerations(moved, gravitational_constant)
    return [
        body.model_copy(
            update={
                "vx": body.vx + 0.5 * ax * dt,
                "vy": body.vy + 0.5 * ay * dt,
            }
        )
        for body, (ax, ay) in zip(moved, next_accelerations)
    ]


def _diagnostics(
    bodies: list[BodyState], initial_energy: float, gravitational_constant: float = 1.0
) -> Diagnostics:
    kinetic = sum(
        0.5 * body.mass * (body.vx * body.vx + body.vy * body.vy)
        for body in bodies
    )
    potential = 0.0
    momentum_x = 0.0
    momentum_y = 0.0
    angular_momentum = 0.0
    mass = sum(body.mass for body in bodies)
    center_x = sum(body.mass * body.x for body in bodies) / mass
    center_y = sum(body.mass * body.y for body in bodies) / mass
    maximum_velocity = 0.0

    for i, body in enumerate(bodies):
        momentum_x += body.mass * body.vx
        momentum_y += body.mass * body.vy
        relative_x = body.x - center_x
        relative_y = body.y - center_y
        angular_momentum += body.mass * (
            relative_x * body.vy - relative_y * body.vx
        )
        maximum_velocity = max(maximum_velocity, math.hypot(body.vx, body.vy))
        for other in bodies[i + 1 :]:
            distance = math.hypot(body.x - other.x, body.y - other.y)
            if distance > 0:
                potential -= (
                    gravitational_constant * body.mass * other.mass / distance
                )

    total = kinetic + potential
    drift = (
        100 * (total - initial_energy) / initial_energy
        if abs(initial_energy) > 1e-12
        else 0.0
    )
    return Diagnostics(
        kinetic_energy=kinetic,
        potential_energy=potential,
        total_energy=total,
        energy_drift_percent=drift,
        linear_momentum=(momentum_x, momentum_y),
        angular_momentum=angular_momentum,
        center_of_mass=(center_x, center_y),
        maximum_velocity=maximum_velocity,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    bodies = request.bodies
    initial_energy = request.reference_energy
    if initial_energy is None:
        initial_energy = _diagnostics(
            bodies, 0.0, request.gravitational_constant
        ).total_energy
    for _ in range(request.steps):
        bodies = _step(
            bodies,
            request.dt,
            request.gravitational_constant,
            request.collisions,
        )
    return SimulationResponse(
        bodies=bodies,
        elapsed_time=request.dt * request.steps,
        diagnostics=_diagnostics(
            bodies, initial_energy, request.gravitational_constant
        ),
    )

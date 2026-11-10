import unittest

from pydantic import ValidationError

from backend.main import (
    BodyState,
    SimulationRequest,
    _diagnostics,
    _merge_collisions,
    _step,
    simulate,
)


class SimulationTests(unittest.TestCase):
    def test_equal_and_opposite_gravity_accelerates_bodies_toward_each_other(self):
        bodies = [
            BodyState(x=0, y=0, vx=0, vy=0, mass=10, radius=1, color="#ffffff"),
            BodyState(x=20, y=0, vx=0, vy=0, mass=10, radius=1, color="#ff0000"),
        ]
        result = _step(bodies, 0.1, 1, False)

        self.assertGreater(result[0].vx, 0)
        self.assertLess(result[1].vx, 0)
        self.assertAlmostEqual(result[0].vx, -result[1].vx)

    def test_merge_conserves_mass_and_momentum(self):
        bodies = [
            BodyState(x=0, y=0, vx=2, vy=0, mass=3, radius=4, color="#ff0000"),
            BodyState(x=4, y=0, vx=-1, vy=0, mass=1, radius=4, color="#0000ff"),
        ]
        result = _merge_collisions(bodies)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].mass, 4)
        self.assertAlmostEqual(result[0].vx, 1.25)
        self.assertAlmostEqual(result[0].x, 1)

    def test_energy_diagnostics_stay_finite_for_zero_initial_energy(self):
        body = BodyState(x=0, y=0, vx=0, vy=0, mass=1, radius=1, color="#ffffff")
        diagnostics = _diagnostics([body], 0)
        self.assertEqual(diagnostics.energy_drift_percent, 0)

    def test_simulation_advances_and_returns_diagnostics(self):
        response = simulate(
            SimulationRequest(
                bodies=[
                    BodyState(
                        x=0, y=0, vx=0, vy=0, mass=1, radius=2, color="#ffffff"
                    ),
                    BodyState(
                        x=20, y=0, vx=0, vy=0, mass=1, radius=2, color="#00aaff"
                    ),
                ],
                dt=0.1,
                steps=2,
            )
        )

        self.assertAlmostEqual(response.elapsed_time, 0.2)
        self.assertNotEqual(response.bodies[0].vx, 0)

    def test_invalid_simulation_limits_are_rejected(self):
        with self.assertRaises(ValidationError):
            SimulationRequest(bodies=[], steps=21)


if __name__ == "__main__":
    unittest.main()

import numpy as np

from openreef.core.flow import (
    FlowParameters,
    FlowParticles,
    ReefMeshFlowField,
    trail_lines,
    trail_rgba,
)


def _ridge_field(direction: float = 90.0) -> ReefMeshFlowField:
    axis = np.linspace(-2.0, 2.0, 101)
    x_grid, _ = np.meshgrid(axis, axis)
    heights = -np.exp(-((x_grid / 0.22) ** 2))
    normals = np.zeros((*heights.shape, 3))
    normals[..., 2] = -1.0
    return ReefMeshFlowField(
        axis,
        axis,
        heights,
        normals,
        np.ones_like(heights, dtype=bool),
        top_sign=-1,
        parameters=FlowParameters(direction=direction, wake_strength=1.0),
    )


def test_flow_reversal_moves_wake_to_opposite_side() -> None:
    field = _ridge_field(90.0)
    positions = np.array(((0.12, 0.0, -1.2), (-0.12, 0.0, -1.2)))

    forward, _ = field.sample(positions, elapsed=0.4)
    field.parameters.direction = 270.0
    reverse, _ = field.sample(positions, elapsed=0.4)

    assert forward[1, 0] > 0
    assert reverse[0, 0] < 0
    assert abs(forward[0, 0]) < abs(forward[1, 0])
    assert abs(reverse[1, 0]) < abs(reverse[0, 0])


def test_particles_stay_above_surface_and_produce_trails() -> None:
    field = _ridge_field()
    particles = FlowParticles(field, 24, trail_segments=5)
    surface = field.surface_at(particles.positions[:, 0], particles.positions[:, 1])
    particles.positions[:, 2] = surface.height + 0.5

    particles.update(0.03, 0.03)
    surface = field.surface_at(particles.positions[:, 0], particles.positions[:, 1])
    clearance = (particles.positions[:, 2] - surface.height) * field.top_sign
    points, speeds = particles.ordered_trails()

    assert np.all(clearance >= field.clearance_min * 0.38 - 1e-9)
    assert points.shape == (24 * 6, 3)
    assert speeds.shape == (24 * 6,)
    assert trail_lines(24, 5).shape == (24 * 7,)


def test_surface_sampling_interpolates_between_grid_cells() -> None:
    axis = np.array((0.0, 1.0))
    heights = np.array(((0.0, 1.0), (2.0, 3.0)))
    normals = np.zeros((2, 2, 3))
    normals[..., 2] = 1.0
    field = ReefMeshFlowField(
        axis,
        axis,
        heights,
        normals,
        np.ones_like(heights, dtype=bool),
        top_sign=1,
    )

    sample = field.surface_at(np.array((0.5,)), np.array((0.5,)))

    assert np.isclose(sample.height[0], 1.5)
    assert np.allclose(sample.normals[0], (0.0, 0.0, 1.0))
    assert sample.valid[0]


def test_trail_colours_fade_from_tail_to_head() -> None:
    colours = trail_rgba(np.ones(8), particle_count=2, trail_segments=3)

    assert colours.shape == (8, 4)
    assert colours.dtype == np.uint8
    assert colours[0, 3] < colours[3, 3]
    assert colours[4, 3] < colours[7, 3]

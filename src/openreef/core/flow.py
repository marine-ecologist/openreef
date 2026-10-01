"""Mesh-derived relative flow field and particle advection."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from openreef.core.model import ModelDocument


@dataclass
class FlowParameters:
    """Dimensionless controls for the synthetic mesh flow field."""

    direction: float = 270.0
    speed: float = 0.58
    wake_strength: float = 0.72
    surface_following: float = 0.82


@dataclass(frozen=True)
class SurfaceSamples:
    """Vectorised terrain lookup result."""

    height: np.ndarray
    normals: np.ndarray
    relief: np.ndarray
    valid: np.ndarray


class FlowField(Protocol):
    """Velocity-source contract consumed by the particle renderer."""

    def sample(
        self,
        positions: np.ndarray,
        elapsed: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return velocity vectors and relative speeds at the supplied positions."""

    def seed(
        self,
        count: int,
        rng: np.random.Generator,
        *,
        upstream: bool,
    ) -> np.ndarray:
        """Return valid particle positions for this field's domain."""

    def constrain(self, positions: np.ndarray) -> np.ndarray:
        """Keep particles outside geometry and return the in-domain mask."""


class ReefMeshFlowField:
    """Constant-time flow samples over a mesh-derived regular terrain grid."""

    def __init__(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        heights: np.ndarray,
        normals: np.ndarray,
        valid: np.ndarray,
        *,
        top_sign: float,
        parameters: FlowParameters | None = None,
    ) -> None:
        self.x_values = np.asarray(x_values, dtype=np.float64)
        self.y_values = np.asarray(y_values, dtype=np.float64)
        self.heights = np.asarray(heights, dtype=np.float64)
        self.normals = np.asarray(normals, dtype=np.float64)
        self.valid = np.asarray(valid, dtype=bool)
        self.top_sign = -1.0 if top_sign < 0 else 1.0
        self.parameters = parameters or FlowParameters()
        if self.heights.shape != (len(self.y_values), len(self.x_values)):
            raise ValueError("Terrain height grid does not match its coordinate axes")
        if self.normals.shape != (*self.heights.shape, 3):
            raise ValueError("Terrain normal grid does not match its height grid")
        if self.valid.shape != self.heights.shape:
            raise ValueError("Terrain validity grid does not match its height grid")
        if not self.valid.any():
            raise ValueError("The mesh did not produce a usable terrain surface")

        self.x_min = float(self.x_values[0])
        self.x_max = float(self.x_values[-1])
        self.y_min = float(self.y_values[0])
        self.y_max = float(self.y_values[-1])
        self.x_span = max(self.x_max - self.x_min, 1e-9)
        self.y_span = max(self.y_max - self.y_min, 1e-9)
        self.domain_scale = max(self.x_span, self.y_span)
        # A thin near-surface sheet reads as flow; a deep random volume reads as
        # particle noise and hides the reconstruction.
        self.clearance_min = self.domain_scale * 0.0035
        self.clearance_max = self.domain_scale * 0.032

        finite = self.heights[self.valid]
        low = float(np.min(finite))
        high = float(np.max(finite))
        height_range = max(high - low, 1e-9)
        if self.top_sign < 0:
            self.relief_grid = (high - self.heights) / height_range
        else:
            self.relief_grid = (self.heights - low) / height_range
        self.relief_grid = np.clip(self.relief_grid, 0.0, 1.0)

        valid_y, valid_x = np.nonzero(self.valid)
        self._valid_x = valid_x
        self._valid_y = valid_y

    @classmethod
    def from_document(
        cls,
        document: ModelDocument,
        *,
        resolution: int = 160,
        parameters: FlowParameters | None = None,
    ) -> ReefMeshFlowField:
        """Build an accelerated height/normal cache from all mesh parts."""

        import pyvista as pv
        from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
        from vtkmodules.vtkCommonDataModel import vtkStaticCellLocator

        mesh_parts = [
            part.dataset.extract_surface(algorithm="dataset_surface").triangulate()
            for part in document.parts
            if part.kind == "mesh"
        ]
        if not mesh_parts:
            raise ValueError("Flow Field requires a textured triangle mesh")
        mesh = pv.merge(mesh_parts, merge_points=False).triangulate()
        mesh = mesh.compute_normals(
            cell_normals=True,
            point_normals=False,
            consistent_normals=True,
            auto_orient_normals=False,
            inplace=False,
        )
        cell_normals = np.asarray(mesh.cell_data["Normals"], dtype=np.float64)
        # OpenReef's viewer treats +Z as up. Triangle winding is not reliable
        # after GLB export, so always take the highest vertical intersection and
        # orient its normal upward rather than inferring the surface from winding.
        top_sign = 1.0

        xmin, xmax, ymin, ymax, zmin, zmax = (float(value) for value in mesh.bounds)
        margin = max(zmax - zmin, xmax - xmin, ymax - ymin, 1.0) * 0.05
        x_values = np.linspace(xmin, xmax, resolution)
        y_values = np.linspace(ymin, ymax, resolution)
        heights = np.zeros((resolution, resolution), dtype=np.float64)
        normals = np.zeros((resolution, resolution, 3), dtype=np.float64)
        valid = np.zeros((resolution, resolution), dtype=bool)

        locator = vtkStaticCellLocator()
        locator.SetDataSet(mesh)
        locator.BuildLocator()
        intersections = vtkPoints()
        cell_ids = vtkIdList()
        start_z = zmin - margin if top_sign < 0 else zmax + margin
        end_z = zmax + margin if top_sign < 0 else zmin - margin

        for row, y_value in enumerate(y_values):
            for column, x_value in enumerate(x_values):
                intersections.Reset()
                cell_ids.Reset()
                hit = locator.IntersectWithLine(
                    (float(x_value), float(y_value), start_z),
                    (float(x_value), float(y_value), end_z),
                    1e-7,
                    intersections,
                    cell_ids,
                )
                if not hit or intersections.GetNumberOfPoints() == 0:
                    continue
                points = np.asarray(
                    [
                        intersections.GetPoint(index)
                        for index in range(intersections.GetNumberOfPoints())
                    ]
                )
                chosen = int(np.argmax(points[:, 2]))
                cell_id = int(cell_ids.GetId(chosen))
                normal = cell_normals[cell_id].copy()
                if normal[2] * top_sign < 0:
                    normal *= -1
                length = float(np.linalg.norm(normal))
                if length <= 1e-9:
                    normal = np.array((0.0, 0.0, top_sign))
                else:
                    normal /= length
                heights[row, column] = points[chosen, 2]
                normals[row, column] = normal
                valid[row, column] = True

        return cls(
            x_values,
            y_values,
            heights,
            normals,
            valid,
            top_sign=top_sign,
            parameters=parameters,
        )

    @property
    def reference_speed(self) -> float:
        return self.domain_scale * 0.075 * max(0.0, min(1.0, self.parameters.speed))

    @property
    def direction_vector(self) -> np.ndarray:
        radians = math.radians(self.parameters.direction)
        return np.array((math.sin(radians), -math.cos(radians), 0.0))

    def surface_at(self, x: np.ndarray, y: np.ndarray) -> SurfaceSamples:
        """Bilinearly interpolate terrain height and normals at horizontal positions."""

        x_array = np.asarray(x, dtype=np.float64)
        y_array = np.asarray(y, dtype=np.float64)
        grid_x = (x_array - self.x_min) / self.x_span * (len(self.x_values) - 1)
        grid_y = (y_array - self.y_min) / self.y_span * (len(self.y_values) - 1)
        inside = (
            (grid_x >= 0.0)
            & (grid_x <= len(self.x_values) - 1)
            & (grid_y >= 0.0)
            & (grid_y <= len(self.y_values) - 1)
        )
        x0 = np.clip(np.floor(grid_x).astype(int), 0, len(self.x_values) - 1)
        y0 = np.clip(np.floor(grid_y).astype(int), 0, len(self.y_values) - 1)
        x1 = np.minimum(x0 + 1, len(self.x_values) - 1)
        y1 = np.minimum(y0 + 1, len(self.y_values) - 1)
        fraction_x = np.clip(grid_x - x0, 0.0, 1.0)
        fraction_y = np.clip(grid_y - y0, 0.0, 1.0)
        weights = np.stack(
            (
                (1.0 - fraction_x) * (1.0 - fraction_y),
                fraction_x * (1.0 - fraction_y),
                (1.0 - fraction_x) * fraction_y,
                fraction_x * fraction_y,
            ),
            axis=1,
        )
        rows = (y0, y0, y1, y1)
        columns = (x0, x1, x0, x1)
        valid_corners = np.stack(
            [self.valid[row, column] for row, column in zip(rows, columns, strict=True)],
            axis=1,
        )
        usable_weights = weights * valid_corners
        weight_sum = np.sum(usable_weights, axis=1)
        safe_weight_sum = np.maximum(weight_sum, 1e-12)

        height_corners = np.stack(
            [self.heights[row, column] for row, column in zip(rows, columns, strict=True)],
            axis=1,
        )
        relief_corners = np.stack(
            [self.relief_grid[row, column] for row, column in zip(rows, columns, strict=True)],
            axis=1,
        )
        normal_corners = np.stack(
            [self.normals[row, column] for row, column in zip(rows, columns, strict=True)],
            axis=1,
        )
        heights = np.sum(height_corners * usable_weights, axis=1) / safe_weight_sum
        relief = np.sum(relief_corners * usable_weights, axis=1) / safe_weight_sum
        normals = np.sum(normal_corners * usable_weights[:, :, None], axis=1)
        normal_length = np.linalg.norm(normals, axis=1)
        good_normal = normal_length > 1e-12
        normals[good_normal] /= normal_length[good_normal, None]
        normals[~good_normal] = (0.0, 0.0, self.top_sign)
        return SurfaceSamples(
            heights,
            normals,
            relief,
            inside & (weight_sum > 1e-9),
        )

    def sample(self, positions: np.ndarray, elapsed: float) -> tuple[np.ndarray, np.ndarray]:
        """Return mesh-following velocity and relative speed for every position."""

        positions = np.asarray(positions, dtype=np.float64)
        count = len(positions)
        base_direction = self.direction_vector
        reference = self.reference_speed
        velocity = np.repeat((base_direction * reference)[None, :], count, axis=0)
        if reference <= 0 or count == 0:
            return velocity, np.zeros(count, dtype=np.float64)

        surface = self.surface_at(positions[:, 0], positions[:, 1])
        valid = surface.valid
        if not valid.any():
            return velocity, np.ones(count, dtype=np.float64)

        projection = np.sum(velocity * surface.normals, axis=1)
        tangent = velocity - surface.normals * projection[:, None]
        following = max(0.0, min(1.0, self.parameters.surface_following)) * 0.82
        velocity[valid] = velocity[valid] * (1.0 - following) + tangent[valid] * following
        velocity[valid] *= (1.0 + surface.relief[valid] * 0.42)[:, None]

        # Look upstream at several distances. A higher upstream surface produces
        # a spatially anchored wake that persists behind relief instead of
        # adding noise everywhere in the field.
        wake = np.zeros(count, dtype=np.float64)
        for distance_scale, decay in ((0.028, 1.0), (0.060, 0.82), (0.105, 0.58)):
            distance = self.domain_scale * distance_scale
            upstream = self.surface_at(
                positions[:, 0] - base_direction[0] * distance,
                positions[:, 1] - base_direction[1] * distance,
            )
            wake_valid = valid & upstream.valid
            relief_above = np.zeros(count, dtype=np.float64)
            relief_above[wake_valid] = np.maximum(
                0.0,
                (upstream.height[wake_valid] - surface.height[wake_valid])
                * self.top_sign
                / distance,
            )
            wake = np.maximum(
                wake,
                np.clip(relief_above * self.domain_scale * 1.15 * decay, 0.0, 1.0),
            )
        wake *= max(0.0, min(1.0, self.parameters.wake_strength))
        velocity *= (1.0 - wake * 0.68)[:, None]

        wavelength = self.domain_scale * 0.12
        along = positions[:, 0] * base_direction[0] + positions[:, 1] * base_direction[1]
        cross = -positions[:, 0] * base_direction[1] + positions[:, 1] * base_direction[0]
        phase = (
            along / wavelength * math.tau
            + cross / wavelength * math.pi
            - elapsed * (1.2 + self.parameters.speed * 1.8)
        )
        vortex = np.sin(phase) * reference * wake * 0.62
        velocity[:, 0] += -base_direction[1] * vortex
        velocity[:, 1] += base_direction[0] * vortex
        recirculation = np.clip((wake - 0.62) / 0.38, 0.0, 1.0) * reference * 0.42
        velocity[:, :2] -= base_direction[:2] * recirculation[:, None]
        velocity[:, 2] += np.cos(phase * 0.5) * reference * wake * 0.06 * self.top_sign

        clearance = (positions[:, 2] - surface.height) * self.top_sign
        desired = self.clearance_min * 2.2
        velocity[valid, 2] += (
            (desired - clearance[valid])
            * self.top_sign
            * max(0.0, min(1.0, self.parameters.surface_following))
            * 0.36
        )
        relative_speed = np.linalg.norm(velocity, axis=1) / max(reference, 1e-9)
        return velocity, relative_speed

    def constrain(self, positions: np.ndarray) -> np.ndarray:
        """Clamp particles above the reef and return those still over the mesh."""

        surface = self.surface_at(positions[:, 0], positions[:, 1])
        clearance = (positions[:, 2] - surface.height) * self.top_sign
        colliding = surface.valid & (clearance < self.clearance_min * 0.38)
        positions[colliding, 2] = (
            surface.height[colliding] + self.top_sign * self.clearance_min * 0.38
        )
        return surface.valid

    def seed(self, count: int, rng: np.random.Generator, *, upstream: bool) -> np.ndarray:
        """Seed positions on valid terrain, optionally restricted to the inlet."""

        direction = self.direction_vector
        valid_x = self.x_values[self._valid_x]
        valid_y = self.y_values[self._valid_y]
        projection = valid_x * direction[0] + valid_y * direction[1]
        candidates = np.arange(len(valid_x))
        if upstream:
            threshold = np.quantile(projection, 0.12)
            candidates = candidates[projection <= threshold]
            cross = -valid_x[candidates] * direction[1] + valid_y[candidates] * direction[0]
            candidates = candidates[np.argsort(cross)]
            lane_count = min(96, max(16, int(math.sqrt(count) * 1.6)))
            lanes = np.arange(count) % lane_count
            lane_fraction = (lanes + 0.5) / lane_count
            centres = np.rint(lane_fraction * (len(candidates) - 1)).astype(int)
            lane_width = max(1, len(candidates) // lane_count)
            jitter = rng.integers(-lane_width // 3, lane_width // 3 + 1, count)
            chosen = candidates[np.clip(centres + jitter, 0, len(candidates) - 1)]
        else:
            chosen = rng.choice(candidates, size=count, replace=True)
        rows = self._valid_y[chosen]
        columns = self._valid_x[chosen]
        dx = self.x_span / max(len(self.x_values) - 1, 1)
        dy = self.y_span / max(len(self.y_values) - 1, 1)
        x = self.x_values[columns] + rng.uniform(-0.45 * dx, 0.45 * dx, count)
        y = self.y_values[rows] + rng.uniform(-0.45 * dy, 0.45 * dy, count)
        clearance = rng.uniform(self.clearance_min, self.clearance_max, count)
        z = self.heights[rows, columns] + self.top_sign * clearance
        return np.column_stack((x, y, z))


class FlowParticles:
    """Deterministic particle state independent of the rendering layer."""

    def __init__(
        self,
        field: FlowField,
        count: int,
        *,
        trail_segments: int = 32,
        trail_length: float = 5.0,
    ) -> None:
        self.field = field
        self.count = int(count)
        self.trail_segments = int(trail_segments)
        self.trail_length = float(trail_length)
        self.rng = np.random.default_rng(0x2F6E2B1)
        self.positions = self.field.seed(self.count, self.rng, upstream=False)
        self.ages = self.rng.uniform(0.0, 5.0, self.count)
        self.lifetimes = self.rng.uniform(8.0, 14.0, self.count)
        self.relative_speed = np.ones(self.count, dtype=np.float64)
        self.history = np.repeat(
            self.positions[None, :, :], self.trail_segments + 1, axis=0
        )
        self.speed_history = np.ones((self.trail_segments + 1, self.count))
        self.history_head = 0
        self.snapshot_elapsed = 0.0

    def reset(self) -> None:
        self.rng = np.random.default_rng(0x2F6E2B1)
        self.positions = self.field.seed(self.count, self.rng, upstream=False)
        self.ages = self.rng.uniform(0.0, 5.0, self.count)
        self.lifetimes = self.rng.uniform(8.0, 14.0, self.count)
        self.relative_speed.fill(1.0)
        self.history[:] = self.positions[None, :, :]
        self.speed_history.fill(1.0)
        self.history_head = 0
        self.snapshot_elapsed = 0.0

    def update(self, delta: float, elapsed: float) -> None:
        delta = min(max(float(delta), 0.0), 0.05)
        velocity, _ = self.field.sample(self.positions, elapsed)
        midpoint = self.positions + velocity * (delta * 0.5)
        velocity, self.relative_speed = self.field.sample(midpoint, elapsed + delta * 0.5)
        self.positions += velocity * delta
        self.ages += delta
        in_domain = self.field.constrain(self.positions)
        expired = (~in_domain) | (self.ages > self.lifetimes)
        if expired.any():
            replacement = self.field.seed(int(expired.sum()), self.rng, upstream=True)
            self.positions[expired] = replacement
            self.ages[expired] = 0.0
            self.lifetimes[expired] = self.rng.uniform(8.0, 14.0, int(expired.sum()))
            self.history[:, expired, :] = replacement[None, :, :]
            self.speed_history[:, expired] = 1.0

        self.history[self.history_head] = self.positions
        self.speed_history[self.history_head] = self.relative_speed
        self.snapshot_elapsed += delta
        interval = max(0.025, self.trail_length / self.trail_segments)
        if self.snapshot_elapsed >= interval:
            self.snapshot_elapsed %= interval
            self.history_head = (self.history_head + 1) % (self.trail_segments + 1)
            self.history[self.history_head] = self.positions
            self.speed_history[self.history_head] = self.relative_speed

    def ordered_trails(self) -> tuple[np.ndarray, np.ndarray]:
        """Return particle-major trails from oldest to newest."""

        slots = np.array(
            [
                (self.history_head + 1 + offset) % (self.trail_segments + 1)
                for offset in range(self.trail_segments + 1)
            ]
        )
        points = self.history[slots].transpose(1, 0, 2).reshape(-1, 3)
        speeds = self.speed_history[slots].transpose(1, 0).reshape(-1)
        return points, speeds


def trail_lines(particle_count: int, trail_segments: int) -> np.ndarray:
    """Return PyVista polyline connectivity for particle-major trail points."""

    width = trail_segments + 1
    starts = np.arange(particle_count, dtype=np.int64) * width
    indices = starts[:, None] + np.arange(width, dtype=np.int64)[None, :]
    return np.column_stack((np.full(particle_count, width), indices)).reshape(-1)


def trail_rgba(
    relative_speed: np.ndarray,
    particle_count: int,
    trail_segments: int,
) -> np.ndarray:
    """Map speed and trail age to a restrained CFD-style RGBA palette."""

    width = trail_segments + 1
    speeds = np.asarray(relative_speed, dtype=np.float64)
    if speeds.size != particle_count * width:
        raise ValueError("Trail speed array does not match particle connectivity")
    palette = np.array(
        (
            (24, 46, 184),
            (0, 139, 235),
            (0, 218, 196),
            (141, 226, 70),
            (247, 213, 41),
            (245, 91, 32),
        ),
        dtype=np.float64,
    )
    scaled = np.clip((speeds - 0.42) / 1.80, 0.0, 1.0) * (len(palette) - 1)
    lower = np.floor(scaled).astype(int)
    upper = np.minimum(lower + 1, len(palette) - 1)
    fraction = (scaled - lower)[:, None]
    rgb = palette[lower] * (1.0 - fraction) + palette[upper] * fraction
    age = np.linspace(0.0, 1.0, width)
    alpha = np.rint(20.0 + 220.0 * age**1.45).astype(np.uint8)
    rgba = np.empty((speeds.size, 4), dtype=np.uint8)
    rgba[:, :3] = np.rint(rgb).astype(np.uint8)
    rgba[:, 3] = np.tile(alpha, particle_count)
    return rgba

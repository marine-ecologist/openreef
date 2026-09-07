"""Portable camera viewpoint state."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _normalized(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    if length <= 1e-12:
        raise ValueError("Camera direction and view-up vectors must not be zero")
    return tuple(component / length for component in vector)  # type: ignore[return-value]


def pan_camera(camera: Any, dx: float, dy: float, viewport_height: int) -> None:
    """Translate a camera and its focal point by a screen-space drag."""
    position = _vector3(camera.position, "position")
    focal_point = _vector3(camera.focal_point, "focal_point")
    view_up = _normalized(_vector3(camera.up, "view_up"))
    forward_vector = tuple(focal_point[i] - position[i] for i in range(3))
    distance = math.sqrt(sum(component * component for component in forward_vector))
    forward = _normalized(forward_vector)
    right = _normalized(
        (
            forward[1] * view_up[2] - forward[2] * view_up[1],
            forward[2] * view_up[0] - forward[0] * view_up[2],
            forward[0] * view_up[1] - forward[1] * view_up[0],
        )
    )
    screen_up = _normalized(
        (
            right[1] * forward[2] - right[2] * forward[1],
            right[2] * forward[0] - right[0] * forward[2],
            right[0] * forward[1] - right[1] * forward[0],
        )
    )

    if camera.parallel_projection:
        visible_height = 2.0 * float(camera.parallel_scale)
    else:
        visible_height = 2.0 * distance * math.tan(math.radians(float(camera.view_angle)) / 2.0)
    units_per_pixel = visible_height / max(viewport_height, 1)
    offset = tuple((-dx * right[i] + dy * screen_up[i]) * units_per_pixel for i in range(3))
    camera.position = tuple(position[i] + offset[i] for i in range(3))
    camera.focal_point = tuple(focal_point[i] + offset[i] for i in range(3))


def _vector3(value: object, field: str) -> tuple[float, float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"'{field}' must contain exactly three numbers")
    try:
        return tuple(float(item) for item in value)  # type: ignore[return-value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' must contain exactly three numbers") from exc


def _pair(value: object, field: str) -> tuple[float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"'{field}' must contain exactly two numbers")
    try:
        return tuple(float(item) for item in value)  # type: ignore[return-value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' must contain exactly two numbers") from exc


@dataclass(frozen=True)
class CameraView:
    """The render-camera values needed to reproduce a viewpoint."""

    position: tuple[float, float, float]
    focal_point: tuple[float, float, float]
    view_up: tuple[float, float, float]
    parallel_projection: bool
    parallel_scale: float
    view_angle: float
    clipping_range: tuple[float, float]

    @classmethod
    def capture(cls, plotter: Any) -> CameraView:
        camera = plotter.camera
        position, focal_point, view_up = plotter.camera_position
        return cls(
            position=_vector3(position, "position"),
            focal_point=_vector3(focal_point, "focal_point"),
            view_up=_vector3(view_up, "view_up"),
            parallel_projection=bool(camera.parallel_projection),
            parallel_scale=float(camera.parallel_scale),
            view_angle=float(camera.view_angle),
            clipping_range=_pair(camera.clipping_range, "clipping_range"),
        )

    def apply(self, plotter: Any) -> None:
        camera = plotter.camera
        plotter.camera_position = (self.position, self.focal_point, self.view_up)
        camera.parallel_projection = self.parallel_projection
        camera.parallel_scale = self.parallel_scale
        camera.view_angle = self.view_angle
        camera.clipping_range = self.clipping_range
        plotter.render()

    def to_dict(self) -> dict[str, object]:
        return {"schema_version": 1, **asdict(self)}

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> CameraView:
        if data.get("schema_version") != 1:
            raise ValueError("Unsupported or missing viewpoint schema version")
        if not isinstance(data.get("parallel_projection"), bool):
            raise ValueError("'parallel_projection' must be true or false")
        try:
            return cls(
                position=_vector3(data["position"], "position"),
                focal_point=_vector3(data["focal_point"], "focal_point"),
                view_up=_vector3(data["view_up"], "view_up"),
                parallel_projection=bool(data["parallel_projection"]),
                parallel_scale=float(data["parallel_scale"]),
                view_angle=float(data["view_angle"]),
                clipping_range=_pair(data["clipping_range"], "clipping_range"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing viewpoint field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ValueError) and str(exc).startswith("'"):
                raise
            raise ValueError("Viewpoint contains an invalid numeric value") from exc

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> CameraView:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read viewpoint: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Viewpoint file must contain a JSON object")
        return cls.from_mapping(data)

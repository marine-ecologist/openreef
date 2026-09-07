"""Read COLMAP sparse camera poses and persist OpenReef ROI metadata."""

from __future__ import annotations

import json
import shutil
import struct
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np

from openreef.core.mesh_edit import project_to_viewport, signed_lasso_distance
from openreef.core.model import ModelDocument


@dataclass(frozen=True)
class CameraPose:
    image_id: int
    camera_id: int
    name: str
    center: tuple[float, float, float]
    right: tuple[float, float, float]
    up: tuple[float, float, float]
    forward: tuple[float, float, float]


@dataclass(frozen=True)
class SparseROI:
    bounds: tuple[float, float, float, float, float, float]
    selected_points: int
    total_points: int
    created_at: str
    sparse_model: str = ""
    coordinate_system: str = "COLMAP world coordinates"
    version: int = 1

    @classmethod
    def from_selection(
        cls,
        bounds: tuple[float, float, float, float, float, float],
        selected_points: int,
        total_points: int,
        sparse_model: str = "",
    ) -> SparseROI:
        return cls(
            bounds=bounds,
            selected_points=selected_points,
            total_points=total_points,
            created_at=datetime.now().astimezone().isoformat(),
            sparse_model=sparse_model,
        )

    def save(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        return destination

    @classmethod
    def load(cls, path: str | Path) -> SparseROI:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        bounds = tuple(float(value) for value in payload["bounds"])
        if len(bounds) != 6 or not all(np.isfinite(bounds)):
            raise ValueError("ROI bounds must contain six finite numbers")
        if not (bounds[0] < bounds[1] and bounds[2] < bounds[3] and bounds[4] < bounds[5]):
            raise ValueError("ROI bounds have no volume")
        return cls(
            bounds=bounds,
            selected_points=int(payload.get("selected_points", 0)),
            total_points=int(payload.get("total_points", 0)),
            created_at=str(payload.get("created_at", "")),
            sparse_model=str(payload.get("sparse_model", "")),
            coordinate_system=str(payload.get("coordinate_system", "COLMAP world coordinates")),
            version=int(payload.get("version", 1)),
        )


def read_camera_poses(images_binary: str | Path) -> tuple[CameraPose, ...]:
    """Read registered image poses from COLMAP images.bin."""
    path = Path(images_binary)
    poses: list[CameraPose] = []
    with path.open("rb") as stream:
        (count,) = _read(stream, "<Q")
        for _ in range(count):
            values = _read(stream, "<i7di")
            image_id = int(values[0])
            quaternion = np.asarray(values[1:5], dtype=float)
            translation = np.asarray(values[5:8], dtype=float)
            camera_id = int(values[8])
            name = _read_c_string(stream)
            (point_count,) = _read(stream, "<Q")
            stream.seek(int(point_count) * 24, 1)

            world_to_camera = _quaternion_rotation(quaternion)
            camera_to_world = world_to_camera.T
            center = -camera_to_world @ translation
            poses.append(
                CameraPose(
                    image_id=image_id,
                    camera_id=camera_id,
                    name=name,
                    center=tuple(float(value) for value in center),
                    right=tuple(float(value) for value in camera_to_world[:, 0]),
                    up=tuple(float(value) for value in -camera_to_world[:, 1]),
                    forward=tuple(float(value) for value in camera_to_world[:, 2]),
                )
            )
    return tuple(poses)


def save_camera_manifest(poses: tuple[CameraPose, ...], path: str | Path) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "coordinate_system": "COLMAP world coordinates",
        "registered_cameras": len(poses),
        "cameras": [asdict(pose) for pose in poses],
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination


def filter_text_model_to_roi(
    source: str | Path,
    destination: str | Path,
    roi: SparseROI,
) -> int:
    """Filter a COLMAP TXT model to an ROI while retaining all registered cameras."""
    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path / "cameras.txt", destination_path / "cameras.txt")

    xmin, xmax, ymin, ymax, zmin, zmax = roi.bounds
    retained: set[int] = set()
    point_output: list[str] = []
    for line in (source_path / "points3D.txt").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            point_output.append(line)
            continue
        values = stripped.split()
        if len(values) < 4:
            continue
        point_id = int(values[0])
        x, y, z = (float(value) for value in values[1:4])
        if xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax:
            retained.add(point_id)
            point_output.append(line)
    (destination_path / "points3D.txt").write_text("\n".join(point_output) + "\n", encoding="utf-8")

    image_output: list[str] = []
    expect_points = False
    for line in (source_path / "images.txt").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            image_output.append(line)
            continue
        if expect_points:
            values = stripped.split()
            for index in range(2, len(values), 3):
                try:
                    if int(values[index]) not in retained:
                        values[index] = "-1"
                except ValueError:
                    values[index] = "-1"
            image_output.append(" ".join(values))
            expect_points = False
        else:
            image_output.append(line)
            if stripped:
                expect_points = True
    (destination_path / "images.txt").write_text("\n".join(image_output) + "\n", encoding="utf-8")
    return len(retained)


def lasso_roi(
    document: ModelDocument,
    camera: Any,
    viewport_size: tuple[int, int],
    polygon: list[tuple[float, float]],
    *,
    margin_fraction: float = 0.02,
    sparse_model: str = "",
) -> SparseROI:
    """Create a world-axis ROI around sparse points selected in the current view."""
    selected: list[np.ndarray] = []
    total = 0
    for part in document.parts:
        if part.kind != "point-cloud":
            continue
        points = np.asarray(part.dataset.points, dtype=float)
        total += len(points)
        screen, valid = project_to_viewport(points, camera, viewport_size)
        distance = signed_lasso_distance(screen, np.asarray(polygon, dtype=float))
        mask = valid & (distance <= 0.0)
        if np.any(mask):
            selected.append(points[mask])
    if not selected:
        raise ValueError("The ROI lasso contains no sparse points")
    points = np.vstack(selected)
    minimum = points.min(axis=0)
    maximum = points.max(axis=0)
    extent = maximum - minimum
    scene_scale = max(float(np.max(extent)), 1.0e-6)
    margin = np.maximum(extent * margin_fraction, scene_scale * 0.002)
    minimum -= margin
    maximum += margin
    bounds = (
        float(minimum[0]),
        float(maximum[0]),
        float(minimum[1]),
        float(maximum[1]),
        float(minimum[2]),
        float(maximum[2]),
    )
    return SparseROI.from_selection(bounds, len(points), total, sparse_model)


def _read(stream: BinaryIO, format_string: str) -> tuple[Any, ...]:
    size = struct.calcsize(format_string)
    value = stream.read(size)
    if len(value) != size:
        raise ValueError("Unexpected end of COLMAP binary model")
    return struct.unpack(format_string, value)


def _read_c_string(stream: BinaryIO) -> str:
    value = bytearray()
    while True:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unexpected end of COLMAP image name")
        if byte == b"\0":
            return value.decode("utf-8", errors="replace")
        value.extend(byte)


def _quaternion_rotation(quaternion: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(quaternion))
    if norm <= 1.0e-12:
        raise ValueError("COLMAP camera quaternion has zero length")
    w, x, y, z = quaternion / norm
    return np.asarray(
        (
            (1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w),
            (2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w),
            (2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y),
        ),
        dtype=float,
    )

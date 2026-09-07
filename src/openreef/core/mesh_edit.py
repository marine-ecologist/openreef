"""Screen-space lasso trimming for meshes and point clouds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openreef.core.model import ModelDocument, ModelPart, classify_dataset, find_vertex_color

LASSO_SCALAR = "__openreef_lasso_distance"


@dataclass(frozen=True)
class TrimResult:
    document: ModelDocument
    removed_points: int
    removed_cells: int


@dataclass(frozen=True)
class LassoOperation:
    """A repeatable screen-space cut captured from one camera view."""

    projection: tuple[tuple[float, float, float, float], ...]
    viewport_size: tuple[int, int]
    polygon: tuple[tuple[float, float], ...]
    keep_inside: bool

    @classmethod
    def capture(
        cls,
        camera: Any,
        viewport_size: tuple[int, int],
        polygon: list[tuple[float, float]],
        *,
        keep_inside: bool,
    ) -> LassoOperation:
        width, height = viewport_size
        if width <= 0 or height <= 0:
            raise ValueError("Viewport must have a positive width and height")
        matrix = _projection_matrix(camera, width / height)
        return cls(
            projection=tuple(tuple(float(value) for value in row) for row in matrix),
            viewport_size=viewport_size,
            polygon=tuple(polygon),
            keep_inside=keep_inside,
        )


def _projection_matrix(camera: Any, aspect: float) -> np.ndarray:
    vtk_matrix = camera.GetCompositeProjectionTransformMatrix(aspect, -1.0, 1.0)
    return np.asarray(
        [[vtk_matrix.GetElement(row, column) for column in range(4)] for row in range(4)],
        dtype=float,
    )


def project_to_viewport(
    points: np.ndarray, camera: Any, viewport_size: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Project world points to Qt viewport coordinates (origin at top-left)."""
    width, height = viewport_size
    if width <= 0 or height <= 0:
        raise ValueError("Viewport must have a positive width and height")
    matrix = _projection_matrix(camera, width / height)
    return _project_with_matrix(points, matrix, viewport_size)


def _project_with_matrix(
    points: np.ndarray, matrix: np.ndarray, viewport_size: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    width, height = viewport_size
    world = np.column_stack((np.asarray(points, dtype=float), np.ones(len(points))))
    clip = world @ matrix.T
    divisor = clip[:, 3]
    valid = divisor > 1e-12
    normalized = np.zeros((len(points), 2), dtype=float)
    normalized[valid] = clip[valid, :2] / divisor[valid, None]
    screen = np.empty_like(normalized)
    screen[:, 0] = (normalized[:, 0] + 1.0) * width / 2.0
    screen[:, 1] = (1.0 - normalized[:, 1]) * height / 2.0
    return screen, valid


def signed_lasso_distance(points: np.ndarray, polygon: np.ndarray) -> np.ndarray:
    """Return negative distances inside a 2D polygon and positive outside."""
    points = np.asarray(points, dtype=float)
    polygon = np.asarray(polygon, dtype=float)
    if len(polygon) < 3:
        raise ValueError("A lasso needs at least three points")

    inside = np.zeros(len(points), dtype=bool)
    minimum_squared = np.full(len(points), np.inf)
    previous = polygon[-1]
    for current in polygon:
        edge = current - previous
        edge_squared = float(edge @ edge)
        if edge_squared > 1e-12:
            relative = points - previous
            along = np.clip((relative @ edge) / edge_squared, 0.0, 1.0)
            nearest = previous + along[:, None] * edge
            minimum_squared = np.minimum(
                minimum_squared, np.einsum("ij,ij->i", points - nearest, points - nearest)
            )

        crosses = (current[1] > points[:, 1]) != (previous[1] > points[:, 1])
        denominator = previous[1] - current[1]
        if abs(denominator) > 1e-12:
            crossing_x = (previous[0] - current[0]) * (
                points[:, 1] - current[1]
            ) / denominator + current[0]
            inside ^= crosses & (points[:, 0] < crossing_x)
        previous = current

    distance = np.sqrt(minimum_squared)
    distance[inside] *= -1.0
    return distance


def _trim_part(
    part: ModelPart,
    operation: LassoOperation,
) -> ModelPart | None:
    dataset = part.dataset.copy(deep=True)
    screen_points, valid = _project_with_matrix(
        dataset.points,
        np.asarray(operation.projection),
        operation.viewport_size,
    )
    distance = signed_lasso_distance(screen_points, np.asarray(operation.polygon))
    distance[~valid] = 1.0e12

    if part.kind == "point-cloud":
        from pyvista import PolyData

        mask = distance <= 0.0 if operation.keep_inside else distance > 0.0
        if not np.any(mask):
            return None
        trimmed = PolyData(np.asarray(dataset.points)[mask])
        for name, values in dataset.point_data.items():
            trimmed.point_data[name] = np.asarray(values)[mask]
    else:
        dataset.point_data[LASSO_SCALAR] = distance
        trimmed = dataset.clip_scalar(
            scalars=LASSO_SCALAR,
            value=0.0,
            invert=operation.keep_inside,
        )
        trimmed.point_data.pop(LASSO_SCALAR, None)
        if int(trimmed.n_points) == 0 or int(trimmed.n_cells) == 0:
            return None

    return ModelPart(
        name=part.name,
        dataset=trimmed,
        kind=classify_dataset(trimmed),
        vertex_color=find_vertex_color(trimmed),
    )


def trim_document(
    document: ModelDocument,
    camera: Any,
    viewport_size: tuple[int, int],
    polygon: list[tuple[float, float]],
    *,
    keep_inside: bool,
) -> TrimResult:
    """Cut all document geometry using a lasso projected through the current view."""
    operation = LassoOperation.capture(
        camera,
        viewport_size,
        polygon,
        keep_inside=keep_inside,
    )
    return apply_lasso_operation(document, operation)


def apply_lasso_operation(document: ModelDocument, operation: LassoOperation) -> TrimResult:
    """Replay a captured lasso operation against any aligned model resolution."""
    before = document.stats
    parts = tuple(
        trimmed for part in document.parts if (trimmed := _trim_part(part, operation)) is not None
    )
    if not parts:
        raise ValueError("The lasso would remove the entire model")

    source = document.source.with_name(f"{document.source.stem}_trimmed{document.source.suffix}")
    edited = ModelDocument(source=source, parts=parts)
    after = edited.stats
    return TrimResult(
        document=edited,
        removed_points=max(before.points - after.points, 0),
        removed_cells=max(before.cells - after.cells, 0),
    )


def create_low_res_document(document: ModelDocument, target_cells: int) -> ModelDocument:
    """Create a lighter display/editing proxy in the same coordinate system."""
    from pyvista import PolyData

    if target_cells < 1_000:
        raise ValueError("Low-resolution target must be at least 1,000 cells")
    mesh_cells = sum(part.dataset.n_cells for part in document.parts if part.kind == "mesh")
    if mesh_cells == 0:
        raise ValueError("The opened model has no mesh surface to simplify")

    parts: list[ModelPart] = []
    for part in document.parts:
        if part.kind != "mesh":
            continue
        surface = (
            part.dataset.copy(deep=True)
            if isinstance(part.dataset, PolyData)
            else part.dataset.extract_surface()
        )
        surface = surface.triangulate()
        part_target = max(500, round(target_cells * int(surface.n_cells) / mesh_cells))
        if int(surface.n_cells) > part_target:
            reduction = 1.0 - part_target / int(surface.n_cells)
            surface = surface.decimate(
                reduction,
                volume_preservation=True,
                enable_all_attribute_error=True,
            )
        parts.append(
            ModelPart(
                name=part.name,
                dataset=surface,
                kind="mesh",
                vertex_color=find_vertex_color(surface),
            )
        )
    source = document.source.with_name(f"{document.source.stem}_lores.ply")
    return ModelDocument(source=source, parts=tuple(parts))


def save_document(document: ModelDocument, path: str | Path) -> Path:
    """Save an edited document as a single PLY or VTP surface."""
    from pyvista import PolyData

    destination = Path(path).expanduser().resolve()
    if destination.suffix.lower() not in {".ply", ".vtp"}:
        raise ValueError("Edited models can be saved as PLY or VTP")

    surfaces: list[PolyData] = []
    for part in document.parts:
        dataset = part.dataset
        surface = dataset if isinstance(dataset, PolyData) else dataset.extract_surface()
        surfaces.append(surface)
    combined = surfaces[0] if len(surfaces) == 1 else surfaces[0].merge(surfaces[1:])
    if not isinstance(combined, PolyData):
        combined = combined.extract_surface()

    options: dict[str, object] = {}
    color_name = find_vertex_color(combined)
    if destination.suffix.lower() == ".ply" and color_name:
        colors = np.asarray(combined.point_data[color_name])
        if colors.dtype == np.uint8:
            options["texture"] = color_name
    combined.save(destination, binary=True, **options)
    return destination

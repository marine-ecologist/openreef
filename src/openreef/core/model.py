"""Format-neutral model representation and statistics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelPart:
    name: str
    dataset: Any
    kind: str
    vertex_color: str | None = None


@dataclass(frozen=True)
class ModelDocument:
    source: Path
    parts: tuple[ModelPart, ...]

    @property
    def stats(self) -> ModelStats:
        return ModelStats.from_document(self)


@dataclass(frozen=True)
class ModelStats:
    filename: str
    format: str
    kind: str
    parts: int
    points: int
    cells: int
    bounds: tuple[float, float, float, float, float, float]
    vertex_colors: bool

    @classmethod
    def from_document(cls, document: ModelDocument) -> ModelStats:
        kinds = {part.kind for part in document.parts}
        kind = next(iter(kinds)) if len(kinds) == 1 else "mixed"
        bounds = combine_bounds(part.dataset.bounds for part in document.parts)
        return cls(
            filename=document.source.name,
            format=document.source.suffix.removeprefix(".").upper(),
            kind=kind,
            parts=len(document.parts),
            points=sum(int(part.dataset.n_points) for part in document.parts),
            cells=sum(int(part.dataset.n_cells) for part in document.parts),
            bounds=bounds,
            vertex_colors=any(part.vertex_color is not None for part in document.parts),
        )

    def as_text(self) -> str:
        xmin, xmax, ymin, ymax, zmin, zmax = self.bounds
        size = (xmax - xmin, ymax - ymin, zmax - zmin)
        return "\n".join(
            (
                f"File: {self.filename}",
                f"Format: {self.format}",
                f"Type: {self.kind.replace('-', ' ').title()}",
                f"Parts: {self.parts:,}",
                f"Points: {self.points:,}",
                f"Cells: {self.cells:,}",
                f"Vertex color: {'Yes' if self.vertex_colors else 'No'}",
                "Bounds:",
                f"  X  {xmin:.4g} to {xmax:.4g}",
                f"  Y  {ymin:.4g} to {ymax:.4g}",
                f"  Z  {zmin:.4g} to {zmax:.4g}",
                f"Size: {size[0]:.4g} × {size[1]:.4g} × {size[2]:.4g}",
            )
        )


def combine_bounds(
    all_bounds: Iterable[tuple[float, float, float, float, float, float]],
) -> tuple[float, float, float, float, float, float]:
    values = list(all_bounds)
    if not values:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (
        min(item[0] for item in values),
        max(item[1] for item in values),
        min(item[2] for item in values),
        max(item[3] for item in values),
        min(item[4] for item in values),
        max(item[5] for item in values),
    )


def classify_dataset(dataset: Any) -> str:
    """Distinguish vertex-only PolyData from renderable mesh data."""
    faces = getattr(dataset, "faces", None)
    lines = getattr(dataset, "lines", None)
    if faces is not None and lines is not None:
        return "point-cloud" if len(faces) == 0 and len(lines) == 0 else "mesh"

    n_cells = int(getattr(dataset, "n_cells", 0))
    if n_cells == 0:
        return "point-cloud"
    return "mesh"


def find_vertex_color(dataset: Any) -> str | None:
    """Return the best point-data RGB/RGBA array name, if present."""
    point_data = getattr(dataset, "point_data", {})
    candidates: list[str] = []
    for name in point_data.keys():
        array = point_data[name]
        shape = getattr(array, "shape", ())
        normalized = str(name).lower()
        looks_like_color = any(token in normalized for token in ("rgb", "color", "colour"))
        if len(shape) == 2 and shape[1] in (3, 4) and looks_like_color:
            candidates.append(str(name))
    if not candidates:
        return None
    preferred = ("rgba", "rgb", "colors", "color", "vertex_colors", "vertex_color")
    lookup = {name.lower(): name for name in candidates}
    for name in preferred:
        if name in lookup:
            return lookup[name]
    return candidates[0]

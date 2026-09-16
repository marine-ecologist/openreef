"""Model file loading through PyVista/VTK."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pyvista as pv

from openreef.core.glb_edit import GLB_TRIANGLE_ID
from openreef.core.model import ModelDocument, ModelPart, classify_dataset, find_vertex_color
from openreef.io.gaussian_ply import read_gaussian_ply

SUPPORTED_EXTENSIONS = frozenset({".ply", ".obj", ".glb"})


class ModelLoadError(RuntimeError):
    """A model could not be converted into renderable datasets."""


def load_model(path: str | Path) -> ModelDocument:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ModelLoadError(f"Model does not exist: {source}")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ModelLoadError(f"Unsupported model format. Expected one of: {supported}")

    try:
        gaussian = read_gaussian_ply(source) if source.suffix.lower() == ".ply" else None
        loaded = gaussian if gaussian is not None else pv.read(source)
    except Exception as exc:
        hint = (
            " Your VTK build may not include a GLTF reader."
            if source.suffix.lower() == ".glb"
            else ""
        )
        raise ModelLoadError(f"Could not open {source.name}: {exc}.{hint}") from exc

    parts_list: list[ModelPart] = []
    triangle_offset = 0
    for name, dataset in _iter_datasets(loaded):
        if int(getattr(dataset, "n_points", 0)) <= 0:
            continue
        kind = classify_dataset(dataset)
        if source.suffix.lower() == ".glb" and kind == "mesh":
            dataset.cell_data[GLB_TRIANGLE_ID] = np.arange(
                triangle_offset,
                triangle_offset + int(dataset.n_cells),
                dtype=np.int64,
            )
            triangle_offset += int(dataset.n_cells)
        parts_list.append(
            ModelPart(
                name=name,
                dataset=dataset,
                kind=kind,
                vertex_color=find_vertex_color(dataset),
            )
        )
    parts = tuple(parts_list)
    if not parts:
        raise ModelLoadError(f"{source.name} contains no renderable points or surfaces")
    return ModelDocument(
        source=source,
        parts=parts,
        material_source=source if source.suffix.lower() == ".glb" else None,
    )


def _iter_datasets(value: Any, prefix: str = "Part") -> Iterator[tuple[str, Any]]:
    if isinstance(value, pv.MultiBlock):
        for index in range(value.n_blocks):
            block = value[index]
            if block is None:
                continue
            name = value.get_block_name(index) or f"{prefix} {index + 1}"
            yield from _iter_datasets(block, name)
        return
    yield prefix, value

"""Model file loading through PyVista/VTK."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pyvista as pv

from openreef.core.model import ModelDocument, ModelPart, classify_dataset, find_vertex_color

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
        loaded = pv.read(source)
    except Exception as exc:
        hint = (
            " Your VTK build may not include a GLTF reader."
            if source.suffix.lower() == ".glb"
            else ""
        )
        raise ModelLoadError(f"Could not open {source.name}: {exc}.{hint}") from exc

    parts = tuple(
        ModelPart(
            name=name,
            dataset=dataset,
            kind=classify_dataset(dataset),
            vertex_color=find_vertex_color(dataset),
        )
        for name, dataset in _iter_datasets(loaded)
        if int(getattr(dataset, "n_points", 0)) > 0
    )
    if not parts:
        raise ModelLoadError(f"{source.name} contains no renderable points or surfaces")
    return ModelDocument(source=source, parts=parts)


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

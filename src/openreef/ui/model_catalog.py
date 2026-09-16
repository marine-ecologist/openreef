"""Discover and group Viewer models stored in a dataset's models folder."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from openreef.pipeline.stages import MESH_EXTENSIONS, DatasetLayout, dataset_label


@dataclass(frozen=True)
class ModelCatalogItem:
    label: str
    path: Path


@dataclass(frozen=True)
class ModelCatalogSection:
    title: str
    items: tuple[ModelCatalogItem, ...]


SECTION_ORDER = (
    "Sparse cloud",
    "Dense cloud",
    "Surface mesh",
    "Texture mesh",
    "Gaussian splat",
    "3D tiles",
    "Custom saves",
)
LEVEL_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Compact": 3}


def discover_model_catalog(layout: DatasetLayout) -> tuple[ModelCatalogSection, ...]:
    """Return a one-column, hierarchical catalogue for the Viewer selector."""
    grouped: dict[str, list[ModelCatalogItem]] = {title: [] for title in SECTION_ORDER}
    seen: dict[str, set[Path]] = {title: set() for title in SECTION_ORDER}
    if layout.models.is_dir():
        try:
            candidates = sorted(layout.models.iterdir(), key=lambda path: path.name.casefold())
        except OSError:
            candidates = []
        for path in candidates:
            is_tiled_entry = path.name.casefold().endswith("_3d_tiles.json")
            if not path.is_file() or (
                path.suffix.lower() not in MESH_EXTENSIONS and not is_tiled_entry
            ):
                continue
            section, label = _classify(path, dataset_label(layout))
            try:
                identity = path.resolve()
            except OSError:
                identity = path.absolute()
            if identity in seen[section]:
                continue
            seen[section].add(identity)
            grouped[section].append(ModelCatalogItem(label, path.resolve()))

    sparse = layout.sparse_model()
    if sparse is not None:
        grouped["Sparse cloud"].insert(0, ModelCatalogItem("Points + cameras", sparse))

    sections: list[ModelCatalogSection] = []
    for title in SECTION_ORDER:
        items = grouped[title]
        if not items:
            continue
        if title != "Custom saves":
            special = [item for item in items if item.label == "Points + cameras"]
            levels = [item for item in items if item.label != "Points + cameras"]
            levels.sort(key=lambda item: (LEVEL_ORDER.get(item.label, 99), item.label.casefold()))
            items = [*special, *levels]
        sections.append(ModelCatalogSection(title, tuple(items)))
    return tuple(sections)


def _classify(path: Path, dataset: str) -> tuple[str, str]:
    escaped = re.escape(dataset)
    stem = path.stem
    if stem.casefold() == f"{dataset}_3d_tiles".casefold():
        return "3D tiles", "Streaming viewer"
    levels = "high|original|medium|low|compact"
    patterns = (
        ("Sparse cloud", rf"^{escaped}_(?:sparsecloud|pointcloud)(?:_({levels}))?$"),
        ("Dense cloud", rf"^{escaped}_densecloud(?:_({levels}))?$"),
        ("Surface mesh", rf"^{escaped}_mesh(?:_({levels}))?$"),
        ("Texture mesh", rf"^{escaped}_textured_mesh(?:_({levels}))?$"),
        ("Gaussian splat", rf"^{escaped}_gaussian(?:_({levels}))?$"),
    )
    for section, pattern in patterns:
        match = re.match(pattern, stem, flags=re.IGNORECASE)
        if match:
            level = (match.group(1) or "high").lower()
            return section, "High" if level in {"high", "original"} else level.title()
    return "Custom saves", path.name

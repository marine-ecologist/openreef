from pathlib import Path
from types import SimpleNamespace

from openreef.core.model import ModelDocument, ModelPart, classify_dataset, find_vertex_color


class Array:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


def dataset(**changes: object) -> SimpleNamespace:
    values = {
        "n_points": 8,
        "n_cells": 6,
        "faces": (3, 0, 1, 2),
        "lines": (),
        "bounds": (0.0, 2.0, -1.0, 1.0, 5.0, 8.0),
        "point_data": {},
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_model_statistics() -> None:
    model = dataset()
    document = ModelDocument(Path("reef.ply"), (ModelPart("Reef", model, "mesh", "RGB"),))
    stats = document.stats
    assert stats.format == "PLY"
    assert stats.points == 8
    assert stats.cells == 6
    assert stats.vertex_colors is True
    assert "2 × 2 × 3" in stats.as_text()


def test_point_cloud_classification() -> None:
    assert classify_dataset(dataset(faces=(), lines=())) == "point-cloud"
    assert classify_dataset(dataset(faces=(), lines=(2, 0, 1))) == "mesh"


def test_vertex_color_prefers_rgb_name() -> None:
    model = dataset(point_data={"normals": Array((8, 3)), "RGB": Array((8, 3))})
    assert find_vertex_color(model) == "RGB"


def test_normals_are_not_mistaken_for_color() -> None:
    model = dataset(point_data={"normals": Array((8, 3))})
    assert find_vertex_color(model) is None

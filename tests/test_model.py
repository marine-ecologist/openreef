import struct
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyvista as pv

from openreef.core.model import ModelDocument, ModelPart, classify_dataset, find_vertex_color
from openreef.core.scene import SceneController, is_gaussian_splat
from openreef.io.gaussian_ply import (
    clean_gaussian_document,
    read_gaussian_ply,
    write_gaussian_ply,
)
from openreef.io.model_loader import load_model


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


def test_gaussian_splat_detection_requires_render_attributes() -> None:
    names = {
        "f_dc_0",
        "f_dc_1",
        "f_dc_2",
        "opacity",
        "scale_0",
        "scale_1",
        "scale_2",
        "rot_0",
        "rot_1",
        "rot_2",
        "rot_3",
    }
    splat = dataset(point_data={name: Array((8,)) for name in names})
    document = ModelDocument(Path("reef_gaussian.ply"), (ModelPart("Splat", splat, "point-cloud"),))

    assert is_gaussian_splat(document)
    assert not is_gaussian_splat(
        ModelDocument(Path("reef.ply"), (ModelPart("Cloud", dataset(), "point-cloud"),))
    )


def test_gaussian_ply_loader_retains_opensplat_attributes(tmp_path: Path) -> None:
    names = (
        "x",
        "y",
        "z",
        "f_dc_0",
        "f_dc_1",
        "f_dc_2",
        "opacity",
        "scale_0",
        "scale_1",
        "scale_2",
        "rot_0",
        "rot_1",
        "rot_2",
        "rot_3",
    )
    header = "\n".join(
        (
            "ply",
            "format binary_little_endian 1.0",
            "element vertex 1",
            *(f"property float {name}" for name in names),
            "end_header",
            "",
        )
    ).encode("ascii")
    source = tmp_path / "reef_gaussian.ply"
    source.write_bytes(header + struct.pack("<14f", *range(14)))

    document = load_model(source)

    assert is_gaussian_splat(document)
    assert np.asarray(document.parts[0].dataset.point_data["opacity"])[0] == 6


def test_gaussian_cleanup_and_save_preserve_render_attributes(tmp_path: Path) -> None:
    import pyvista as pv

    cloud = pv.PolyData(np.asarray(((0, 0, 0), (1, 0, 0), (3, 0, 0)), dtype=float))
    attributes = (
        "f_dc_0",
        "f_dc_1",
        "f_dc_2",
        "scale_0",
        "scale_1",
        "scale_2",
        "rot_0",
        "rot_1",
        "rot_2",
        "rot_3",
    )
    for name in attributes:
        cloud.point_data[name] = np.zeros(3, dtype=np.float32)
    cloud.point_data["opacity"] = np.asarray((-5.0, 2.0, 2.0), dtype=np.float32)
    document = ModelDocument(
        tmp_path / "source.ply",
        (ModelPart("Splat", cloud, "point-cloud"),),
    )

    result = clean_gaussian_document(
        document,
        minimum_opacity=0.5,
        maximum_scale_percentile=100,
        maximum_aspect_ratio=100,
        bounds=(-1, 2, -1, 1, -1, 1),
    )
    destination = write_gaussian_ply(result.document, tmp_path / "cleaned.ply")
    reloaded = load_model(destination)

    assert result.retained == 1
    assert result.removed == 2
    assert reloaded.stats.points == 1
    assert is_gaussian_splat(reloaded)


def test_gaussian_cleanup_removes_extremely_stretched_splats(tmp_path: Path) -> None:
    cloud = pv.PolyData(np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))))
    for name in ("f_dc_0", "f_dc_1", "f_dc_2", "rot_0", "rot_1", "rot_2", "rot_3"):
        cloud.point_data[name] = np.zeros(2, dtype=np.float32)
    cloud.point_data["opacity"] = np.ones(2, dtype=np.float32)
    cloud.point_data["scale_0"] = np.asarray((0.0, 0.0), dtype=np.float32)
    cloud.point_data["scale_1"] = np.asarray((0.0, 0.0), dtype=np.float32)
    cloud.point_data["scale_2"] = np.asarray((0.0, np.log(100.0)), dtype=np.float32)
    document = ModelDocument(
        tmp_path / "source.ply",
        (ModelPart("Splat", cloud, "point-cloud"),),
    )

    result = clean_gaussian_document(
        document,
        minimum_opacity=0.0,
        maximum_scale_percentile=100,
        maximum_aspect_ratio=50,
    )

    assert result.retained == 1
    assert result.removed == 1


def test_non_gaussian_ply_with_vertex_lists_is_left_for_standard_loader(
    tmp_path: Path,
) -> None:
    source = tmp_path / "dense_cloud.ply"
    source.write_bytes(
        b"ply\n"
        b"format binary_little_endian 1.0\n"
        b"element vertex 0\n"
        b"property float32 x\n"
        b"property float32 y\n"
        b"property float32 z\n"
        b"property list uint8 uint32 view_indices\n"
        b"property list uint8 float32 view_weights\n"
        b"end_header\n"
    )

    assert read_gaussian_ply(source) is None


def test_glb_material_import_ignores_non_mesh_helper_actors() -> None:
    class Property2D:
        pass

    class Mapper:
        def __init__(self) -> None:
            self.dataset = None

        def SetInputData(self, dataset: object) -> None:  # noqa: N802
            self.dataset = dataset

    class Property3D:
        representation = ""

        def __init__(self, material: str = "") -> None:
            self.material = material

        def SetRepresentationToWireframe(self) -> None:  # noqa: N802
            self.representation = "wireframe"

        def SetRepresentationToSurface(self) -> None:  # noqa: N802
            self.representation = "surface"

        def SetEdgeVisibility(self, value: bool) -> None:  # noqa: N802, ARG002
            pass

    class Actor:
        def __init__(self, prop: object) -> None:
            self.prop = prop
            self.mapper = Mapper()

        def GetProperty(self) -> object:  # noqa: N802
            return self.prop

        def GetMapper(self) -> Mapper:  # noqa: N802
            return self.mapper

    class Plotter:
        def __init__(self) -> None:
            self.renderer = SimpleNamespace(actors={})
            self.mesh_property = Property3D("embedded texture")
            self.added_mesh: Actor | None = None

        def set_background(self, *args: object, **kwargs: object) -> None:
            pass

        def add_axes(self, **kwargs: object) -> None:
            self.renderer.actors["axes"] = Actor(Property2D())

        def clear(self) -> None:
            self.renderer.actors.clear()

        def import_gltf(self, *args: object, **kwargs: object) -> None:
            if "trimmed" in str(args[0]):
                raise FileNotFoundError
            self.renderer.actors["helper"] = Actor(Property2D())
            self.renderer.actors["mesh"] = Actor(self.mesh_property)

        def add_mesh(self, *args: object, **kwargs: object) -> Actor:
            self.added_mesh = Actor(Property3D())
            return self.added_mesh

        def add_actor(self, actor: Actor, **kwargs: object) -> None:
            self.added_mesh = actor
            self.renderer.actors["edited"] = actor

        def reset_camera(self) -> None:
            pass

        def reset_camera_clipping_range(self) -> None:
            pass

        def render(self) -> None:
            pass

    plotter = Plotter()
    controller = SceneController(plotter)
    source = Path("reef.glb").resolve()
    controller.set_document(ModelDocument(source, (), material_source=source))

    assert len(controller._actors) == 1
    assert plotter.mesh_property.representation == "wireframe"

    edited = ModelDocument(
        Path("reef_trimmed.glb").resolve(),
        (ModelPart("Reef", dataset(), "mesh"),),
        material_source=source,
    )
    controller.set_document(edited)

    assert plotter.added_mesh is not None
    assert plotter.added_mesh.GetProperty().material == "embedded texture"

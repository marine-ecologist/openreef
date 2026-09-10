import json
import os
import struct
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import pyvista as pv

from openreef.pipeline.runner import format_elapsed, strip_ansi
from openreef.pipeline.stages import (
    DatasetLayout,
    PipelineOptions,
    StageConfigurationError,
    StageKey,
    build_stage_command,
    sparse_model_identity,
    stage_output_exists,
    sync_model_links,
)


def prepare_selected_sparse_chain(layout: DatasetLayout) -> None:
    model = layout.sparse / "0"
    model.mkdir(parents=True, exist_ok=True)
    (model / "cameras.bin").touch()
    (model / "images.bin").write_bytes(struct.pack("<Q", 5))
    (model / "points3D.bin").write_bytes(struct.pack("<Q", 100))
    (layout.dense / "images").mkdir(parents=True, exist_ok=True)
    dense_sparse = layout.dense / "sparse"
    dense_sparse.mkdir(parents=True, exist_ok=True)
    for name in ("cameras.bin", "images.bin", "points3D.bin"):
        (dense_sparse / name).touch()
    layout.undistort_selection_state.write_text(
        json.dumps(sparse_model_identity(model)), encoding="utf-8"
    )
    os.utime(layout.undistort_selection_state, ns=(1, 1))
    layout.openmvs.mkdir(parents=True, exist_ok=True)
    layout.scene.touch()
    os.utime(layout.scene, ns=(2, 2))


def test_dataset_layout_and_image_count(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "a.jpg").touch()
    (images / "b.PNG").touch()
    (images / "notes.txt").touch()
    layout = DatasetLayout.from_path(tmp_path)
    assert layout.image_count() == 2
    assert layout.database == tmp_path / "colmap" / "database.db"
    assert layout.dense_cloud == tmp_path / "openmvs" / "scene_dense.ply"
    assert layout.surface_mesh == tmp_path / "openmvs" / "scene_mesh.ply"
    assert layout.models == tmp_path / "models"
    assert layout.meshes == layout.models


def test_reconstruction_outputs_are_linked_into_models_folder(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    layout.openmvs.mkdir(parents=True)
    dense = layout.openmvs / "scene_dense.ply"
    mesh = layout.openmvs / "scene_mesh.ply"
    low = layout.openmvs / "scene_dense_low.ply"
    medium = layout.openmvs / "scene_dense_medium.ply"
    dense.touch()
    low.touch()
    medium.touch()
    mesh.touch()

    links = sync_model_links(layout)

    assert {path.name for path in links} == {
        f"{tmp_path.name}_densecloud.ply",
        f"{tmp_path.name}_densecloud_high.ply",
        f"{tmp_path.name}_densecloud_low.ply",
        f"{tmp_path.name}_densecloud_medium.ply",
        f"{tmp_path.name}_mesh.ply",
        f"{tmp_path.name}_mesh_original.ply",
    }
    dense_link = layout.models / f"{tmp_path.name}_densecloud.ply"
    assert dense_link.is_symlink()
    assert dense_link.resolve() == dense.resolve()


def test_textured_mesh_levels_are_linked_without_name_collisions(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    layout.openmvs.mkdir(parents=True)
    for name in (
        "scene_mesh.ply",
        "scene_mesh_medium.ply",
        "scene_mesh_low.ply",
        "scene_mesh_textured.glb",
        "scene_mesh_medium_textured.glb",
        "scene_mesh_low_textured.glb",
    ):
        (layout.openmvs / name).touch()

    links = sync_model_links(layout)
    names = {path.name for path in links}

    assert f"{tmp_path.name}_textured_mesh.glb" in names
    assert f"{tmp_path.name}_textured_mesh_original.glb" in names
    assert f"{tmp_path.name}_textured_mesh_medium.glb" in names
    assert f"{tmp_path.name}_textured_mesh_low.glb" in names


def test_roi_change_invalidates_openmvs_outputs(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    prepare_selected_sparse_chain(layout)
    layout.models.mkdir()
    layout.dense_scene.touch()
    layout.dense_cloud.touch()
    layout.surface_mesh.touch()
    os.utime(layout.scene, ns=(2, 2))
    os.utime(layout.dense_scene, ns=(2, 2))
    os.utime(layout.dense_cloud, ns=(2, 2))
    os.utime(layout.surface_mesh, ns=(3, 3))
    assert stage_output_exists(StageKey.OPENMVS_IMPORT, layout)
    assert stage_output_exists(StageKey.DENSE, layout)
    assert stage_output_exists(StageKey.MESH, layout)

    roi = {"bounds": [0, 1, 0, 1, 0, 1]}
    layout.roi.write_text(json.dumps(roi), encoding="utf-8")
    assert not stage_output_exists(StageKey.OPENMVS_IMPORT, layout)
    assert not stage_output_exists(StageKey.DENSE, layout)
    assert not stage_output_exists(StageKey.MESH, layout)

    layout.imported_roi_state.write_text(json.dumps({"roi": roi}), encoding="utf-8")
    assert stage_output_exists(StageKey.OPENMVS_IMPORT, layout)
    assert stage_output_exists(StageKey.DENSE, layout)
    assert stage_output_exists(StageKey.MESH, layout)


def test_legacy_mesh_folder_moves_to_root_models(tmp_path: Path) -> None:
    legacy = tmp_path / "images" / "meshes"
    legacy.mkdir(parents=True)
    (legacy / "manual_edit.ply").write_text("manual", encoding="utf-8")
    layout = DatasetLayout(tmp_path)

    sync_model_links(layout)

    assert (layout.models / "manual_edit.ply").read_text(encoding="utf-8") == "manual"
    assert layout.legacy_meshes.is_symlink()
    assert layout.legacy_meshes.resolve() == layout.models.resolve()


def test_feature_command_uses_resource_and_camera_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "reef.jpg").touch()
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")
    options = PipelineOptions(
        cores=6,
        camera_model="OPENCV",
        single_camera=False,
        use_gpu=False,
        max_image_size=2400,
    )
    command = build_stage_command(StageKey.FEATURES, DatasetLayout(tmp_path), options)
    assert command.program == "/colmap"
    assert ("--FeatureExtraction.num_threads", "6") == command.arguments[-6:-4]
    assert "OPENCV" in command.arguments
    assert command.arguments[-1] == "0"


def test_stage_validation_catches_missing_prerequisite(tmp_path: Path) -> None:
    with pytest.raises(StageConfigurationError, match="feature extraction"):
        build_stage_command(
            StageKey.MATCHING,
            DatasetLayout(tmp_path),
            PipelineOptions(cores=4),
        )


def test_sparse_stage_exports_a_named_point_cloud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "reef.jpg").touch()
    colmap = tmp_path / "colmap"
    colmap.mkdir()
    (colmap / "database.db").touch()
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    command = build_stage_command(
        StageKey.SPARSE,
        DatasetLayout(tmp_path),
        PipelineOptions(cores=4),
    )

    assert command.arguments == (
        "-m",
        "openreef.pipeline.tasks",
        "sparse-colmap",
        "--executable",
        "/colmap",
        "--database",
        str(tmp_path / "colmap" / "database.db"),
        "--images",
        str(images),
        "--output",
        str(tmp_path / "colmap" / "sparse"),
        "--cores",
        "4",
    )


def test_openmvs_import_receives_roi_not_sparse_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = DatasetLayout(tmp_path)
    (layout.dense / "images").mkdir(parents=True)
    sparse = layout.dense / "sparse"
    sparse.mkdir()
    for name in ("cameras.bin", "images.bin", "points3D.bin"):
        (sparse / name).touch()
    prepare_selected_sparse_chain(layout)
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    command = build_stage_command(
        StageKey.OPENMVS_IMPORT,
        layout,
        PipelineOptions(cores=6),
    )

    assert "sparse-colmap" not in command.arguments
    assert command.arguments[command.arguments.index("--roi") + 1] == str(layout.roi)
    assert command.arguments[command.arguments.index("--sparse-model") + 1] == "0"


def test_sparse_output_detection(tmp_path: Path) -> None:
    model = tmp_path / "colmap" / "sparse" / "0"
    model.mkdir(parents=True)
    (model / "cameras.bin").touch()
    (model / "images.bin").touch()
    (model / "points3D.bin").touch()
    assert stage_output_exists(StageKey.SPARSE, DatasetLayout(tmp_path))


def test_sparse_models_prefer_most_registered_images_and_persist_selection(
    tmp_path: Path,
) -> None:
    layout = DatasetLayout(tmp_path)
    for name, images, points in (("0", 17, 2_685), ("1", 10, 737), ("2", 26, 2_685)):
        model = layout.sparse / name
        model.mkdir(parents=True)
        (model / "cameras.bin").touch()
        (model / "images.bin").write_bytes(struct.pack("<Q", images))
        (model / "points3D.bin").write_bytes(struct.pack("<Q", points))

    assert [model.name for model in layout.sparse_models()] == ["0", "1", "2"]
    assert layout.sparse_model() == layout.sparse / "2"

    layout.select_sparse_model(layout.sparse / "0")

    assert layout.selected_sparse.is_symlink()
    assert layout.selected_sparse.resolve() == (layout.sparse / "0").resolve()
    assert layout.sparse_model() == (layout.sparse / "0").resolve()


def test_undistortion_uses_selected_sparse_model_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = DatasetLayout(tmp_path)
    layout.images.mkdir()
    for name, image_count in (("0", 5), ("1", 12)):
        model = layout.sparse / name
        model.mkdir(parents=True)
        (model / "cameras.bin").touch()
        (model / "images.bin").write_bytes(struct.pack("<Q", image_count))
        (model / "points3D.bin").write_bytes(struct.pack("<Q", 100))
    layout.select_sparse_model(layout.sparse / "0")
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    command = build_stage_command(StageKey.UNDISTORT, layout, PipelineOptions(cores=4))

    input_index = command.arguments.index("--input") + 1
    assert Path(command.arguments[input_index]).resolve() == (layout.sparse / "0").resolve()


def test_surface_mesh_command_and_output_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = DatasetLayout(tmp_path)
    prepare_selected_sparse_chain(layout)
    layout.dense_scene.touch()
    layout.dense_cloud.touch()
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    command = build_stage_command(StageKey.MESH, layout, PipelineOptions(cores=7))

    assert command.program.endswith("python")
    assert "mesh-multi" in command.arguments
    assert "/ReconstructMesh" in command.arguments
    levels_index = command.arguments.index("--levels") + 1
    assert command.arguments[levels_index] == "original"
    assert not stage_output_exists(StageKey.MESH, layout)
    layout.surface_mesh.touch()
    assert stage_output_exists(StageKey.MESH, layout)


def test_texture_command_and_output_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = DatasetLayout(tmp_path)
    prepare_selected_sparse_chain(layout)
    layout.dense_scene.touch()
    layout.dense_cloud.touch()
    layout.surface_mesh.touch()
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")
    options = PipelineOptions(
        cores=7,
        texture_resolution_level=1,
        max_texture_size=4096,
        texture_sharpness=0.7,
        local_seam_leveling=False,
    )

    command = build_stage_command(StageKey.TEXTURE, layout, options)

    assert command.program.endswith("python")
    assert "texture-multi" in command.arguments
    assert "/TextureMesh" in command.arguments
    assert command.arguments[command.arguments.index("--levels") + 1] == "original"
    assert command.arguments[command.arguments.index("--resolution-level") + 1] == "1"
    assert command.arguments[command.arguments.index("--max-texture-size") + 1] == "4096"
    assert command.arguments[command.arguments.index("--sharpness-weight") + 1] == "0.7"
    assert command.arguments[command.arguments.index("--local-seam-leveling") + 1] == "0"
    assert not stage_output_exists(StageKey.TEXTURE, layout, options)
    (layout.openmvs / "scene_mesh_textured.glb").touch()
    assert stage_output_exists(StageKey.TEXTURE, layout, options)


def test_dense_command_requests_optional_viewing_clouds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = DatasetLayout(tmp_path)
    prepare_selected_sparse_chain(layout)
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    options = PipelineOptions(cores=6, dense_low=True, dense_medium=True)
    command = build_stage_command(StageKey.DENSE, layout, options)

    assert command.program.endswith("python")
    assert "dense-multi" in command.arguments
    levels_index = command.arguments.index("--levels") + 1
    assert command.arguments[levels_index] == "original,medium,low"
    assert command.arguments[command.arguments.index("--medium-percent") + 1] == "20"
    assert command.arguments[command.arguments.index("--low-percent") + 1] == "5"


def test_dense_output_detection_includes_requested_previews(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    prepare_selected_sparse_chain(layout)
    layout.dense_scene.touch()
    layout.dense_cloud.touch()
    options = PipelineOptions(cores=2, dense_low=True, dense_medium=True)

    assert stage_output_exists(StageKey.DENSE, layout)
    assert not stage_output_exists(StageKey.DENSE, layout, options)
    layout.dense_cloud_low.touch()
    layout.dense_cloud_medium.touch()
    layout.dense_levels_state.write_text(
        json.dumps(
            {
                "source_mtime_ns": layout.dense_cloud.stat().st_mtime_ns,
                "levels": {"original": 100, "medium": 20, "low": 5},
            }
        ),
        encoding="utf-8",
    )
    assert stage_output_exists(StageKey.DENSE, layout, options)

    changed = PipelineOptions(cores=2, dense_medium=True, dense_medium_percent=30)
    assert not stage_output_exists(StageKey.DENSE, layout, changed)


def test_dense_previews_preserve_colors_and_reduce_points(tmp_path: Path) -> None:
    from openreef.pipeline.tasks import _write_dense_previews

    source = tmp_path / "scene_dense.ply"
    cloud = pv.PolyData(np.arange(300_000, dtype=float).reshape(100_000, 3))
    cloud.point_data["RGB"] = np.tile(
        np.array([[12, 34, 56]], dtype=np.uint8), (cloud.n_points, 1)
    )
    cloud.save(source, texture="RGB")
    low = tmp_path / "scene_dense_low.ply"
    medium = tmp_path / "scene_dense_medium.ply"

    _write_dense_previews(source, {"low": (low, 0.05), "medium": (medium, 0.20)})

    low_cloud = pv.read(low)
    medium_cloud = pv.read(medium)
    assert low_cloud.n_points == 5_000
    assert medium_cloud.n_points == 20_000
    assert "RGB" in low_cloud.point_data
    assert low_cloud.point_data["RGB"][0].tolist() == [12, 34, 56]


def test_dense_preview_preserves_openmvs_camera_view_lists(tmp_path: Path) -> None:
    from openreef.pipeline.tasks import _write_dense_previews

    source = tmp_path / "scene_dense.ply"
    header = (
        b"ply\nformat binary_little_endian 1.0\nelement vertex 4\n"
        b"property float32 x\nproperty float32 y\nproperty float32 z\n"
        b"property uint8 red\nproperty uint8 green\nproperty uint8 blue\n"
        b"property float32 nx\nproperty float32 ny\nproperty float32 nz\n"
        b"property list uint8 uint32 view_indices\n"
        b"property list uint8 float32 view_weights\nend_header\n"
    )
    records = bytearray()
    for index in range(4):
        records.extend(struct.pack("<fffBBBfff", index, 0, 0, 1, 2, 3, 0, 0, 1))
        records.extend(struct.pack("<BII", 2, index, index + 10))
        records.extend(struct.pack("<Bff", 2, 0.75, 0.25))
    source.write_bytes(header + records)
    output = tmp_path / "scene_dense_medium.ply"

    _write_dense_previews(source, {"medium": (output, 0.5)})

    payload = output.read_bytes()
    output_header, vertex_data = payload.split(b"end_header\n", 1)
    assert b"element vertex 2" in output_header
    assert len(vertex_data) == 2 * 45
    assert struct.unpack_from("<f", vertex_data, 0)[0] == 1
    assert struct.unpack_from("<BII", vertex_data, 27) == (2, 1, 11)
    assert struct.unpack_from("<f", vertex_data, 45)[0] == 3
    assert struct.unpack_from("<BII", vertex_data, 45 + 27) == (2, 3, 13)


def test_mesh_multi_passes_each_dense_cloud_to_openmvs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from openreef.pipeline.tasks import mesh_multi

    for name in ("scene_dense.ply", "scene_dense_medium.ply", "scene_dense_low.ply"):
        (tmp_path / name).touch()
    commands: list[list[str]] = []

    def record(command: list[str], **kwargs: object) -> SimpleNamespace:
        commands.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("openreef.pipeline.tasks.subprocess.run", record)
    result = mesh_multi(
        Namespace(
            executable="/ReconstructMesh",
            openmvs_folder=str(tmp_path),
            levels="original,medium,low",
            original_percent=100,
            medium_percent=20,
            low_percent=5,
            cores=8,
        )
    )

    assert result == 0
    assert [command[command.index("-p") + 1] for command in commands] == [
        "scene_dense.ply",
        "scene_dense_medium.ply",
        "scene_dense_low.ply",
    ]
    assert [command[command.index("-o") + 1] for command in commands] == [
        "scene_mesh.mvs",
        "scene_mesh_medium.mvs",
        "scene_mesh_low.mvs",
    ]


def test_texture_multi_exports_each_selected_mesh_as_glb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from openreef.pipeline.tasks import texture_multi

    for name in ("scene_mesh.ply", "scene_mesh_medium.ply", "scene_mesh_low.ply"):
        (tmp_path / name).touch()
    commands: list[list[str]] = []

    def record(command: list[str], **kwargs: object) -> SimpleNamespace:
        commands.append(command)
        output = Path(command[command.index("-o") + 1]).with_suffix(".glb")
        (tmp_path / output).touch()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("openreef.pipeline.tasks.subprocess.run", record)
    result = texture_multi(
        Namespace(
            executable="/TextureMesh",
            openmvs_folder=str(tmp_path),
            levels="original,medium,low",
            cores=8,
            resolution_level=0,
            max_texture_size=8192,
            sharpness_weight=0.5,
            global_seam_leveling=1,
            local_seam_leveling=1,
        )
    )

    assert result == 0
    assert [command[command.index("-m") + 1] for command in commands] == [
        "scene_mesh.ply",
        "scene_mesh_medium.ply",
        "scene_mesh_low.ply",
    ]
    assert [command[command.index("-o") + 1] for command in commands] == [
        "scene_mesh_textured.mvs",
        "scene_mesh_medium_textured.mvs",
        "scene_mesh_low_textured.mvs",
    ]
    assert all(command[command.index("--export-type") + 1] == "glb" for command in commands)


def test_terminal_helpers() -> None:
    assert strip_ansi("\x1b[31mERROR\x1b[0m\r\n") == "ERROR\n"
    assert format_elapsed(65) == "01:05"
    assert format_elapsed(3661) == "1:01:01"

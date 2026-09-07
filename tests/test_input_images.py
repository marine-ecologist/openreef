from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from openreef.io.color_correction import enhance_underwater
from openreef.pipeline.input_tasks import prepare
from openreef.ui.input_images_page import _format_milliseconds


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    image = np.full((24, 32, 3), color, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def options(dataset: Path, source: Path, color_correct: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        dataset=str(dataset),
        source_kind="photos",
        source=str(source),
        interval=1.0,
        color_correct=color_correct,
        jpeg_quality=98,
    )


def test_photo_input_preserves_originals_and_builds_images(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    source = tmp_path / "source"
    dataset.mkdir()
    source.mkdir()
    write_image(source / "reef.jpg", (40, 90, 120))

    assert prepare(options(dataset, source)) == 0
    assert (dataset / "original" / "reef.jpg").is_file()
    assert (dataset / "images" / "reef.jpg").is_file()


def test_existing_images_are_adopted_before_color_correction(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    images = dataset / "images"
    images.mkdir(parents=True)
    write_image(images / "frame.jpg", (100, 120, 40))
    colmap = dataset / "colmap"
    colmap.mkdir()
    (colmap / "database.db").touch()

    job = SimpleNamespace(
        dataset=str(dataset),
        source_kind="existing",
        source=str(images),
        interval=1.0,
        color_correct=True,
        jpeg_quality=98,
    )
    assert prepare(job) == 0
    assert (dataset / "original" / "frame.jpg").is_file()
    assert (dataset / "images" / "frame.jpg").is_file()
    assert not colmap.exists()
    assert list((dataset / ".openreef" / "history").glob("*/colmap/database.db"))


def test_unchanged_existing_images_keep_reconstruction(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    images = dataset / "images"
    images.mkdir(parents=True)
    write_image(images / "frame.jpg", (100, 120, 40))
    colmap = dataset / "colmap"
    colmap.mkdir()
    (colmap / "database.db").touch()
    job = SimpleNamespace(
        dataset=str(dataset),
        source_kind="existing",
        source=str(images),
        interval=1.0,
        color_correct=False,
        jpeg_quality=98,
    )

    assert prepare(job) == 0
    assert (colmap / "database.db").is_file()


def test_image_rebuild_preserves_mesh_folder_and_refreshes_links(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    images = dataset / "images"
    meshes = images / "meshes"
    meshes.mkdir(parents=True)
    write_image(images / "frame.jpg", (100, 120, 40))
    (meshes / "manual_edit.ply").write_text("manual", encoding="utf-8")
    openmvs = dataset / "openmvs"
    openmvs.mkdir()
    generated = openmvs / "scene_mesh.ply"
    generated.write_text("generated", encoding="utf-8")

    job = options(dataset, images)
    job.source_kind = "existing"
    assert prepare(job) == 0

    assert (meshes / "manual_edit.ply").read_text(encoding="utf-8") == "manual"
    generated_link = meshes / "dataset_mesh.ply"
    assert generated_link.is_symlink()
    assert generated_link.resolve() == generated.resolve()


def test_underwater_correction_preserves_shape_and_type() -> None:
    image = np.full((20, 30, 3), (120, 90, 30), dtype=np.uint8)
    corrected = enhance_underwater(image)
    assert corrected.shape == image.shape
    assert corrected.dtype == np.uint8
    assert not np.array_equal(corrected, image)


def test_video_time_format() -> None:
    assert _format_milliseconds(65_000) == "01:05"
    assert _format_milliseconds(3_661_000) == "1:01:01"

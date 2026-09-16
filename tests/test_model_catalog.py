from pathlib import Path

from openreef.pipeline.stages import DatasetLayout
from openreef.ui.model_catalog import discover_model_catalog


def test_model_catalog_groups_levels_and_custom_saves(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    layout.models.mkdir()
    dense = tmp_path / "dense.ply"
    dense.touch()
    (layout.models / f"{tmp_path.name}_densecloud.ply").symlink_to(dense)
    (layout.models / f"{tmp_path.name}_densecloud_high.ply").symlink_to(dense)
    (layout.models / f"{tmp_path.name}_densecloud_low.ply").touch()
    (layout.models / f"{tmp_path.name}_gaussian_medium.ply").touch()
    layout.tiled_model_manifest.write_text('{"format":"openreef-3d-tiles"}')
    (layout.models / f"{tmp_path.name}_mesh_edited.ply").touch()
    (layout.models / "colony_crop.glb").touch()

    sections = discover_model_catalog(layout)
    by_title = {section.title: section for section in sections}

    assert [item.label for item in by_title["Dense cloud"].items] == ["High", "Low"]
    assert [item.label for item in by_title["Gaussian splat"].items] == ["Medium"]
    assert [item.label for item in by_title["3D tiles"].items] == ["Streaming viewer"]
    assert {item.label for item in by_title["Custom saves"].items} == {
        f"{tmp_path.name}_mesh_edited.ply",
        "colony_crop.glb",
    }


def test_model_catalog_adds_sparse_points_and_cameras(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    model = layout.sparse / "0"
    model.mkdir(parents=True)
    for name in ("cameras.bin", "images.bin", "points3D.bin"):
        (model / name).write_bytes(b"\0" * 8)

    sections = discover_model_catalog(layout)

    assert sections[0].title == "Sparse cloud"
    assert sections[0].items[0].label == "Points + cameras"
    assert sections[0].items[0].path == model

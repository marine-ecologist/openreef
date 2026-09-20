import json
import struct
from pathlib import Path

import numpy as np

from openreef.io.markertags import (
    Detection,
    RayObservation,
    estimate_metric_scale,
    format_viewer_diagnostics,
    has_metric_scale,
    read_viewer_metadata,
    run_markertag_workflow,
    scale_colmap_model,
    triangulate_robust,
)
from openreef.pipeline.stages import DatasetLayout, markertag_status, sparse_model_identity


def _write_minimal_model(folder: Path) -> None:
    folder.mkdir(parents=True)
    (folder / "cameras.bin").write_bytes(
        struct.pack("<QiiQQ4d", 1, 1, 2, 1000, 800, 800.0, 500.0, 400.0, 0.01)
    )
    with (folder / "images.bin").open("wb") as stream:
        stream.write(struct.pack("<Q", 1))
        stream.write(struct.pack("<i7di", 7, 1.0, 0.0, 0.0, 0.0, 2.0, 3.0, 4.0, 1))
        stream.write(b"frame.jpg\0")
        stream.write(struct.pack("<Q", 0))
    with (folder / "points3D.bin").open("wb") as stream:
        stream.write(struct.pack("<Q", 1))
        stream.write(struct.pack("<Q3d3Bd", 11, 1.0, 2.0, 3.0, 10, 20, 30, 1.25))
        stream.write(struct.pack("<Q", 0))


def test_robust_scale_uses_known_tag_edges() -> None:
    corners = [
        np.asarray((0.0, 0.0, 0.0)),
        np.asarray((10.0, 0.0, 0.0)),
        np.asarray((10.0, 10.0, 0.0)),
        np.asarray((0.0, 10.0, 0.0)),
    ]

    result = estimate_metric_scale({7: {"corners": corners}}, 0.050)

    assert result["status"] == "scaled"
    assert result["scale_factor"] == 0.005
    assert result["residual_rms_m"] == 0.0
    assert result["inlier_measurements"] == 4


def test_scale_colmap_model_scales_world_geometry_but_not_reprojection_error(
    tmp_path: Path,
) -> None:
    source = tmp_path / "raw"
    destination = tmp_path / "metric" / "sparse"
    _write_minimal_model(source)

    scale_colmap_model(source, destination, 0.1)

    with (destination / "images.bin").open("rb") as stream:
        stream.read(8)
        image = struct.unpack("<i7di", stream.read(struct.calcsize("<i7di")))
    assert image[5:8] == (0.2, 0.30000000000000004, 0.4)

    with (destination / "points3D.bin").open("rb") as stream:
        stream.read(8)
        point = struct.unpack("<Q3d3Bd", stream.read(struct.calcsize("<Q3d3Bd")))
    assert point[1:4] == (0.1, 0.2, 0.30000000000000004)
    assert point[-1] == 1.25
    assert (destination / "points3D.ply").is_file()


def test_processing_model_prefers_current_metric_copy(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    source = layout.sparse / "0"
    _write_minimal_model(source)
    _write_minimal_model(layout.metric_sparse)
    layout.models.mkdir(parents=True)
    layout.markertags_metadata.write_text(
        json.dumps(
            {
                "status": "scaled",
                "scaled": True,
                "source_model": sparse_model_identity(source),
            }
        ),
        encoding="utf-8",
    )

    assert layout.processing_sparse_model() == layout.metric_sparse


def test_triangulation_uses_registered_multi_view_geometry() -> None:
    point = np.asarray((0.2, -0.1, 4.0))
    detection = Detection(7, "frame.jpg", np.zeros((4, 2)), np.zeros(2))
    projections = (
        np.column_stack((np.eye(3), np.zeros(3))),
        np.column_stack((np.eye(3), np.asarray((-1.0, 0.0, 0.0)))),
        np.column_stack((np.eye(3), np.asarray((0.0, -1.0, 0.0)))),
    )
    centers = (np.zeros(3), np.asarray((1.0, 0.0, 0.0)), np.asarray((0.0, 1.0, 0.0)))
    observations = []
    for projection, center in zip(projections, centers, strict=True):
        camera_point = projection[:, :3] @ point + projection[:, 3]
        normalized = camera_point[:2] / camera_point[2]
        observations.append(
            RayObservation(
                detection=detection,
                point=normalized * 800,
                normalized=normalized,
                projection=projection,
                camera_center=center,
                focal_pixels=800.0,
            )
        )

    result = triangulate_robust(observations, 2.0)

    assert result is not None
    reconstructed, used, residual = result
    assert np.allclose(reconstructed, point)
    assert len(used) == 3
    assert residual < 1.0e-9


def test_workflow_persists_detections_and_builds_metric_model(
    tmp_path: Path, monkeypatch
) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "a.jpg").touch()
    (images / "b.jpg").touch()
    source = tmp_path / "colmap" / "sparse" / "0"
    source.mkdir(parents=True)
    (source / "cameras.bin").write_bytes(
        struct.pack("<QiiQQ3d", 1, 1, 0, 1000, 800, 800.0, 500.0, 400.0)
    )
    with (source / "images.bin").open("wb") as stream:
        stream.write(struct.pack("<Q", 2))
        for image_id, name, tx in ((1, "a.jpg", 0.0), (2, "b.jpg", -1.0)):
            stream.write(
                struct.pack(
                    "<i7di", image_id, 1.0, 0.0, 0.0, 0.0, tx, 0.0, 0.0, 1
                )
            )
            stream.write(name.encode() + b"\0")
            stream.write(struct.pack("<Q", 0))
    (source / "points3D.bin").write_bytes(struct.pack("<Q", 0))

    square = np.asarray(
        ((0.0, 0.0, 4.0), (10.0, 0.0, 4.0), (10.0, 10.0, 4.0), (0.0, 10.0, 4.0))
    )
    fake_detections = []
    for name, translation in (("a.jpg", np.zeros(3)), ("b.jpg", np.asarray((-1.0, 0, 0)))):
        camera_points = square + translation
        pixels = camera_points[:, :2] / camera_points[:, 2, None] * 800.0 + (500.0, 400.0)
        fake_detections.append(Detection(7, name, pixels, pixels.mean(axis=0)))
    monkeypatch.setattr(
        "openreef.io.markertags.detect_markertags",
        lambda image_folder, family: fake_detections,
    )
    metric = tmp_path / "colmap" / "metric" / "sparse"
    metadata = tmp_path / "models" / "reef_markertags.json"

    payload = run_markertag_workflow(images, source, metric, metadata)

    assert payload["status"] == "scaled"
    assert np.isclose(payload["scale_factor"], 0.005)
    assert payload["unique_tags"] == 1
    assert payload["registered_observations"] == 2
    assert payload["detections"][0]["reconstructed_3d_corners"] is not None
    assert payload["detections"][0]["coordinate_units"] == "metres"
    assert payload["markertags"]["detected"] is True
    assert payload["markertags"]["family"] == "tag36h11"
    assert payload["markertags"]["tag_size_m"] == 0.05
    assert payload["markertags"]["ids"] == [7]
    assert payload["markertags"]["detections"] == 2
    assert payload["markertags"]["tags_used_for_scale"] == 1
    assert payload["markertags"]["corner_reprojection_rmse_px"] is not None
    assert payload["scale"]["applied"] is True
    assert payload["scale"]["source"] == "markertag"
    assert payload["scale"]["units"] == "m"
    assert metric.is_dir()
    assert json.loads(metadata.read_text(encoding="utf-8"))["tag_ids"] == [7]


def test_viewer_metadata_normalizes_legacy_payload(tmp_path: Path) -> None:
    path = tmp_path / "markers.json"
    path.write_text(
        json.dumps(
            {
                "scaled": True,
                "family": "tag36h11",
                "tag_edge_m": 0.05,
                "unique_tags": 2,
                "tag_ids": [3, 9],
                "observations": 11,
                "inlier_tags": 2,
                "scale_factor": 0.0012,
            }
        ),
        encoding="utf-8",
    )

    payload = read_viewer_metadata(path)

    assert has_metric_scale(payload)
    diagnostics = format_viewer_diagnostics(payload)
    assert "Tag IDs: 3, 9" in diagnostics
    assert "Physical tag size: 50 mm" in diagnostics
    assert "Scale factor: 0.0012" in diagnostics
    assert "Robust scale SD (MAD):" in diagnostics


def test_process_status_reports_robust_scale_sd_across_tags(tmp_path: Path) -> None:
    layout = DatasetLayout(tmp_path)
    layout.models.mkdir(parents=True)
    layout.markertags_metadata.write_text(
        json.dumps(
            {
                "scaled": True,
                "unique_tags": 3,
                "scale_factor": 0.0049,
                "residual_rms_m": 0.0007,
                "markertags": {"tags_used_for_scale": 3},
                "scale": {"scale_residual_pct": 1.234},
            }
        ),
        encoding="utf-8",
    )

    status = markertag_status(layout)

    assert "MarkerTags detected: 3" in status
    assert "Robust scale SD: 1.23% across 3 tags" in status
    assert "Edge residual: 0.70 mm" in status


def test_scale_quality_uses_robust_dispersion_across_tags() -> None:
    reconstructed = {
        1: {"corners": _square(10.0)},
        2: {"corners": _square(10.2)},
        3: {"corners": _square(9.8)},
    }

    result = estimate_metric_scale(reconstructed, 0.05)

    estimates = np.asarray(
        [item["scale_factor"] for item in result["tag_scale_estimates"]]
    )
    expected = 100 * 1.4826 * np.median(np.abs(estimates - np.median(estimates))) / np.median(
        estimates
    )
    assert np.isclose(result["scale_residual_pct"], expected)
    assert result["inlier_tags"] == 3


def _square(edge: float) -> list[np.ndarray]:
    return [
        np.asarray((0.0, 0.0, 0.0)),
        np.asarray((edge, 0.0, 0.0)),
        np.asarray((edge, edge, 0.0)),
        np.asarray((0.0, edge, 0.0)),
    ]

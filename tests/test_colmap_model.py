import json
import struct
from pathlib import Path

import numpy as np

from openreef.core.model import ModelDocument, ModelPart
from openreef.io.colmap_model import (
    SparseROI,
    filter_text_model_to_roi,
    lasso_roi,
    read_camera_poses,
)


def test_reads_colmap_camera_pose(tmp_path: Path) -> None:
    images = tmp_path / "images.bin"
    with images.open("wb") as stream:
        stream.write(struct.pack("<Q", 1))
        stream.write(struct.pack("<i7di", 7, 1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4))
        stream.write(b"reef_0001.jpg\0")
        stream.write(struct.pack("<Q", 0))

    poses = read_camera_poses(images)

    assert len(poses) == 1
    assert poses[0].image_id == 7
    assert poses[0].camera_id == 4
    assert poses[0].name == "reef_0001.jpg"
    assert poses[0].center == (-1.0, -2.0, -3.0)
    assert poses[0].forward == (0.0, 0.0, 1.0)


def test_filters_colmap_text_points_to_roi(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "roi"
    source.mkdir()
    (source / "cameras.txt").write_text("# cameras\n1 PINHOLE 100 100 50 50 50 50\n")
    (source / "points3D.txt").write_text(
        "# points\n1 0 0 0 255 0 0 0.1 7 0\n2 20 20 20 0 255 0 0.2 7 1\n"
    )
    (source / "images.txt").write_text("# images\n7 1 0 0 0 0 0 0 1 reef.jpg\n10 10 1 20 20 2\n")
    roi = SparseROI.from_selection((-1, 1, -1, 1, -1, 1), 1, 2)

    retained = filter_text_model_to_roi(source, destination, roi)

    assert retained == 1
    points = (destination / "points3D.txt").read_text()
    assert "1 0 0 0" in points
    assert "2 20 20 20" not in points
    assert (destination / "images.txt").read_text().endswith("10 10 1 20 20 -1\n")


def test_sparse_roi_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "reef_roi.json"
    roi = SparseROI.from_selection((0, 1, 2, 3, 4, 5), 20, 50, "2")

    roi.save(path)
    loaded = SparseROI.load(path)

    assert loaded.bounds == roi.bounds
    assert loaded.selected_points == 20
    assert loaded.sparse_model == "2"
    assert json.loads(path.read_text())["coordinate_system"] == "COLMAP world coordinates"


def test_lasso_roi_uses_selected_sparse_points() -> None:
    from pyvista import PolyData
    from vtkmodules.vtkRenderingCore import vtkCamera

    points = PolyData(np.asarray(((0.0, 0.0, 0.0), (5.0, 0.0, 0.0))))
    document = ModelDocument(Path("points3D.ply"), (ModelPart("Sparse", points, "point-cloud"),))
    camera = vtkCamera()
    camera.SetPosition(0.0, 0.0, 10.0)
    camera.SetFocalPoint(0.0, 0.0, 0.0)
    camera.SetViewUp(0.0, 1.0, 0.0)
    camera.SetClippingRange(0.1, 100.0)

    roi = lasso_roi(
        document,
        camera,
        (200, 200),
        [(80.0, 80.0), (120.0, 80.0), (120.0, 120.0), (80.0, 120.0)],
    )

    assert roi.selected_points == 1
    assert roi.total_points == 2
    assert roi.bounds[0] < 0.0 < roi.bounds[1]

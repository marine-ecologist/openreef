from pathlib import Path
from typing import Any

import numpy as np
import pytest

from openreef.core.mesh_edit import (
    LassoOperation,
    apply_lasso_operation,
    create_low_res_document,
    project_to_viewport,
    save_document,
    signed_lasso_distance,
    trim_document,
)
from openreef.core.model import ModelDocument, ModelPart


def camera() -> Any:
    from vtkmodules.vtkRenderingCore import vtkCamera

    result = vtkCamera()
    result.SetPosition(0.0, 0.0, 10.0)
    result.SetFocalPoint(0.0, 0.0, 0.0)
    result.SetViewUp(0.0, 1.0, 0.0)
    result.SetClippingRange(0.1, 100.0)
    return result


def plane_mesh():
    from pyvista import Plane

    return Plane(i_size=4.0, j_size=4.0, i_resolution=20, j_resolution=20).triangulate()


def test_project_to_viewport_places_focal_point_at_center() -> None:
    projected, valid = project_to_viewport(np.array([[0.0, 0.0, 0.0]]), camera(), (200, 100))
    assert valid.tolist() == [True]
    assert projected[0] == pytest.approx((100.0, 50.0))


def test_signed_lasso_distance_marks_inside_negative() -> None:
    polygon = np.array(((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)))
    distances = signed_lasso_distance(np.array(((5.0, 5.0), (20.0, 5.0))), polygon)
    assert distances[0] < 0.0
    assert distances[1] > 0.0


def test_keep_inside_lasso_trims_mesh_without_changing_original() -> None:
    mesh = plane_mesh()
    document = ModelDocument(Path("reef.ply"), (ModelPart("Reef", mesh, "mesh"),))
    lasso = [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)]

    result = trim_document(document, camera(), (200, 200), lasso, keep_inside=True)

    assert result.document.stats.cells < document.stats.cells
    assert result.document.stats.cells > 0
    assert document.stats.cells == 800


def test_delete_inside_lasso_retains_surrounding_mesh() -> None:
    mesh = plane_mesh()
    document = ModelDocument(Path("reef.ply"), (ModelPart("Reef", mesh, "mesh"),))
    lasso = [(80.0, 80.0), (120.0, 80.0), (120.0, 120.0), (80.0, 120.0)]

    result = trim_document(document, camera(), (200, 200), lasso, keep_inside=False)

    assert 0 < result.document.stats.cells < document.stats.cells


def test_save_document_writes_ply(tmp_path: Path) -> None:
    mesh = plane_mesh()
    document = ModelDocument(Path("reef.ply"), (ModelPart("Reef", mesh, "mesh"),))

    destination = save_document(document, tmp_path / "reef_trimmed.ply")

    assert destination.is_file()
    assert destination.stat().st_size > 0


def test_low_res_proxy_edits_replay_on_full_resolution() -> None:
    from pyvista import Plane

    mesh = Plane(i_size=4.0, j_size=4.0, i_resolution=50, j_resolution=50).triangulate()
    document = ModelDocument(Path("reef.ply"), (ModelPart("Reef", mesh, "mesh"),))
    proxy = create_low_res_document(document, target_cells=1_000)
    operation = LassoOperation.capture(
        camera(),
        (200, 200),
        [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)],
        keep_inside=True,
    )

    proxy_result = apply_lasso_operation(proxy, operation).document
    full_result = apply_lasso_operation(document, operation).document

    assert proxy.stats.cells <= 1_000
    assert proxy_result.stats.cells < proxy.stats.cells
    assert full_result.stats.cells < document.stats.cells
    assert full_result.stats.cells > proxy_result.stats.cells

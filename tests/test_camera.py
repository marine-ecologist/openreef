from pathlib import Path

import pytest

from openreef.core.camera import (
    CameraOrientation,
    CameraView,
    orthomosaic_image_size,
    pan_camera,
)


class FakeCamera:
    position = (0.0, 0.0, 10.0)
    focal_point = (0.0, 0.0, 0.0)
    up = (0.0, 1.0, 0.0)
    parallel_projection = True
    parallel_scale = 5.0
    view_angle = 30.0


class FakePlotter:
    def __init__(self) -> None:
        self.camera = FakeCamera()
        self.camera.position = (10.0, 0.0, 0.0)
        self.camera.focal_point = (0.0, 0.0, 0.0)
        self.camera.up = (0.0, 0.0, 1.0)

    @property
    def camera_position(self):
        return self.camera.position, self.camera.focal_point, self.camera.up


def sample_view() -> CameraView:
    return CameraView(
        position=(1.0, 2.0, 3.0),
        focal_point=(0.0, 0.0, 0.0),
        view_up=(0.0, 0.0, 1.0),
        parallel_projection=True,
        parallel_scale=4.5,
        view_angle=30.0,
        clipping_range=(0.1, 100.0),
    )


def test_viewpoint_json_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "view.json"
    original = sample_view()
    original.save(path)
    assert CameraView.load(path) == original


def test_viewpoint_rejects_wrong_vector_length() -> None:
    data = sample_view().to_dict()
    data["position"] = [1, 2]
    with pytest.raises(ValueError, match="position"):
        CameraView.from_mapping(data)


def test_viewpoint_rejects_unknown_schema() -> None:
    data = sample_view().to_dict()
    data["schema_version"] = 99
    with pytest.raises(ValueError, match="schema"):
        CameraView.from_mapping(data)


def test_viewpoint_rejects_non_boolean_projection() -> None:
    data = sample_view().to_dict()
    data["parallel_projection"] = "false"
    with pytest.raises(ValueError, match="parallel_projection"):
        CameraView.from_mapping(data)


def test_camera_orientation_json_round_trip() -> None:
    orientation = CameraOrientation(direction=(-1.0, 0.0, 0.0), view_up=(0.0, 0.0, 1.0))

    assert CameraOrientation.from_json(orientation.to_json()) == orientation


def test_camera_orientation_reuses_direction_without_reusing_model_position() -> None:
    plotter = FakePlotter()
    orientation = CameraOrientation.capture(plotter)
    plotter.camera.position = (4.0, 8.0, 3.0)
    plotter.camera.focal_point = (4.0, 5.0, 3.0)
    original_distance = 3.0

    orientation.apply(plotter)

    assert plotter.camera.focal_point == (4.0, 5.0, 3.0)
    assert plotter.camera.position == pytest.approx((4.0 + original_distance, 5.0, 3.0))
    assert plotter.camera.up == (0.0, 0.0, 1.0)


def test_screen_pan_moves_camera_and_focal_point_together() -> None:
    camera = FakeCamera()
    pan_camera(camera, dx=20.0, dy=10.0, viewport_height=100)

    assert camera.position == pytest.approx((-2.0, 1.0, 10.0))
    assert camera.focal_point == pytest.approx((-2.0, 1.0, 0.0))
    assert tuple(camera.position[i] - camera.focal_point[i] for i in range(3)) == pytest.approx(
        (0.0, 0.0, 10.0)
    )


@pytest.mark.parametrize(
    ("viewport", "expected"),
    (((1600, 900), (4096, 2304)), ((900, 1600), (2304, 4096)), ((1, 1), (4096, 4096))),
)
def test_orthomosaic_image_size_preserves_viewport_aspect(
    viewport: tuple[int, int], expected: tuple[int, int]
) -> None:
    assert orthomosaic_image_size(4096, *viewport) == expected


def test_orthomosaic_image_size_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="positive"):
        orthomosaic_image_size(4096, 0, 900)

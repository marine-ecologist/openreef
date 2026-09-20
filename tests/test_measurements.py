import math

import numpy as np

from openreef.core.measurements import length_metres, measure_surface_polygon
from openreef.ui.measurements import vtk_display_coordinates


def test_length_is_straight_line_in_metric_coordinates() -> None:
    assert length_metres(np.asarray((0.0, 0.0, 0.0)), np.asarray((1.0, 2.0, 2.0))) == 3.0


def test_retina_click_coordinates_are_scaled_for_vtk_surface_picking() -> None:
    assert vtk_display_coordinates(
        400.0,
        300.0,
        widget_height=800,
        device_pixel_ratio=2.0,
    ) == (800, 998)


def test_standard_density_click_coordinates_only_flip_y_for_vtk() -> None:
    assert vtk_display_coordinates(
        400.0,
        300.0,
        widget_height=800,
        device_pixel_ratio=1.0,
    ) == (400, 499)


def test_flat_surface_matches_planar_area() -> None:
    polygon = np.asarray(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0))
    )
    triangles = np.asarray(
        (
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)),
            ((0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)),
        )
    )

    result = measure_surface_polygon(polygon, triangles)

    assert math.isclose(result.planar_area_m2, 1.0)
    assert math.isclose(result.surface_area_m2, 1.0)
    assert math.isclose(result.perimeter_m, 4.0)
    assert math.isclose(result.surface_planar_ratio, 1.0)
    assert result.contributing_triangles == 2


def test_surface_area_follows_interior_reef_relief() -> None:
    polygon = np.asarray(
        (
            (-1.0, -1.0, 0.0),
            (1.0, -1.0, 0.0),
            (1.0, 1.0, 0.0),
            (-1.0, 1.0, 0.0),
        )
    )
    center = (0.0, 0.0, 1.0)
    triangles = np.asarray(
        (
            (polygon[0], polygon[1], center),
            (polygon[1], polygon[2], center),
            (polygon[2], polygon[3], center),
            (polygon[3], polygon[0], center),
        )
    )

    result = measure_surface_polygon(polygon, triangles)

    assert math.isclose(result.planar_area_m2, 4.0)
    assert math.isclose(result.surface_area_m2, 4.0 * math.sqrt(2.0))
    assert math.isclose(result.surface_planar_ratio, math.sqrt(2.0))


def test_concave_footprint_clips_mesh_without_filling_notch() -> None:
    polygon = np.asarray(
        (
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 2.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 2.0, 0.0),
        )
    )
    triangles = np.asarray(
        (
            ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0)),
            ((0.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0)),
        )
    )

    result = measure_surface_polygon(polygon, triangles)

    assert math.isclose(result.planar_area_m2, 3.0)
    assert math.isclose(result.surface_area_m2, 3.0)

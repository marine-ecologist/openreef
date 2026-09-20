"""Geometry for metric measurements on reconstructed reef meshes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SurfacePolygonMeasurement:
    """Metrics for one user-drawn polygon in metric model coordinates."""

    planar_area_m2: float
    surface_area_m2: float
    perimeter_m: float
    surface_planar_ratio: float
    contributing_triangles: int


def length_metres(first: np.ndarray, second: np.ndarray) -> float:
    """Return straight-line distance between two metric 3D points."""

    return float(np.linalg.norm(np.asarray(second, dtype=float) - np.asarray(first, dtype=float)))


def measure_surface_polygon(
    polygon: np.ndarray,
    mesh_triangles: np.ndarray,
) -> SurfacePolygonMeasurement:
    """Measure a polygon footprint and the clipped 3D mesh beneath it.

    The clicked boundary is projected to its best-fit plane.  The (possibly
    concave) footprint is ear-clipped into triangles.  Every overlapping mesh
    triangle is then clipped in that plane and the corresponding clipped points
    are mapped back to the original 3D triangle with barycentric coordinates.
    Summing those true 3D fragments gives surface area without flattening the
    reef surface.
    """

    points = np.asarray(polygon, dtype=float)
    triangles = np.asarray(mesh_triangles, dtype=float)
    if points.ndim != 2 or points.shape[0] < 3 or points.shape[1] != 3:
        raise ValueError("A surface polygon needs at least three 3D points")
    if triangles.ndim != 3 or triangles.shape[1:] != (3, 3):
        raise ValueError("Mesh triangles must have shape (n, 3, 3)")
    if not np.isfinite(points).all() or not np.isfinite(triangles).all():
        raise ValueError("Measurement geometry contains non-finite coordinates")

    origin, axis_u, axis_v = _best_fit_plane(points)
    polygon_2d = _project(points, origin, axis_u, axis_v)
    signed_area = _signed_area(polygon_2d)
    if abs(signed_area) <= 1.0e-12:
        raise ValueError("The selected polygon has no measurable planar area")
    if signed_area < 0:
        points = points[::-1].copy()
        polygon_2d = polygon_2d[::-1].copy()
        signed_area = -signed_area

    footprint = _ear_clip(polygon_2d)
    projected_mesh = _project(triangles.reshape(-1, 3), origin, axis_u, axis_v).reshape(-1, 3, 2)
    polygon_min = polygon_2d.min(axis=0)
    polygon_max = polygon_2d.max(axis=0)
    triangle_min = projected_mesh.min(axis=1)
    triangle_max = projected_mesh.max(axis=1)
    candidates = np.flatnonzero(
        (triangle_max[:, 0] >= polygon_min[0])
        & (triangle_min[:, 0] <= polygon_max[0])
        & (triangle_max[:, 1] >= polygon_min[1])
        & (triangle_min[:, 1] <= polygon_max[1])
    )

    surface_area = 0.0
    contributing: set[int] = set()
    for mesh_index in candidates:
        triangle_2d = projected_mesh[mesh_index]
        projected_area = _cross_2d(
            triangle_2d[1] - triangle_2d[0], triangle_2d[2] - triangle_2d[0]
        )
        if abs(projected_area) <= 1.0e-14:
            continue
        triangle_3d = triangles[mesh_index]
        for footprint_indices in footprint:
            clip_triangle = polygon_2d[np.asarray(footprint_indices)]
            clipped = _clip_convex_polygon(triangle_2d, clip_triangle)
            if len(clipped) < 3:
                continue
            clipped_3d = np.asarray(
                [_barycentric_point(point, triangle_2d, triangle_3d) for point in clipped]
            )
            fragment_area = _polygon_area_3d(clipped_3d)
            if fragment_area > 1.0e-15:
                surface_area += fragment_area
                contributing.add(int(mesh_index))

    perimeter = sum(
        length_metres(points[index], points[(index + 1) % len(points)])
        for index in range(len(points))
    )
    planar_area = float(signed_area)
    return SurfacePolygonMeasurement(
        planar_area_m2=planar_area,
        surface_area_m2=float(surface_area),
        perimeter_m=float(perimeter),
        surface_planar_ratio=float(surface_area / planar_area),
        contributing_triangles=len(contributing),
    )


def _best_fit_plane(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    origin = points.mean(axis=0)
    _, singular_values, vh = np.linalg.svd(points - origin, full_matrices=False)
    if len(singular_values) < 2 or singular_values[1] <= 1.0e-12:
        raise ValueError("The selected points are collinear")
    axis_u = vh[0]
    normal = vh[-1]
    axis_v = np.cross(normal, axis_u)
    axis_v /= max(float(np.linalg.norm(axis_v)), 1.0e-15)
    return origin, axis_u, axis_v


def _project(
    points: np.ndarray,
    origin: np.ndarray,
    axis_u: np.ndarray,
    axis_v: np.ndarray,
) -> np.ndarray:
    relative = points - origin
    return np.column_stack((relative @ axis_u, relative @ axis_v))


def _signed_area(points: np.ndarray) -> float:
    return 0.5 * float(
        np.sum(points[:, 0] * np.roll(points[:, 1], -1) - points[:, 1] * np.roll(points[:, 0], -1))
    )


def _ear_clip(points: np.ndarray) -> list[tuple[int, int, int]]:
    """Triangulate a simple counter-clockwise polygon."""

    remaining = list(range(len(points)))
    result: list[tuple[int, int, int]] = []
    guard = 0
    while len(remaining) > 3:
        clipped = False
        for position, current in enumerate(remaining):
            previous = remaining[position - 1]
            following = remaining[(position + 1) % len(remaining)]
            a, b, c = points[[previous, current, following]]
            if _cross_2d(b - a, c - b) <= 1.0e-12:
                continue
            if any(
                _point_in_triangle(points[index], a, b, c)
                for index in remaining
                if index not in {previous, current, following}
            ):
                continue
            result.append((previous, current, following))
            del remaining[position]
            clipped = True
            break
        guard += 1
        if not clipped or guard > len(points) * len(points):
            raise ValueError("The polygon boundary crosses itself or cannot be triangulated")
    result.append(tuple(remaining))
    return result


def _point_in_triangle(point: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> bool:
    tolerance = 1.0e-12
    first = _cross_2d(b - a, point - a)
    second = _cross_2d(c - b, point - b)
    third = _cross_2d(a - c, point - c)
    return first >= -tolerance and second >= -tolerance and third >= -tolerance


def _clip_convex_polygon(subject: np.ndarray, clip: np.ndarray) -> list[np.ndarray]:
    """Sutherland-Hodgman clip, with a counter-clockwise convex clip polygon."""

    output = [np.asarray(point, dtype=float) for point in subject]
    for index in range(len(clip)):
        edge_start = clip[index]
        edge_end = clip[(index + 1) % len(clip)]
        input_points = output
        output = []
        if not input_points:
            break
        previous = input_points[-1]
        previous_inside = _inside(previous, edge_start, edge_end)
        for current in input_points:
            current_inside = _inside(current, edge_start, edge_end)
            if current_inside != previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            if current_inside:
                output.append(current)
            previous = current
            previous_inside = current_inside
    return _deduplicate_polygon(output)


def _inside(point: np.ndarray, edge_start: np.ndarray, edge_end: np.ndarray) -> bool:
    return _cross_2d(edge_end - edge_start, point - edge_start) >= -1.0e-12


def _line_intersection(
    segment_start: np.ndarray,
    segment_end: np.ndarray,
    edge_start: np.ndarray,
    edge_end: np.ndarray,
) -> np.ndarray:
    segment = segment_end - segment_start
    edge = edge_end - edge_start
    denominator = _cross_2d(segment, edge)
    if abs(denominator) <= 1.0e-15:
        return segment_end.copy()
    amount = _cross_2d(edge_start - segment_start, edge) / denominator
    return segment_start + amount * segment


def _deduplicate_polygon(points: list[np.ndarray]) -> list[np.ndarray]:
    result: list[np.ndarray] = []
    for point in points:
        if not result or float(np.linalg.norm(point - result[-1])) > 1.0e-10:
            result.append(point)
    if len(result) > 1 and float(np.linalg.norm(result[0] - result[-1])) <= 1.0e-10:
        result.pop()
    return result


def _barycentric_point(
    point: np.ndarray, triangle_2d: np.ndarray, triangle_3d: np.ndarray
) -> np.ndarray:
    a, b, c = triangle_2d
    matrix = np.column_stack((b - a, c - a))
    weights = np.linalg.solve(matrix, point - a)
    return triangle_3d[0] + weights[0] * (triangle_3d[1] - triangle_3d[0]) + weights[1] * (
        triangle_3d[2] - triangle_3d[0]
    )


def _polygon_area_3d(points: np.ndarray) -> float:
    anchor = points[0]
    return sum(
        0.5
        * float(
            np.linalg.norm(
                np.cross(points[index] - anchor, points[index + 1] - anchor)
            )
        )
        for index in range(1, len(points) - 1)
    )


def _cross_2d(first: np.ndarray, second: np.ndarray) -> float:
    return float(first[0] * second[1] - first[1] * second[0])

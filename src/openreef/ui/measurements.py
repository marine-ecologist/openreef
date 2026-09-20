"""Persistent metric measurement annotations for the native 3D viewer."""

from __future__ import annotations

from typing import Any

import numpy as np

from openreef.core.measurements import length_metres, measure_surface_polygon
from openreef.core.model import ModelDocument

MEASUREMENT_COLOR = "#f2f2f7"
MEASUREMENT_POINT_COLOR = "#d1d1d6"


class MeasurementController:
    """Pick mesh surfaces and own persistent VTK measurement actors."""

    def __init__(self, plotter: Any) -> None:
        self.plotter = plotter
        self.document: ModelDocument | None = None
        self.mesh_actors: tuple[Any, ...] = ()
        self.mode: str | None = None
        self.points: list[np.ndarray] = []
        self.display_points: list[tuple[float, float]] = []
        self._mesh_triangles: np.ndarray | None = None
        self._actor_names: list[str] = []
        self._preview_names = ("measurement-preview-line", "measurement-preview-points")
        self._counter = 0

    def configure(
        self,
        document: ModelDocument | None,
        mesh_actors: tuple[Any, ...],
        *,
        available: bool,
        scaled_status: str = "MarkerTags detected · scaled",
    ) -> None:
        """Reset for a newly loaded model and show tools only for metric meshes."""

        self.clear_all()
        self.document = document
        self.mesh_actors = mesh_actors
        self._mesh_triangles = None
        self.plotter.set_measurement_available(
            available and document is not None and bool(mesh_actors), scaled_status
        )

    def begin(self, mode: str) -> None:
        if mode not in {"length", "polygon"}:
            return
        self.cancel()
        self.mode = mode
        self.plotter.set_measurement_mode(mode)
        self.plotter.set_measurement_hint(
            "Click two mesh points · Esc cancels"
            if mode == "length"
            else "Click 3+ points · first point, double-click, or Enter closes"
        )

    def add_display_point(self, x: float, y: float) -> None:
        if self.mode is None:
            return
        point = self._pick_mesh_point(x, y)
        if point is None:
            self.plotter.set_measurement_hint("No mesh surface at that point")
            return
        if (
            self.mode == "polygon"
            and len(self.points) >= 3
            and self.display_points
            and _display_distance((x, y), self.display_points[0]) <= 12.0
        ):
            self.close_polygon()
            return
        self.points.append(point)
        self.display_points.append((x, y))
        self._draw_preview()
        if self.mode == "length" and len(self.points) == 2:
            self._complete_length()
        elif self.mode == "polygon":
            self.plotter.set_measurement_hint(
                f"{len(self.points)} vertices · Enter closes · Backspace removes last"
            )

    def close_polygon(self) -> None:
        if self.mode != "polygon" or len(self.points) < 3:
            return
        polygon = np.asarray(self.points, dtype=float)
        try:
            result = measure_surface_polygon(polygon, self._triangles())
        except (TypeError, ValueError, RuntimeError) as exc:
            self.plotter.set_measurement_hint(str(exc))
            return

        self._remove_preview()
        self._counter += 1
        prefix = f"measurement-{self._counter}"
        closed = np.vstack((polygon, polygon[0]))
        self._add_segment_lines(closed, f"{prefix}-boundary")
        self._add_points(polygon, f"{prefix}-points")
        center = polygon.mean(axis=0)
        label = (
            f"Surface {result.surface_area_m2:.3f} m²\n"
            f"Planar {result.planar_area_m2:.3f} m² · Perimeter {result.perimeter_m:.3f} m\n"
            f"Surface / planar {result.surface_planar_ratio:.3f}"
        )
        self._add_label(center, label, f"{prefix}-label")
        self._finish_current("Surface polygon added")

    def remove_last_vertex(self) -> None:
        if self.mode != "polygon" or not self.points:
            return
        self.points.pop()
        self.display_points.pop()
        self._draw_preview()
        self.plotter.set_measurement_hint(f"{len(self.points)} vertices")

    def cancel(self) -> None:
        self._remove_preview()
        self.points.clear()
        self.display_points.clear()
        self.mode = None
        self.plotter.set_measurement_mode(None)
        self.plotter.set_measurement_hint("")

    def clear_all(self) -> None:
        self.cancel()
        for name in self._actor_names:
            self._remove_actor(name)
        self._actor_names.clear()
        self.plotter.render()

    def _complete_length(self) -> None:
        first, second = self.points
        distance = length_metres(first, second)
        self._remove_preview()
        self._counter += 1
        prefix = f"measurement-{self._counter}"
        self._add_segment_lines(np.asarray((first, second)), f"{prefix}-line")
        self._add_points(np.asarray((first, second)), f"{prefix}-points")
        self._add_label((first + second) / 2.0, f"{distance:.3f} m", f"{prefix}-label")
        self._finish_current("Length added")

    def _finish_current(self, message: str) -> None:
        self.points.clear()
        self.display_points.clear()
        self.mode = None
        self.plotter.set_measurement_mode(None)
        self.plotter.set_measurement_hint(message)
        self.plotter.render()

    def _pick_mesh_point(self, x: float, y: float) -> np.ndarray | None:
        from vtkmodules.vtkRenderingCore import vtkCellPicker

        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        if self.mesh_actors:
            picker.PickFromListOn()
            for actor in self.mesh_actors:
                picker.AddPickList(actor)
        display_x, display_y = vtk_display_coordinates(
            x,
            y,
            widget_height=self.plotter.height(),
            device_pixel_ratio=self.plotter.devicePixelRatioF(),
        )
        picked = picker.Pick(
            display_x,
            display_y,
            0.0,
            self.plotter.renderer,
        )
        if not picked or picker.GetCellId() < 0:
            return None
        return np.asarray(picker.GetPickPosition(), dtype=float)

    def _triangles(self) -> np.ndarray:
        if self._mesh_triangles is not None:
            return self._mesh_triangles
        if self.document is None:
            raise ValueError("No mesh is loaded")
        pieces: list[np.ndarray] = []
        for part in self.document.parts:
            if part.kind != "mesh":
                continue
            surface = part.dataset.extract_surface().triangulate()
            faces = np.asarray(surface.faces, dtype=np.int64).reshape(-1, 4)
            triangle_faces = faces[faces[:, 0] == 3, 1:4]
            if len(triangle_faces):
                pieces.append(np.asarray(surface.points, dtype=float)[triangle_faces])
        if not pieces:
            raise ValueError("The loaded model has no triangular surface")
        self._mesh_triangles = np.concatenate(pieces, axis=0)
        return self._mesh_triangles

    def _draw_preview(self) -> None:
        self._remove_preview()
        if self.points:
            self._add_points(
                np.asarray(self.points), self._preview_names[1], persistent=False
            )
        if len(self.points) >= 2:
            self._add_segment_lines(
                np.asarray(self.points), self._preview_names[0], persistent=False
            )
        self.plotter.render()

    def _remove_preview(self) -> None:
        for name in self._preview_names:
            self._remove_actor(name)

    def _add_segment_lines(
        self, points: np.ndarray, name: str, *, persistent: bool = True
    ) -> None:
        segments = np.asarray(
            [(points[index], points[index + 1]) for index in range(len(points) - 1)],
            dtype=float,
        ).reshape(-1, 3)
        if len(segments):
            self.plotter.add_lines(
                segments,
                color=MEASUREMENT_COLOR,
                width=3,
                name=name,
            )
            if persistent:
                self._actor_names.append(name)

    def _add_points(
        self, points: np.ndarray, name: str, *, persistent: bool = True
    ) -> None:
        self.plotter.add_points(
            points,
            color=MEASUREMENT_POINT_COLOR,
            point_size=11,
            render_points_as_spheres=True,
            name=name,
        )
        if persistent:
            self._actor_names.append(name)

    def _add_label(self, point: np.ndarray, text: str, name: str) -> None:
        self.plotter.add_point_labels(
            np.asarray([point]),
            [text],
            name=name,
            always_visible=True,
            show_points=False,
            font_size=13,
            text_color="#f2f2f7",
            shape_color="#17191b",
            shape_opacity=0.90,
            margin=6,
        )
        self._actor_names.append(name)

    def _remove_actor(self, name: str) -> None:
        try:
            self.plotter.remove_actor(name, reset_camera=False, render=False)
        except (KeyError, TypeError, ValueError):
            pass


def _display_distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return float(np.linalg.norm(np.asarray(first) - np.asarray(second)))


def vtk_display_coordinates(
    x: float,
    y: float,
    *,
    widget_height: int,
    device_pixel_ratio: float,
) -> tuple[int, int]:
    """Convert Qt logical pixels into VTK's bottom-left device-pixel coordinates."""

    scale = max(float(device_pixel_ratio), 1.0)
    return (
        round(float(x) * scale),
        round((max(1, int(widget_height)) - float(y) - 1.0) * scale),
    )

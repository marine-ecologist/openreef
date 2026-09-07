"""Rendering state and viewport operations."""

from __future__ import annotations

from typing import Any

from openreef.core.model import ModelDocument

DISPLAY_MODES = ("Solid", "Wireframe", "Solid + wireframe")


class SceneController:
    """Own model actors and map UI actions onto PyVista operations."""

    def __init__(self, plotter: Any) -> None:
        self.plotter = plotter
        self.document: ModelDocument | None = None
        self._actors: list[tuple[Any, str]] = []
        self._display_mode = "Wireframe"
        self._point_size = 5
        self.plotter.set_background("#132028", top="#071015")
        self.plotter.add_axes(line_width=2)

    def set_document(self, document: ModelDocument) -> None:
        self.plotter.clear()
        self.plotter.add_axes(line_width=2)
        self.document = document
        self._actors.clear()

        for part in document.parts:
            color_options: dict[str, object] = {}
            if part.vertex_color:
                color_options = {"scalars": part.vertex_color, "rgb": True}

            if part.kind == "point-cloud":
                actor = self.plotter.add_points(
                    part.dataset,
                    name=part.name,
                    color="#62c8cf" if not color_options else None,
                    point_size=self._point_size,
                    render_points_as_spheres=True,
                    **color_options,
                )
            else:
                actor = self.plotter.add_mesh(
                    part.dataset,
                    name=part.name,
                    color="#61b8c8" if not color_options else None,
                    smooth_shading=False,
                    **color_options,
                )
            self._actors.append((actor, part.kind))

        self.set_display_mode(self._display_mode)
        self.fit_to_view()

    def set_display_mode(self, mode: str) -> None:
        if mode not in DISPLAY_MODES:
            raise ValueError(f"Unknown display mode: {mode}")
        self._display_mode = mode
        for actor, kind in self._actors:
            if kind == "point-cloud":
                continue
            prop = actor.GetProperty()
            if mode == "Wireframe":
                prop.SetRepresentationToWireframe()
                prop.SetEdgeVisibility(False)
            else:
                prop.SetRepresentationToSurface()
                prop.SetEdgeVisibility(mode == "Solid + wireframe")
                if mode == "Solid + wireframe":
                    prop.SetEdgeColor(0.06, 0.09, 0.11)
        self.plotter.render()

    def set_point_size(self, size: int) -> None:
        self._point_size = size
        for actor, kind in self._actors:
            if kind == "point-cloud":
                actor.GetProperty().SetPointSize(size)
        self.plotter.render()

    def fit_to_view(self) -> None:
        if self.document:
            self.plotter.reset_camera()
            self.plotter.reset_camera_clipping_range()
            self.plotter.render()

    def set_parallel_projection(self, enabled: bool) -> None:
        if enabled:
            self.plotter.enable_parallel_projection()
        else:
            self.plotter.disable_parallel_projection()
        self.plotter.render()

    def set_standard_view(self, view: str) -> None:
        commands = {
            "Top": lambda: self.plotter.view_xy(),
            "Bottom": lambda: self.plotter.view_xy(negative=True),
            "Front": lambda: self.plotter.view_xz(),
            "Back": lambda: self.plotter.view_xz(negative=True),
            "Right": lambda: self.plotter.view_yz(),
            "Left": lambda: self.plotter.view_yz(negative=True),
        }
        try:
            commands[view]()
        except KeyError as exc:
            raise ValueError(f"Unknown standard view: {view}") from exc
        self.fit_to_view()

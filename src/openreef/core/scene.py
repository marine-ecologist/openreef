"""Rendering state and viewport operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openreef.core.model import ModelDocument

DISPLAY_MODES = ("Solid", "Wireframe", "Solid + wireframe")
SPLAT_DISPLAY_MODE = "Gaussian splat"
SPLAT_RGB = "OpenReef splat RGB"
SPLAT_SCALE = "OpenReef splat scale"
SPLAT_OPACITY = "OpenReef splat opacity"
SPLAT_SCALE_FACTOR = 0.3
_GAUSSIAN_ARRAYS = {
    "f_dc_0",
    "f_dc_1",
    "f_dc_2",
    "opacity",
    "scale_0",
    "scale_1",
    "scale_2",
    "rot_0",
    "rot_1",
    "rot_2",
    "rot_3",
}


def _actor_identity(actor: Any) -> object:
    """Return a stable VTK identity even when Python wrapper objects are recreated."""
    if hasattr(actor, "GetAddressAsString"):
        return actor.GetAddressAsString("")
    return id(actor)


def is_gaussian_splat(document: ModelDocument) -> bool:
    """Return whether a document carries the standard 3D Gaussian attributes."""
    return any(
        _GAUSSIAN_ARRAYS.issubset(set(getattr(part.dataset, "point_data", {}).keys()))
        for part in document.parts
    )


class SceneController:
    """Own model actors and map UI actions onto PyVista operations."""

    def __init__(self, plotter: Any) -> None:
        self.plotter = plotter
        self.document: ModelDocument | None = None
        self._actors: list[tuple[Any, str]] = []
        self._glb_actors: list[Any] = []
        self._glb_source: Path | None = None
        self._display_mode = "Wireframe"
        self._point_size = 1
        self._is_splat = False
        self.set_theme(True)
        self.plotter.add_axes(line_width=2)

    def set_theme(self, dark: bool) -> None:
        from openreef.ui.theme import viewport_background

        color, top = viewport_background(dark)
        self.plotter.set_background(color, top=top)
        self.plotter.render()

    def clear_document(self) -> None:
        """Remove the current project model without leaving stale actors behind."""

        self.plotter.clear()
        self.plotter.add_axes(line_width=2)
        self.document = None
        self._actors.clear()
        self._glb_actors.clear()
        self._glb_source = None
        self._is_splat = False
        self.plotter.render()

    def set_document(self, document: ModelDocument, *, render_splat: bool = True) -> None:
        self.plotter.clear()
        self.plotter.add_axes(line_width=2)
        self.document = document
        self._actors.clear()
        self._is_splat = is_gaussian_splat(document)

        if self._is_splat:
            self._glb_actors.clear()
            self._glb_source = None
            if render_splat:
                for part in document.parts:
                    self._add_gaussian_splats(part.dataset, part.name)
                self.fit_to_view()
            return

        if document.material_source is not None:
            material_source = document.material_source.resolve()
            source_is_material = document.source.resolve() == material_source
            imported = source_is_material and self._import_textured_glb(material_source)
            if not imported and self._glb_source != material_source:
                imported = self._import_textured_glb(material_source)
            if imported and not source_is_material:
                imported = self._reuse_textured_actors(document)
            elif not imported and self._glb_source == material_source:
                imported = self._reuse_textured_actors(document)
            if imported:
                self.set_display_mode(self._display_mode)
                self.fit_to_view()
                return
        else:
            self._glb_actors.clear()
            self._glb_source = None

        for part in document.parts:
            color_options: dict[str, object] = {}
            if part.vertex_color:
                color_options = {"scalars": part.vertex_color, "rgb": True}

            if part.kind == "point-cloud":
                actor = self.plotter.add_points(
                    part.dataset,
                    name=part.name,
                    color="#6ea0ff" if not color_options else None,
                    point_size=self._point_size,
                    render_points_as_spheres=True,
                    **color_options,
                )
            else:
                actor = self.plotter.add_mesh(
                    part.dataset,
                    name=part.name,
                    color="#5b8cff" if not color_options else None,
                    smooth_shading=False,
                    **color_options,
                )
            self._actors.append((actor, part.kind))

        self.set_display_mode(self._display_mode)
        self.fit_to_view()

    @property
    def is_splat(self) -> bool:
        return self._is_splat

    @property
    def mesh_actors(self) -> tuple[Any, ...]:
        """Actors that may be used for surface picking."""

        return tuple(actor for actor, kind in self._actors if kind == "mesh")

    def _add_gaussian_splats(self, dataset: Any, name: str) -> None:
        """Render OpenSplat attributes with VTK's embedded GPU Gaussian mapper."""
        import numpy as np

        dc = np.column_stack(
            (
                np.asarray(dataset.point_data["f_dc_0"]),
                np.asarray(dataset.point_data["f_dc_1"]),
                np.asarray(dataset.point_data["f_dc_2"]),
            )
        )
        rgb = np.clip(0.5 + 0.28209479177387814 * dc, 0.0, 1.0)
        opacity_logits = np.asarray(dataset.point_data["opacity"], dtype=float)
        opacity = 1.0 / (1.0 + np.exp(-np.clip(opacity_logits, -20.0, 20.0)))
        log_scales = np.column_stack(
            tuple(np.asarray(dataset.point_data[f"scale_{index}"]) for index in range(3))
        )
        scale = np.exp(np.clip(log_scales, -20.0, 20.0)).max(axis=1)
        finite_scale = scale[np.isfinite(scale)]
        if finite_scale.size:
            # A few unconstrained outliers can otherwise cover the entire view.
            scale = np.minimum(scale, np.percentile(finite_scale, 99.0))
        rgba = np.column_stack((rgb, opacity))
        dataset.point_data[SPLAT_RGB] = np.round(rgba * 255).astype(np.uint8)
        dataset.point_data[SPLAT_SCALE] = scale.astype(np.float32)
        dataset.point_data[SPLAT_OPACITY] = opacity.astype(np.float32)

        actor = self.plotter.add_points(
            dataset,
            name=name,
            style="points_gaussian",
            scalars=SPLAT_RGB,
            rgba=True,
            emissive=False,
            point_size=self._point_size,
        )
        mapper = actor.GetMapper()
        if hasattr(mapper, "SetScaleArray"):
            mapper.SetScaleArray(SPLAT_SCALE)
        if hasattr(mapper, "SetScaleFactor"):
            mapper.SetScaleFactor(SPLAT_SCALE_FACTOR * self._point_size)
        self._actors.append((actor, "gaussian-splat"))

    def _import_textured_glb(self, source: Path) -> bool:
        """Let VTK's glTF importer retain embedded materials and texture images."""
        try:
            renderer = self.plotter.renderer
            existing_actors = list(renderer.actors.values())
            existing = {_actor_identity(actor) for actor in existing_actors}
            self.plotter.import_gltf(source, set_camera=False)
            imported = [
                actor
                for actor in renderer.actors.values()
                if _actor_identity(actor) not in existing
                and hasattr(actor, "GetProperty")
                and hasattr(actor.GetProperty(), "SetRepresentationToWireframe")
            ]
        except Exception:
            return False
        self._glb_actors = imported
        self._glb_source = source
        self._actors.extend((actor, "mesh") for actor in imported)
        return bool(imported)

    def _reuse_textured_actors(self, document: ModelDocument) -> bool:
        """Keep the GLB importer pipeline while replacing it with edited geometry."""
        mesh_parts = [part for part in document.parts if part.kind == "mesh"]
        if not mesh_parts or len(mesh_parts) != len(self._glb_actors):
            return False
        self._actors.clear()
        for part, actor in zip(mesh_parts, self._glb_actors, strict=True):
            actor.GetMapper().SetInputData(part.dataset)
            self.plotter.add_actor(actor, name=part.name)
            self._actors.append((actor, "mesh"))
        return True

    def set_display_mode(self, mode: str) -> None:
        if mode not in DISPLAY_MODES:
            raise ValueError(f"Unknown display mode: {mode}")
        self._display_mode = mode
        for actor, kind in self._actors:
            if kind == "point-cloud":
                continue
            prop = actor.GetProperty()
            if not hasattr(prop, "SetRepresentationToWireframe"):
                continue
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
            if kind == "gaussian-splat":
                mapper = actor.GetMapper()
                if hasattr(mapper, "SetScaleFactor"):
                    mapper.SetScaleFactor(SPLAT_SCALE_FACTOR * size)
            elif kind == "point-cloud":
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

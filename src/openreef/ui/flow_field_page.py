"""Dedicated mesh-only flow-field workflow page."""

from __future__ import annotations

import time
from pathlib import Path

import pyvista as pv
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from openreef.core.camera import CameraOrientation
from openreef.core.flow import (
    FlowField,
    FlowParameters,
    FlowParticles,
    ReefMeshFlowField,
    trail_lines,
    trail_rgba,
)
from openreef.core.scene import DISPLAY_MODES, SceneController
from openreef.io.model_loader import ModelLoadError, load_model
from openreef.pipeline.stages import DatasetLayout
from openreef.ui.controls import CollapsibleSection
from openreef.ui.model_catalog import (
    ModelCatalogItem,
    discover_model_catalog,
    textured_mesh_items,
)
from openreef.ui.viewport import ReefInteractor


class FlowFieldControls(QWidget):
    """Viewer controls limited to texture resolution, camera, display, and flow."""

    resolution_changed = Signal(str)
    fit_requested = Signal()
    projection_changed = Signal(bool)
    display_mode_changed = Signal(str)
    standard_view_requested = Signal(str)
    enabled_changed = Signal(bool)
    direction_changed = Signal(int)
    speed_changed = Signal(float)
    density_changed = Signal(int)
    trail_length_changed = Signal(float)
    wake_strength_changed = Signal(float)
    surface_following_changed = Signal(float)
    reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("viewerControls")
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("OPENREEF")
        heading.setObjectName("heading")
        subtitle = QLabel("Flow Field 0.1")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        resolution_form = QFormLayout()
        self.resolution = QComboBox()
        self.resolution.setToolTip(
            "Choose among textured-mesh resolutions generated for this project."
        )
        self.resolution.currentIndexChanged.connect(self._resolution_changed)
        resolution_form.addRow("Texture mesh", self.resolution)
        layout.addLayout(resolution_form)

        self.view_group = CollapsibleSection("View", expanded=True)
        view_layout = self.view_group.content_layout
        fit_button = QPushButton("Fit to view")
        fit_button.setShortcut("F")
        fit_button.clicked.connect(self.fit_requested)
        view_layout.addWidget(fit_button)
        self.projection = QCheckBox("Orthographic projection")
        self.projection.toggled.connect(self.projection_changed)
        view_layout.addWidget(self.projection)
        view_grid = QGridLayout()
        for index, name in enumerate(("Top", "Bottom", "Front", "Back", "Left", "Right")):
            button = QPushButton(name)
            button.clicked.connect(
                lambda checked=False, value=name: self.standard_view_requested.emit(value)
            )
            view_grid.addWidget(button, index // 3, index % 3)
        view_layout.addLayout(view_grid)
        layout.addWidget(self.view_group)

        self.display_group = CollapsibleSection("Display", expanded=True)
        display_form = QFormLayout()
        self.display_mode = QComboBox()
        self.display_mode.addItems(DISPLAY_MODES)
        self.display_mode.setCurrentText("Solid")
        self.display_mode.currentTextChanged.connect(self.display_mode_changed)
        display_form.addRow("Mesh mode", self.display_mode)
        self.display_group.content_layout.addLayout(display_form)
        layout.addWidget(self.display_group)

        self.flow_group = CollapsibleSection("Flow", expanded=True)
        flow_layout = self.flow_group.content_layout
        self.enabled = QCheckBox("Show flow")
        self.enabled.setChecked(True)
        self.enabled.toggled.connect(self.enabled_changed)
        flow_layout.addWidget(self.enabled)

        flow_form = QFormLayout()
        self.direction = QSlider(Qt.Orientation.Horizontal)
        self.direction.setRange(0, 360)
        self.direction.setSingleStep(5)
        self.direction.setValue(270)
        self.direction_value = QLabel("270°")
        self.direction.valueChanged.connect(self._direction_changed)
        flow_form.addRow("Direction", self._slider_row(self.direction, self.direction_value))

        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(0, 100)
        self.speed.setValue(58)
        self.speed_value = QLabel("0.58")
        self.speed.valueChanged.connect(self._speed_changed)
        flow_form.addRow("Relative speed", self._slider_row(self.speed, self.speed_value))

        self.density = QComboBox()
        self.density.addItem("Low · 750", 750)
        self.density.addItem("Medium · 1.5k", 1_500)
        self.density.addItem("High · 3k", 3_000)
        self.density.setCurrentIndex(1)
        self.density.currentIndexChanged.connect(
            lambda: self.density_changed.emit(int(self.density.currentData()))
        )
        flow_form.addRow("Particle density", self.density)

        self.trail_length = QSlider(Qt.Orientation.Horizontal)
        self.trail_length.setRange(25, 70)
        self.trail_length.setValue(50)
        self.trail_value = QLabel("5.0 s")
        self.trail_length.valueChanged.connect(self._trail_changed)
        flow_form.addRow("Trail length", self._slider_row(self.trail_length, self.trail_value))

        self.wake_strength = QSlider(Qt.Orientation.Horizontal)
        self.wake_strength.setRange(0, 100)
        self.wake_strength.setValue(72)
        self.wake_value = QLabel("0.72")
        self.wake_strength.valueChanged.connect(self._wake_changed)
        flow_form.addRow("Wake strength", self._slider_row(self.wake_strength, self.wake_value))

        self.surface_following = QSlider(Qt.Orientation.Horizontal)
        self.surface_following.setRange(0, 100)
        self.surface_following.setValue(82)
        self.following_value = QLabel("0.82")
        self.surface_following.valueChanged.connect(self._following_changed)
        flow_form.addRow(
            "Surface following",
            self._slider_row(self.surface_following, self.following_value),
        )
        flow_layout.addLayout(flow_form)
        reset_button = QPushButton("Reset particles")
        reset_button.clicked.connect(self.reset_requested)
        flow_layout.addWidget(reset_button)
        layout.addWidget(self.flow_group)

        self.status = QLabel("Choose a project with a textured mesh.")
        self.status.setObjectName("pageSubtitle")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)

    @staticmethod
    def _slider_row(slider: QSlider, value: QLabel) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)
        row.addWidget(slider, 1)
        value.setMinimumWidth(38)
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(value)
        return container

    def set_resolutions(
        self,
        items: tuple[ModelCatalogItem, ...],
        selected: Path | None = None,
    ) -> None:
        wanted = selected.resolve() if selected is not None else None
        self.resolution.blockSignals(True)
        self.resolution.clear()
        selected_index = -1
        for item in items:
            path = Path(item.path)
            self.resolution.addItem(item.label, str(path))
            index = self.resolution.count() - 1
            self.resolution.setItemData(index, str(path), Qt.ItemDataRole.ToolTipRole)
            if wanted is not None and path.resolve() == wanted:
                selected_index = index
        if selected_index < 0:
            selected_index = self.resolution.findText("Medium")
        if selected_index < 0 and self.resolution.count():
            selected_index = 0
        self.resolution.setCurrentIndex(selected_index)
        self.resolution.setEnabled(self.resolution.count() > 0)
        self.resolution.blockSignals(False)

    def current_path(self) -> Path | None:
        value = str(self.resolution.currentData() or "")
        return Path(value) if value else None

    def set_status(self, message: str) -> None:
        self.status.setText(message)

    def _resolution_changed(self) -> None:
        path = self.current_path()
        if path is not None:
            self.resolution_changed.emit(str(path))

    def _direction_changed(self, value: int) -> None:
        self.direction_value.setText(f"{value}°")
        self.direction_changed.emit(value)

    def _speed_changed(self, value: int) -> None:
        relative = value / 100.0
        self.speed_value.setText(f"{relative:.2f}")
        self.speed_changed.emit(relative)

    def _trail_changed(self, value: int) -> None:
        seconds = value / 10.0
        self.trail_value.setText(f"{seconds:.1f} s")
        self.trail_length_changed.emit(seconds)

    def _wake_changed(self, value: int) -> None:
        relative = value / 100.0
        self.wake_value.setText(f"{relative:.2f}")
        self.wake_strength_changed.emit(relative)

    def _following_changed(self, value: int) -> None:
        relative = value / 100.0
        self.following_value.setText(f"{relative:.2f}")
        self.surface_following_changed.emit(relative)


class FlowOverlayController:
    """Own the animated PyVista trail actor without changing the mesh renderer."""

    def __init__(self, plotter: ReefInteractor) -> None:
        self.plotter = plotter
        self.parameters = FlowParameters()
        self.field: FlowField | None = None
        self.particles: FlowParticles | None = None
        self.polydata: pv.PolyData | None = None
        self.enabled = True
        self.particle_count = 1_500
        self.trail_length = 5.0
        self.elapsed = 0.0

    def set_flow_field(self, field: FlowField) -> None:
        self.clear()
        self.field = field
        self._build_particles()

    def clear(self) -> None:
        self.plotter.remove_actor("flow-trails", render=False)
        self.plotter.remove_actor("flow-direction", render=False)
        self.field = None
        self.particles = None
        self.polydata = None

    def update(self, delta: float) -> None:
        if not self.enabled or self.particles is None or self.polydata is None:
            return
        self.elapsed += delta
        self.particles.update(delta, self.elapsed)
        points, speeds = self.particles.ordered_trails()
        self.polydata.points = points
        self.polydata.point_data["Flow colour"] = trail_rgba(
            speeds,
            self.particle_count,
            self.particles.trail_segments,
        )
        self.polydata.Modified()
        self.plotter.render()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        actor = self.plotter.renderer.actors.get("flow-trails")
        if actor is not None:
            actor.SetVisibility(enabled)
        self.plotter.render()

    def set_direction(self, direction: int) -> None:
        self.parameters.direction = float(direction)
        if self.particles is not None:
            self.particles.reset()
        self._update_direction_indicator()

    def set_speed(self, speed: float) -> None:
        self.parameters.speed = speed

    def set_density(self, count: int) -> None:
        self.particle_count = count
        if self.field is not None:
            self._build_particles()

    def set_trail_length(self, seconds: float) -> None:
        self.trail_length = seconds
        if self.particles is not None:
            self.particles.trail_length = seconds
            self.particles.reset()

    def set_wake_strength(self, strength: float) -> None:
        self.parameters.wake_strength = strength

    def set_surface_following(self, strength: float) -> None:
        self.parameters.surface_following = strength

    def reset(self) -> None:
        if self.particles is not None:
            self.particles.reset()

    def _build_particles(self) -> None:
        if self.field is None:
            return
        self.plotter.remove_actor("flow-trails", render=False)
        self.particles = FlowParticles(
            self.field,
            self.particle_count,
            trail_length=self.trail_length,
        )
        points, speeds = self.particles.ordered_trails()
        self.polydata = pv.PolyData(
            points,
            lines=trail_lines(self.particle_count, self.particles.trail_segments),
        )
        self.polydata.point_data["Flow colour"] = trail_rgba(
            speeds,
            self.particle_count,
            self.particles.trail_segments,
        )
        self.plotter.add_mesh(
            self.polydata,
            name="flow-trails",
            scalars="Flow colour",
            rgba=True,
            line_width=1.2,
            opacity=1.0,
            lighting=False,
            render_lines_as_tubes=False,
            show_scalar_bar=False,
        )
        self.set_enabled(self.enabled)
        self._update_direction_indicator()

    def _update_direction_indicator(self) -> None:
        self.plotter.remove_actor("flow-direction", render=False)
        # Keep this ASCII-only: Qt/VTK font fallbacks can omit arrow glyphs on macOS.
        directions = ("^", "/>", "-->", "\\>", "v", "</", "<--", "<\\")
        index = round(self.parameters.direction / 45.0) % len(directions)
        self.plotter.add_text(
            f"CURRENT  {directions[index]}  {self.parameters.direction:.0f} deg",
            position="lower_right",
            font_size=10,
            color="#00bc8c",
            name="flow-direction",
        )


class FlowFieldPage(QWidget):
    """Workflow page with a compact project band above a large flow viewer."""

    dataset_path_changed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        preferred_orientation: CameraOrientation | None = None,
    ) -> None:
        super().__init__(parent)
        self._dataset_root: Path | None = None
        self._pending_path: Path | None = None
        self._active = False
        self._preferred_orientation = preferred_orientation
        self._last_tick = time.perf_counter()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)
        outer.addWidget(self._build_header())

        viewer = QWidget()
        viewer_layout = QHBoxLayout(viewer)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        self.plotter = ReefInteractor(viewer)
        if preferred_orientation is not None:
            self.plotter.set_world_up(preferred_orientation.world_up_axis)
        self.controls = FlowFieldControls(viewer)
        controls_scroll = QScrollArea(viewer)
        controls_scroll.setObjectName("viewerControlsScroll")
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls_scroll.setMinimumWidth(280)
        controls_scroll.setMaximumWidth(360)
        controls_scroll.setWidget(self.controls)
        viewer_layout.addWidget(self.plotter.interactor, 1)
        viewer_layout.addWidget(controls_scroll)
        outer.addWidget(viewer, 1)

        self.scene = SceneController(self.plotter)
        self.scene.set_display_mode("Solid")
        self.flow = FlowOverlayController(self.plotter)
        self._connect_controls()
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("flowFieldHeader")
        header.setMinimumHeight(130)
        header.setMaximumHeight(170)
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(8)
        title = QLabel("Flow Field")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Configure and run the flow field.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.dataset_path = QLineEdit()
        self.dataset_path.setPlaceholderText("Dataset folder")
        self.dataset_path.setMinimumWidth(380)
        self.dataset_path.editingFinished.connect(self._path_edited)
        browse = QPushButton("Choose…")
        browse.clicked.connect(self._choose_folder)
        row.addWidget(self.dataset_path, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        return header

    def _connect_controls(self) -> None:
        self.controls.resolution_changed.connect(self._resolution_changed)
        self.controls.fit_requested.connect(self.scene.fit_to_view)
        self.controls.projection_changed.connect(self.scene.set_parallel_projection)
        self.controls.display_mode_changed.connect(self.scene.set_display_mode)
        self.controls.standard_view_requested.connect(self.scene.set_standard_view)
        self.controls.enabled_changed.connect(self.flow.set_enabled)
        self.controls.direction_changed.connect(self.flow.set_direction)
        self.controls.speed_changed.connect(self.flow.set_speed)
        self.controls.density_changed.connect(self.flow.set_density)
        self.controls.trail_length_changed.connect(self.flow.set_trail_length)
        self.controls.wake_strength_changed.connect(self.flow.set_wake_strength)
        self.controls.surface_following_changed.connect(self.flow.set_surface_following)
        self.controls.reset_requested.connect(self.flow.reset)

    def set_dataset_root(self, path: str | Path) -> None:
        value = str(Path(path).expanduser().resolve()) if str(path).strip() else ""
        self.dataset_path.blockSignals(True)
        self.dataset_path.setText(value)
        self.dataset_path.blockSignals(False)
        if not value:
            self._dataset_root = None
            self.controls.set_resolutions(())
            self.controls.set_status("Choose a project with a textured mesh.")
            return
        self._dataset_root = Path(value)
        sections = discover_model_catalog(DatasetLayout(self._dataset_root))
        items = textured_mesh_items(sections)
        current = self.controls.current_path()
        self.controls.set_resolutions(items, current)
        selected = self.controls.current_path()
        if selected is None:
            self.controls.set_status("No textured mesh is available for this project yet.")
            self.scene.clear_document()
            self.flow.clear()
            return
        self._pending_path = selected
        self.controls.set_status(
            f"{len(items)} textured resolution{'s' if len(items) != 1 else ''} available."
        )
        if self._active:
            self._load_pending()

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._load_pending()
            self._last_tick = time.perf_counter()
            self.timer.start()
        else:
            self.timer.stop()

    def set_theme(self, dark: bool) -> None:
        self.scene.set_theme(dark)

    def set_preferred_orientation(
        self,
        orientation: CameraOrientation | None,
    ) -> None:
        """Apply the Viewer Set view orientation and rebuild its visible surface."""

        self._preferred_orientation = orientation
        self.plotter.set_world_up(
            orientation.world_up_axis if orientation is not None else (0.0, 0.0, 1.0)
        )
        selected = self.controls.current_path()
        if selected is not None:
            self._pending_path = selected
        if self._active:
            self._load_pending()

    def shutdown(self) -> None:
        self.timer.stop()
        self.flow.clear()
        self.plotter.close()

    def _load_pending(self) -> None:
        path = self._pending_path
        if path is None:
            return
        self._pending_path = None
        self.controls.set_status(f"Loading {path.name}…")
        QApplication.processEvents()
        try:
            document = load_model(path)
            self.scene.set_document(document)
            self.scene.set_display_mode(self.controls.display_mode.currentText())
            self.controls.set_status("Building mesh flow terrain…")
            QApplication.processEvents()
            field = ReefMeshFlowField.from_document(
                document,
                surface_sign=self._surface_sign(),
                parameters=self.flow.parameters,
            )
            self.flow.set_flow_field(field)
        except (ModelLoadError, OSError, RuntimeError, TypeError, ValueError) as exc:
            self.controls.set_status(f"Flow Field could not load: {exc}")
            return
        self.controls.set_status(
            f"{path.stem} · {document.stats.cells:,} cells · relative units"
        )
        self._fit_to_preferred_view()

    def _surface_sign(self) -> float:
        orientation = self._preferred_orientation
        return orientation.world_up_axis[2] if orientation is not None else 1.0

    def _fit_to_preferred_view(self) -> None:
        orientation = self._preferred_orientation
        if orientation is not None:
            orientation.apply(self.plotter)
        self.scene.fit_to_view()
        if orientation is not None:
            self.plotter.camera.Zoom(0.82)
            self.plotter.reset_camera_clipping_range()
            self.plotter.render()
        self.flow.reset()

    def _resolution_changed(self, value: str) -> None:
        self._pending_path = Path(value)
        if self._active:
            self._load_pending()

    def _choose_folder(self) -> None:
        start = self.dataset_path.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose OpenReef dataset", start)
        if selected:
            self.set_dataset_root(selected)
            self.dataset_path_changed.emit(selected)

    def _path_edited(self) -> None:
        value = self.dataset_path.text().strip()
        if (
            self._dataset_root is not None
            and Path(value).expanduser().resolve() == self._dataset_root
        ):
            return
        self.set_dataset_root(value)
        self.dataset_path_changed.emit(value)

    def _tick(self) -> None:
        now = time.perf_counter()
        delta = now - self._last_tick
        self._last_tick = now
        self.flow.update(delta)

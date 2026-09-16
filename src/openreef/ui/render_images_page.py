"""Consolidated reconstruction workflow dashboard."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from openreef.pipeline.runner import PipelineRunner, format_elapsed
from openreef.pipeline.stages import (
    STAGE_LABELS,
    STAGE_OUTPUTS,
    DatasetLayout,
    PipelineOptions,
    StageKey,
    stage_output_exists,
    textured_output_for_level,
)
from openreef.ui.theme import (
    PRIMARY_ACCENT,
    RUNNING_ACCENT,
    WARNING_ACCENT,
    bootstrap_icon,
)

WORKFLOW_GROUPS = (
    (
        "Sparse cloud",
        "Find overlaps and solve camera positions",
        "cloud",
        PRIMARY_ACCENT,
        (
            StageKey.FEATURES,
            StageKey.MATCHING,
            StageKey.SPARSE,
            StageKey.UNDISTORT,
        ),
    ),
    (
        "Dense cloud",
        "Build detailed points and a surface",
        "cloud-fill",
        RUNNING_ACCENT,
        (StageKey.OPENMVS_IMPORT, StageKey.DENSE, StageKey.MESH),
    ),
    (
        "Texture mesh",
        "Project photographs onto the surface",
        "border",
        "#6b95ed",
        (StageKey.TEXTURE,),
    ),
    (
        "Gaussian splat",
        "Train an optional appearance model",
        "flower2",
        "#7a9ce8",
        (StageKey.GAUSSIAN,),
    ),
)


class WorkflowStep(QFrame):
    """One selectable pipeline step with state and progress."""

    clicked = Signal(str)

    def __init__(self, stage: StageKey, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stage = stage
        self.setObjectName("workflowStep")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)

        self.checkbox = QCheckBox(STAGE_LABELS[stage])
        self.checkbox.setToolTip(f"Expected output: {STAGE_OUTPUTS[stage]}")
        self.checkbox.clicked.connect(lambda: self.clicked.emit(self.stage.value))
        self.status = QLabel("Pending")
        self.status.setObjectName("statusBadge")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.checkbox, 0, 0)
        layout.addWidget(self.status, 0, 1)
        layout.addWidget(self.progress, 1, 0, 1, 2)
        layout.setColumnStretch(0, 1)

    def mousePressEvent(self, event: object) -> None:  # noqa: N802 - Qt API name
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.stage.value)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_state(self, state: str, detail: str | None = None) -> None:
        labels = {
            "complete": "Complete",
            "pending": "Pending",
            "queued": "Queued",
            "running": "Running",
            "failed": "Failed",
            "stopped": "Stopped",
        }
        self.status.setText(labels.get(state, state.title()))
        self.status.setProperty("state", state)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.progress.setProperty("state", state)
        self.progress.style().unpolish(self.progress)
        self.progress.style().polish(self.progress)
        self.status.setToolTip(detail or "")
        if state == "running":
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 1)
            self.progress.setValue(1 if state == "complete" else 0)

    def set_progress(self, completed: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(completed)
        percent = completed * 100 // max(1, total)
        prefix = "Running · " if self.status.property("state") == "running" else ""
        self.status.setText(f"{prefix}{percent}%")


class WorkflowGroup(QFrame):
    settings_requested = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        accent: str,
        stages: tuple[StageKey, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workflowGroup")
        self.stages = stages
        self.setMinimumWidth(226)
        self.setStyleSheet(f"QFrame#workflowGroup {{ border-top: 2px solid {accent}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 11)
        layout.setSpacing(8)

        heading = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(bootstrap_icon(icon_name, accent, 40).pixmap(22, 22))
        icon.setStyleSheet("background: transparent; border: 0;")
        title_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("workflowGroupTitle")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("workflowGroupSubtitle")
        subtitle_label.setWordWrap(True)
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        heading.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        heading.addLayout(title_box, 1)
        self.status = QLabel("Pending")
        self.status.setObjectName("statusBadge")
        self.status.setProperty("state", "pending")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.addWidget(self.status, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(heading)

        self.steps: dict[StageKey, WorkflowStep] = {}
        for stage in stages:
            step = WorkflowStep(stage)
            self.steps[stage] = step
            layout.addWidget(step)
        layout.addStretch(1)

        settings = QPushButton("Processing settings")
        settings.setObjectName("workflowSettingsButton")
        settings.clicked.connect(self.settings_requested)
        layout.addWidget(settings)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def refresh_state(self) -> None:
        states = [step.status.property("state") for step in self.steps.values()]
        if "running" in states:
            state, label = "running", "Running"
        elif "failed" in states:
            state, label = "failed", "Needs attention"
        elif states and all(value == "complete" for value in states):
            state, label = "complete", "Complete"
        elif "queued" in states:
            state, label = "queued", "Queued"
        else:
            state, label = "pending", "Pending"
        self.status.setText(label)
        self.status.setProperty("state", state)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)


class CropCheckpoint(QFrame):
    requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cropCheckpoint")
        self.setStyleSheet(
            f"QFrame#cropCheckpoint {{ border-top: 2px solid {WARNING_ACCENT}; }}"
        )
        self.setFixedWidth(142)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(11, 12, 11, 11)
        layout.setSpacing(8)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(bootstrap_icon("crosshair", WARNING_ACCENT, 40).pixmap(24, 24))
        icon.setStyleSheet("background: transparent; border: 0;")
        title = QLabel("Crop area")
        title.setObjectName("workflowGroupTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {WARNING_ACCENT}; font-size: 15px; font-weight: 700;"
        )
        note = QLabel("Optional checkpoint after the sparse cloud")
        note.setObjectName("workflowGroupSubtitle")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        self.status = QLabel("No crop")
        self.status.setObjectName("statusBadge")
        self.status.setProperty("state", "pending")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button = QPushButton("Review & crop")
        self.button.setEnabled(False)
        self.button.clicked.connect(self.requested)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(self.status)
        layout.addWidget(self.button)

    def set_available(self, sparse_ready: bool, cropped: bool) -> None:
        self.button.setEnabled(sparse_ready)
        self.status.setText("Crop saved" if cropped else "Optional")
        self.status.setProperty("state", "complete" if cropped else "pending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)


class TilesetCheckpoint(QFrame):
    requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._building = False
        self.setObjectName("tilesetCheckpoint")
        self.setStyleSheet(
            "QFrame#tilesetCheckpoint { border-top: 2px solid #20c997; }"
        )
        self.setFixedWidth(142)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(11, 12, 11, 11)
        layout.setSpacing(8)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(bootstrap_icon("box", "#20c997", 40).pixmap(24, 24))
        icon.setStyleSheet("background: transparent; border: 0;")
        title = QLabel("3D tiles")
        title.setObjectName("workflowGroupTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #20c997; font-size: 15px; font-weight: 700;")
        note = QLabel("Build streaming tiles from a textured model")
        note.setObjectName("workflowGroupSubtitle")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        self.status = QLabel("Not packaged")
        self.status.setObjectName("statusBadge")
        self.status.setProperty("state", "pending")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button = QPushButton("Build tiles…")
        self.button.setEnabled(False)
        self.button.setToolTip(
            "Choose the highest-detail textured GLB in this dataset's models folder."
        )
        self.button.clicked.connect(self.requested)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(self.status)
        layout.addWidget(self.button)

    def set_available(self, dataset_ready: bool, packaged: bool) -> None:
        self.button.setEnabled(dataset_ready and not self._building)
        if self._building:
            return
        self.status.setText("In models" if packaged else "Not packaged")
        self.status.setProperty("state", "complete" if packaged else "pending")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def set_building(self, building: bool, percent: int = 0, message: str = "") -> None:
        self._building = building
        self.button.setEnabled(not building)
        if building:
            self.status.setText(f"Building {max(0, min(100, percent))}%")
            self.status.setProperty("state", "running")
            self.button.setToolTip(message)
        else:
            self.button.setToolTip(
                "Choose the highest-detail textured GLB in this dataset's models folder."
            )
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)


class RenderImagesPage(QWidget):
    dataset_path_changed = Signal(str)
    open_artifact_requested = Signal(str)
    crop_requested = Signal()
    tileset_requested = Signal()

    def __init__(self, runner: PipelineRunner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.runner = runner
        self._external_busy = False
        self._artifact: Path | None = None
        self.steps: dict[StageKey, WorkflowStep] = {}
        self.groups: list[WorkflowGroup] = []
        self.global_controls: list[QWidget] = []
        self.settings_pages: dict[StageKey, int] = {}
        self._selected_stage = StageKey.FEATURES

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)
        layout.addLayout(self._build_header())
        layout.addWidget(self._build_workflow())
        layout.addLayout(self._build_run_bar())
        layout.addWidget(self._build_details(), 1)

        self.runner.output_received.connect(self._append_output)
        self.runner.stage_changed.connect(self._stage_changed)
        self.runner.current_stage_changed.connect(self.current_stage.setText)
        self.runner.progress_changed.connect(self._progress_changed)
        self.runner.stage_progress.connect(self._stage_progress)
        self.runner.running_changed.connect(self._running_changed)
        self.runner.job_finished.connect(self._job_finished)
        self.runner.artifact_ready.connect(self._artifact_ready)

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(1000)
        self.elapsed_timer.timeout.connect(self._update_elapsed)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(18)
        title = QLabel("Render images")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        self.dataset_path = QLineEdit()
        self.dataset_path.setPlaceholderText("Dataset folder")
        self.dataset_path.setMinimumWidth(380)
        self.dataset_path.editingFinished.connect(self._path_edited)
        self.browse_button = QPushButton("Choose…")
        self.browse_button.clicked.connect(self._choose_folder)
        row.addWidget(self.dataset_path, 1)
        row.addWidget(self.browse_button)

        # Retain the summary as internal state for cross-page synchronisation,
        # without adding another line of explanatory text to the header.
        self.dataset_summary = QLabel("No dataset selected")
        self.dataset_summary.hide()
        return row

    def _build_workflow(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(330)
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(10)

        for index, (title, subtitle, icon, accent, stages) in enumerate(WORKFLOW_GROUPS):
            group = WorkflowGroup(title, subtitle, icon, accent, stages)
            group.settings_requested.connect(
                lambda checked=False, stage=stages[0]: self._select_settings(stage)
            )
            for step in group.steps.values():
                step.clicked.connect(self._step_clicked)
            self.groups.append(group)
            self.steps.update(group.steps)
            row.addWidget(group, 1)
            if index == 0:
                arrow = QLabel("→")
                arrow.setObjectName("workflowArrow")
                arrow.setStyleSheet(f"color: {PRIMARY_ACCENT}; font-size: 22px;")
                row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignCenter)
                self.crop_checkpoint = CropCheckpoint()
                self.crop_checkpoint.requested.connect(self.crop_requested)
                row.addWidget(self.crop_checkpoint)
                crop_arrow = QLabel("→")
                crop_arrow.setObjectName("workflowArrow")
                crop_arrow.setStyleSheet("color: #718099; font-size: 22px;")
                row.addWidget(crop_arrow, 0, Qt.AlignmentFlag.AlignCenter)
            elif index < len(WORKFLOW_GROUPS) - 1:
                arrow = QLabel("→")
                arrow.setObjectName("workflowArrow")
                arrow.setStyleSheet(f"color: {accent}; font-size: 24px;")
                row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignCenter)
        tiles_arrow = QLabel("→")
        tiles_arrow.setObjectName("workflowArrow")
        tiles_arrow.setStyleSheet("color: #20c997; font-size: 22px;")
        row.addWidget(tiles_arrow, 0, Qt.AlignmentFlag.AlignCenter)
        self.tileset_checkpoint = TilesetCheckpoint()
        self.tileset_checkpoint.requested.connect(self.tileset_requested)
        row.addWidget(self.tileset_checkpoint)
        scroll.setWidget(container)
        return scroll

    def _build_global_options(self) -> QGroupBox:
        """Single-column controls shared by every reconstruction stage."""
        panel = QGroupBox("Global processing & outputs")
        panel.setObjectName("globalOptions")
        panel.setMinimumWidth(240)
        layout = QVBoxLayout(panel)
        layout.setSpacing(9)

        resources = QFormLayout()
        resources.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        available_cores = max(1, os.cpu_count() or 1)
        self.cores = QSpinBox()
        self.cores.setRange(1, available_cores)
        self.cores.setValue(max(1, available_cores - 2))
        self.cores.setSuffix(" cores")
        self.memory = QDoubleSpinBox()
        self.memory.setRange(0, 256)
        self.memory.setDecimals(0)
        self.memory.setSpecialValueText("Unlimited")
        self.memory.setSuffix(" GB")
        self.global_controls.extend((self.cores, self.memory))
        resources.addRow("CPU", self.cores)
        resources.addRow("RAM", self.memory)
        layout.addLayout(resources)

        outputs = QLabel("OUTPUT LEVELS")
        outputs.setObjectName("fieldLabel")
        layout.addWidget(outputs)
        for key, label, value, checked in (
            ("original", "Original", 100, True),
            ("medium", "Medium", 20, False),
            ("low", "Low", 5, False),
        ):
            checkbox = QCheckBox(label)
            checkbox.setChecked(checked)
            percent = QSpinBox()
            percent.setRange(1, 100)
            percent.setValue(value)
            percent.setSuffix("%")
            percent.setFixedWidth(72)
            percent.setEnabled(checked)
            checkbox.toggled.connect(percent.setEnabled)
            checkbox.toggled.connect(self._profiles_changed)
            percent.valueChanged.connect(self._profiles_changed)
            setattr(self, f"dense_{key}", checkbox)
            setattr(self, f"dense_{key}_percent", percent)
            output_row = QHBoxLayout()
            output_row.setSpacing(7)
            output_row.addWidget(checkbox, 1)
            output_row.addWidget(percent)
            layout.addLayout(output_row)
            self.global_controls.extend((checkbox, percent))
        self.compact_output = QCheckBox("Compact")
        self.compact_output.setToolTip(
            "Prepare the smallest selected geometry for a final share copy under 100 MB."
        )
        self.compact_output.toggled.connect(self._profiles_changed)
        self.global_controls.append(self.compact_output)
        layout.addWidget(self.compact_output)
        layout.addStretch(1)
        return panel

    def _build_settings(self) -> QGroupBox:
        group = QGroupBox("Feature extraction settings")
        group.setMinimumWidth(280)
        self.settings_group = group
        layout = QHBoxLayout(group)

        self.settings_stack = QStackedWidget()
        pages = (
            (StageKey.FEATURES, self._feature_settings()),
            (StageKey.MATCHING, self._matching_settings()),
            (StageKey.SPARSE, self._information_settings(
                "Sparse reconstruction uses the shared CPU and RAM limits above. "
                "COLMAP estimates camera positions and creates connected sparse models."
            )),
            (StageKey.UNDISTORT, self._undistort_settings()),
            (StageKey.OPENMVS_IMPORT, self._information_settings(
                "OpenMVS imports the selected COLMAP model and any saved crop. "
                "It uses the shared CPU and RAM limits above."
            )),
            (StageKey.DENSE, self._dense_settings()),
            (StageKey.MESH, self._information_settings(
                "Surface reconstruction uses each selected dense-cloud level and "
                "the shared CPU and RAM limits above."
            )),
            (StageKey.TEXTURE, self._texture_settings()),
            (StageKey.GAUSSIAN, self._gaussian_settings()),
        )
        for stage, page in pages:
            self.settings_pages[stage] = self.settings_stack.addWidget(page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.settings_stack)
        layout.addWidget(scroll, 1)
        self._select_settings(StageKey.FEATURES)
        return group

    def _build_details(self) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        row.addWidget(self._build_global_options(), 1)
        row.addWidget(self._build_settings(), 1)
        row.addWidget(self._build_terminal(), 2)
        return panel

    def _feature_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.camera_model = QComboBox()
        self.camera_model.addItems(
            ("SIMPLE_RADIAL", "PINHOLE", "OPENCV", "SIMPLE_RADIAL_FISHEYE")
        )
        self.single_camera = QCheckBox("Treat all images as one unchanged camera")
        self.single_camera.setChecked(True)
        self.feature_use_gpu = QCheckBox("Use GPU for feature finding")
        self.feature_use_gpu.setChecked(True)
        self.max_image_size = QSpinBox()
        self.max_image_size.setRange(640, 16384)
        self.max_image_size.setValue(3200)
        self.max_image_size.setSuffix(" px")
        form.addRow("Camera model", self.camera_model)
        form.addRow("Maximum image size", self.max_image_size)
        form.addRow(self.single_camera)
        form.addRow(self.feature_use_gpu)
        return page

    def _matching_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.overlap = QSpinBox()
        self.overlap.setRange(2, 100)
        self.overlap.setValue(10)
        self.overlap.setSuffix(" frames")
        self.matching_use_gpu = QCheckBox("Use GPU for feature matching")
        self.matching_use_gpu.setChecked(True)
        form.addRow("Sequence overlap", self.overlap)
        form.addRow(self.matching_use_gpu)
        return page

    def _undistort_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.undistort_max_image_size = QSpinBox()
        self.undistort_max_image_size.setRange(640, 16384)
        self.undistort_max_image_size.setValue(3200)
        self.undistort_max_image_size.setSuffix(" px")
        note = QLabel(
            "Prepares PINHOLE images for OpenMVS and Gaussian processing."
        )
        note.setObjectName("datasetSummary")
        note.setWordWrap(True)
        form.addRow(note)
        form.addRow("Maximum output size", self.undistort_max_image_size)
        return page

    def _information_settings(self, message: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel(message)
        note.setObjectName("settingsExplanation")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _dense_settings(self) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        form = QFormLayout()
        self.resolution_level = QSpinBox()
        self.resolution_level.setRange(0, 4)
        self.resolution_level.setValue(1)
        self.max_resolution = QSpinBox()
        self.max_resolution.setRange(640, 16384)
        self.max_resolution.setValue(2560)
        self.max_resolution.setSuffix(" px")
        self.number_views = QSpinBox()
        self.number_views.setRange(2, 20)
        self.number_views.setValue(5)
        self.fusion_views = QSpinBox()
        self.fusion_views.setRange(2, 10)
        self.fusion_views.setValue(3)
        self.estimate_colors = QCheckBox("Estimate point colors")
        self.estimate_colors.setChecked(True)
        self.estimate_normals = QCheckBox("Estimate point normals")
        self.estimate_normals.setChecked(True)
        form.addRow("Dense image scale", self.resolution_level)
        form.addRow("Maximum resolution", self.max_resolution)
        form.addRow("Neighbor views", self.number_views)
        form.addRow("Fusion agreement", self.fusion_views)
        form.addRow(self.estimate_colors)
        form.addRow(self.estimate_normals)
        grid.addLayout(form, 0, 0)
        grid.setColumnStretch(0, 1)
        return page

    def _texture_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.texture_resolution_level = QSpinBox()
        self.texture_resolution_level.setRange(0, 4)
        self.max_texture_size = QSpinBox()
        self.max_texture_size.setRange(1024, 16384)
        self.max_texture_size.setSingleStep(1024)
        self.max_texture_size.setValue(8192)
        self.max_texture_size.setSuffix(" px")
        self.texture_sharpness = QDoubleSpinBox()
        self.texture_sharpness.setRange(0, 2)
        self.texture_sharpness.setSingleStep(0.1)
        self.texture_sharpness.setValue(0.5)
        self.global_seam_leveling = QCheckBox("Balance texture patches")
        self.global_seam_leveling.setChecked(True)
        self.local_seam_leveling = QCheckBox("Blend patch seams")
        self.local_seam_leveling.setChecked(True)
        note = QLabel("Texture the Original, Medium, or Low meshes selected in Dense settings.")
        note.setObjectName("datasetSummary")
        note.setWordWrap(True)
        form.addRow(note)
        form.addRow("Texture image scale", self.texture_resolution_level)
        form.addRow("Texture atlas size", self.max_texture_size)
        form.addRow("Texture sharpness", self.texture_sharpness)
        form.addRow(self.global_seam_leveling)
        form.addRow(self.local_seam_leveling)
        return page

    def _gaussian_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.gaussian_executable = QLineEdit(shutil.which("opensplat") or "")
        self.gaussian_executable.setPlaceholderText("~/OpenSplat/build/opensplat")
        executable_row = QWidget()
        executable_layout = QHBoxLayout(executable_row)
        executable_layout.setContentsMargins(0, 0, 0, 0)
        executable_layout.addWidget(self.gaussian_executable, 1)
        choose = QPushButton("Choose…")
        choose.clicked.connect(self._choose_gaussian_executable)
        executable_layout.addWidget(choose)
        self.gaussian_preset = QComboBox()
        self.gaussian_preset.addItem("Preview — 7k, 4× images", (7000, 4.0, 2_000_000))
        self.gaussian_preset.addItem("Balanced — 15k, 2× images", (15000, 2.0, 3_500_000))
        self.gaussian_preset.addItem("High — 30k, full images", (30000, 1.0, 5_000_000))
        self.gaussian_preset.addItem("Custom", None)
        self.gaussian_iterations = QSpinBox()
        self.gaussian_iterations.setRange(500, 100_000)
        self.gaussian_iterations.setValue(7000)
        self.gaussian_iterations.setSuffix(" steps")
        self.gaussian_downscale = QDoubleSpinBox()
        self.gaussian_downscale.setRange(1, 8)
        self.gaussian_downscale.setValue(4)
        self.gaussian_downscale.setSuffix("×")
        self.gaussian_max_points = QSpinBox()
        self.gaussian_max_points.setRange(100_000, 20_000_000)
        self.gaussian_max_points.setValue(2_000_000)
        self.gaussian_max_points.setSuffix(" splats")
        self.gaussian_save_every = QSpinBox()
        self.gaussian_save_every.setRange(250, 10_000)
        self.gaussian_save_every.setValue(1000)
        self.gaussian_save_every.setSuffix(" steps")
        self.gaussian_resume = QCheckBox("Resume the newest checkpoint")
        self.gaussian_resume.setChecked(True)
        self.gaussian_low_memory = QCheckBox("Use less memory (slower)")
        self.gaussian_cpu = QCheckBox("Force CPU (very slow)")
        self.gaussian_center = QCheckBox("Center output (changes shared coordinates)")
        self.gaussian_preset.currentIndexChanged.connect(self._apply_gaussian_preset)
        ram = self._system_memory_gb()
        machine = platform.machine() or "unknown"
        hardware = QLabel(f"Detected {machine} · {ram:.0f} GB memory · Metal recommended")
        hardware.setObjectName("datasetSummary")
        form.addRow("OpenSplat", executable_row)
        form.addRow("Quality", self.gaussian_preset)
        form.addRow("Training length", self.gaussian_iterations)
        form.addRow("Image downscale", self.gaussian_downscale)
        form.addRow("Maximum splats", self.gaussian_max_points)
        form.addRow("Checkpoint interval", self.gaussian_save_every)
        form.addRow(self.gaussian_resume)
        form.addRow(self.gaussian_low_memory)
        form.addRow(self.gaussian_cpu)
        form.addRow(self.gaussian_center)
        form.addRow(hardware)
        return page

    def _build_run_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.run_button = QPushButton("Run checked steps")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self._start_run)
        self.incomplete_button = QPushButton("Select incomplete")
        self.incomplete_button.clicked.connect(self._select_incomplete)
        self.cancel_button = QPushButton("Stop")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.runner.cancel)
        self.latest_button = QPushButton("Open latest result")
        self.latest_button.setEnabled(False)
        self.latest_button.clicked.connect(self._open_artifact)
        row.addWidget(self.run_button)
        row.addWidget(self.incomplete_button)
        row.addWidget(self.cancel_button)
        row.addWidget(self.latest_button)
        self.current_stage = QLabel("Idle")
        self.current_stage.setObjectName("currentStage")
        row.addWidget(self.current_stage)
        self.overall_progress = QProgressBar()
        self.overall_progress.setFormat("%v of %m checked steps")
        row.addWidget(self.overall_progress, 1)
        self.elapsed = QLabel("00:00")
        row.addWidget(self.elapsed)
        return row

    def _build_terminal(self) -> QGroupBox:
        group = QGroupBox("Live processing")
        group.setMinimumWidth(480)
        layout = QVBoxLayout(group)
        toolbar = QHBoxLayout()
        clear = QPushButton("Clear")
        toolbar.addStretch(1)
        toolbar.addWidget(clear)
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName("processingTerminal")
        self.terminal.setReadOnly(True)
        self.terminal.setMinimumHeight(115)
        self.terminal.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        clear.clicked.connect(self.terminal.clear)
        layout.addLayout(toolbar)
        layout.addWidget(self.terminal)
        return group

    def _step_clicked(self, key: str) -> None:
        try:
            self._select_settings(StageKey(key))
        except ValueError:
            return

    def _select_settings(self, stage: StageKey) -> None:
        if stage not in self.settings_pages:
            return
        self._selected_stage = stage
        self.settings_stack.setCurrentIndex(self.settings_pages[stage])
        self.settings_group.setTitle(f"{STAGE_LABELS[stage]} settings")
        for group in self.groups:
            group.set_selected(stage in group.stages)
            for step_stage, step in group.steps.items():
                step.set_selected(step_stage == stage)

    def selected_options(self) -> PipelineOptions:
        return PipelineOptions(
            cores=self.cores.value(),
            memory_gb=self.memory.value(),
            use_gpu=self.feature_use_gpu.isChecked(),
            matching_use_gpu=self.matching_use_gpu.isChecked(),
            camera_model=self.camera_model.currentText(),
            single_camera=self.single_camera.isChecked(),
            max_image_size=self.max_image_size.value(),
            undistort_max_image_size=self.undistort_max_image_size.value(),
            sequential_overlap=self.overlap.value(),
            resolution_level=self.resolution_level.value(),
            max_resolution=self.max_resolution.value(),
            number_views=self.number_views.value(),
            number_views_fuse=self.fusion_views.value(),
            estimate_colors=self.estimate_colors.isChecked(),
            estimate_normals=self.estimate_normals.isChecked(),
            dense_original=self.dense_original.isChecked(),
            dense_medium=self.dense_medium.isChecked(),
            dense_low=self.dense_low.isChecked(),
            dense_compact=self.compact_output.isChecked(),
            dense_original_percent=self.dense_original_percent.value(),
            dense_medium_percent=self.dense_medium_percent.value(),
            dense_low_percent=self.dense_low_percent.value(),
            dense_compact_percent=1,
            texture_resolution_level=self.texture_resolution_level.value(),
            max_texture_size=self.max_texture_size.value(),
            texture_sharpness=self.texture_sharpness.value(),
            global_seam_leveling=self.global_seam_leveling.isChecked(),
            local_seam_leveling=self.local_seam_leveling.isChecked(),
            gaussian_executable=self.gaussian_executable.text().strip(),
            gaussian_iterations=self.gaussian_iterations.value(),
            gaussian_downscale=self.gaussian_downscale.value(),
            gaussian_max_points=self.gaussian_max_points.value(),
            gaussian_save_every=self.gaussian_save_every.value(),
            gaussian_resume=self.gaussian_resume.isChecked(),
            gaussian_center=self.gaussian_center.isChecked(),
            gaussian_cpu=self.gaussian_cpu.isChecked(),
            gaussian_low_memory=self.gaussian_low_memory.isChecked(),
        )

    def set_dataset_root(self, path: str | Path) -> None:
        value = str(Path(path).expanduser().resolve()) if str(path).strip() else ""
        self.dataset_path.blockSignals(True)
        self.dataset_path.setText(value)
        self.dataset_path.blockSignals(False)
        if not value:
            self.dataset_summary.setText("No dataset selected")
            self.tileset_checkpoint.set_available(False, False)
            return
        layout = DatasetLayout.from_path(value)
        self.dataset_summary.setText(f"{layout.image_count():,} images · {layout.root.name}")
        options = self.selected_options()
        for stage, step in self.steps.items():
            complete = stage_output_exists(stage, layout, options)
            step.set_state("complete" if complete else "pending")
            if not self.runner.is_running:
                step.checkbox.setChecked(not complete)
        for group in self.groups:
            group.refresh_state()
        sparse_ready = stage_output_exists(StageKey.SPARSE, layout)
        self.crop_checkpoint.set_available(sparse_ready, layout.roi.is_file())
        self.tileset_checkpoint.set_available(
            True,
            layout.tiled_model_manifest.is_file(),
        )
        self._find_latest_artifact(layout)

    def set_external_busy(self, busy: bool) -> None:
        self._external_busy = busy
        self._update_enabled()

    def _find_latest_artifact(self, layout: DatasetLayout) -> None:
        candidates = [layout.tiled_model_manifest, layout.gaussian_output]
        candidates.extend(
            textured_output_for_level(layout, level)
            for level in ("original", "medium", "low", "compact")
        )
        candidates.extend((layout.surface_mesh, layout.dense_cloud))
        existing = [path for path in candidates if path.is_file()]
        if existing:
            self._artifact_ready(str(max(existing, key=lambda path: path.stat().st_mtime_ns)))

    def _choose_folder(self) -> None:
        start = self.dataset_path.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose OpenReef dataset", start)
        if selected:
            self.set_dataset_root(selected)
            self.dataset_path_changed.emit(selected)

    def _path_edited(self) -> None:
        value = self.dataset_path.text().strip()
        self.set_dataset_root(value)
        self.dataset_path_changed.emit(value)

    def _choose_gaussian_executable(self) -> None:
        start = self.gaussian_executable.text() or str(Path.home())
        selected, _ = QFileDialog.getOpenFileName(self, "Choose OpenSplat", start)
        if selected:
            self.gaussian_executable.setText(selected)

    def _apply_gaussian_preset(self, *_: object) -> None:
        values = self.gaussian_preset.currentData()
        if values is None:
            return
        iterations, downscale, max_points = values
        self.gaussian_iterations.setValue(iterations)
        self.gaussian_downscale.setValue(downscale)
        self.gaussian_max_points.setValue(max_points)

    def _select_incomplete(self) -> None:
        if not self.dataset_path.text().strip():
            return
        layout = DatasetLayout.from_path(self.dataset_path.text())
        options = self.selected_options()
        for stage, step in self.steps.items():
            step.checkbox.setChecked(not stage_output_exists(stage, layout, options))

    def _profiles_changed(self, *_: object) -> None:
        if self.dataset_path.text().strip() and not self.runner.is_running:
            self.set_dataset_root(self.dataset_path.text())

    def _start_run(self) -> None:
        stages = [stage for stage, step in self.steps.items() if step.checkbox.isChecked()]
        self.runner.run(self.dataset_path.text(), stages, self.selected_options())

    def _stage_changed(self, key: str, state: str, detail: str) -> None:
        try:
            step = self.steps.get(StageKey(key))
        except ValueError:
            return
        if step is not None:
            step.set_state(state, detail)
            for group in self.groups:
                if step.stage in group.stages:
                    group.refresh_state()
                    break

    def _stage_progress(self, key: str, completed: int, total: int) -> None:
        try:
            step = self.steps.get(StageKey(key))
        except ValueError:
            return
        if step is not None:
            step.set_progress(completed, total)

    def _progress_changed(self, completed: int, total: int) -> None:
        self.overall_progress.setRange(0, total)
        self.overall_progress.setValue(completed)

    def _running_changed(self, running: bool) -> None:
        self.cancel_button.setEnabled(running)
        self._update_enabled()
        if running:
            self.elapsed_timer.start()
        else:
            self.elapsed_timer.stop()
            self._update_elapsed()

    def _update_enabled(self) -> None:
        locked = self.runner.is_running or self._external_busy
        self.run_button.setEnabled(not locked)
        self.incomplete_button.setEnabled(not locked)
        self.dataset_path.setEnabled(not locked)
        self.browse_button.setEnabled(not locked)
        for step in self.steps.values():
            step.checkbox.setEnabled(not locked)
        for control in self.global_controls:
            control.setEnabled(not locked)
        if not locked:
            for key in ("original", "medium", "low"):
                getattr(self, f"dense_{key}_percent").setEnabled(
                    getattr(self, f"dense_{key}").isChecked()
                )

    def _job_finished(self, success: bool, message: str) -> None:
        self.current_stage.setText(message)
        if self.dataset_path.text().strip():
            self.set_dataset_root(self.dataset_path.text())

    def _append_output(self, text: str) -> None:
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _update_elapsed(self) -> None:
        self.elapsed.setText(format_elapsed(self.runner.elapsed_seconds))

    def _artifact_ready(self, path: str) -> None:
        artifact = Path(path)
        if artifact.is_file():
            self._artifact = artifact
            self.latest_button.setEnabled(True)
            self.latest_button.setToolTip(str(artifact))

    def _open_artifact(self) -> None:
        if self._artifact is not None:
            self.open_artifact_requested.emit(str(self._artifact))

    @staticmethod
    def _system_memory_gb() -> float:
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        except (OSError, ValueError):
            return 0.0

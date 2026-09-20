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
    markertag_status,
    stage_output_exists,
    textured_output_for_level,
)
from openreef.ui.theme import WORKFLOW_LEVEL_COLORS, bootstrap_icon

WORKFLOW_GROUPS = (
    (
        "Sparse cloud",
        "Find overlaps and solve camera positions",
        "cloud",
        WORKFLOW_LEVEL_COLORS[0],
        (
            StageKey.FEATURES,
            StageKey.MATCHING,
            StageKey.SPARSE,
            StageKey.MARKERTAGS,
            StageKey.UNDISTORT,
        ),
    ),
    (
        "Dense cloud",
        "Build detailed points and a surface",
        "cloud-fill",
        WORKFLOW_LEVEL_COLORS[2],
        (StageKey.OPENMVS_IMPORT, StageKey.DENSE, StageKey.MESH),
    ),
    (
        "Texture mesh",
        "Project photographs onto the surface",
        "border",
        WORKFLOW_LEVEL_COLORS[3],
        (StageKey.TEXTURE,),
    ),
    (
        "Gaussian splat",
        "Train an optional appearance model",
        "flower2",
        WORKFLOW_LEVEL_COLORS[4],
        (StageKey.GAUSSIAN,),
    ),
)

STAGE_LEVELS = {
    StageKey.FEATURES: 1,
    StageKey.MATCHING: 1,
    StageKey.SPARSE: 1,
    StageKey.MARKERTAGS: 1,
    StageKey.UNDISTORT: 1,
    StageKey.OPENMVS_IMPORT: 3,
    StageKey.DENSE: 3,
    StageKey.MESH: 3,
    StageKey.TEXTURE: 4,
    StageKey.GAUSSIAN: 5,
}


class WorkflowStep(QFrame):
    """One selectable pipeline step with state and progress."""

    clicked = Signal(str)

    def __init__(
        self,
        stage: StageKey,
        level: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.stage = stage
        self.setObjectName("workflowStep")
        if level is not None:
            self.setProperty("level", str(level))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)

        self.checkbox = QCheckBox(STAGE_LABELS[stage])
        self.checkbox.setObjectName("workflowStageCheckbox")
        self.checkbox.setToolTip(f"Expected output: {STAGE_OUTPUTS[stage]}")
        self.checkbox.clicked.connect(lambda: self.clicked.emit(self.stage.value))
        self.status = QLabel("Pending")
        self.status.setObjectName("statusBadge")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        if level is not None:
            self.progress.setProperty("level", str(level))
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.checkbox, 0, 0)
        layout.addWidget(self.status, 0, 1)
        layout.addWidget(self.progress, 1, 0, 1, 2)
        self.detail = QLabel()
        self.detail.setObjectName("datasetSummary")
        self.detail.setWordWrap(True)
        self.detail.setVisible(stage == StageKey.MARKERTAGS)
        layout.addWidget(self.detail, 2, 0, 1, 2)
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
            "attention": "Needs attention",
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
        if self.stage == StageKey.MARKERTAGS:
            self.detail.setText(detail or "Awaiting MarkerTag scan")
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
        number: int,
        title: str,
        subtitle: str,
        icon_name: str,
        accent: str,
        stages: tuple[StageKey, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workflowGroup")
        self.setProperty("level", str(number))
        self.stages = stages
        self.setMinimumWidth(232)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 12)
        layout.setSpacing(9)

        heading = QHBoxLayout()
        number_label = QLabel(str(number))
        number_label.setObjectName("stageNumberBadge")
        number_label.setProperty("level", str(number))
        number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number_label.setFixedSize(28, 28)
        title_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("workflowGroupTitle")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("workflowGroupSubtitle")
        subtitle_label.setWordWrap(True)
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        heading.addWidget(number_label, 0, Qt.AlignmentFlag.AlignTop)
        heading.addLayout(title_box, 1)
        self.status = QLabel("Pending")
        self.status.setObjectName("statusBadge")
        self.status.setProperty("state", "pending")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.hide()
        layout.addLayout(heading)

        self.steps: dict[StageKey, WorkflowStep] = {}
        for stage in stages:
            step = WorkflowStep(stage, number)
            self.steps[stage] = step
            layout.addWidget(step)
        layout.addStretch(1)


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
        elif "attention" in states:
            state, label = "attention", "Needs attention"
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
        self.setProperty("level", "2")
        self.setFixedWidth(176)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 12)
        layout.setSpacing(9)
        heading = QHBoxLayout()
        number = QLabel("2")
        number.setObjectName("stageNumberBadge")
        number.setProperty("level", "2")
        number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number.setFixedSize(28, 28)
        heading.addWidget(number)
        title = QLabel("Crop area")
        title.setObjectName("workflowGroupTitle")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        heading.addWidget(title, 1)
        layout.addLayout(heading)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(
            bootstrap_icon("crosshair", WORKFLOW_LEVEL_COLORS[1], 56).pixmap(42, 42)
        )
        icon.setStyleSheet("background: transparent; border: 0;")
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
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(icon)
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
        self.setProperty("level", "6")
        self.setFixedWidth(176)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 12)
        layout.setSpacing(9)
        heading = QHBoxLayout()
        number = QLabel("6")
        number.setObjectName("stageNumberBadge")
        number.setProperty("level", "6")
        number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number.setFixedSize(28, 28)
        heading.addWidget(number)
        title = QLabel("3D tiles")
        title.setObjectName("workflowGroupTitle")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        heading.addWidget(title, 1)
        layout.addLayout(heading)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(
            bootstrap_icon("box", WORKFLOW_LEVEL_COLORS[5], 64).pixmap(48, 48)
        )
        icon.setStyleSheet("background: transparent; border: 0;")
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
        layout.addWidget(note)
        layout.addStretch(1)
        layout.addWidget(icon)
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
        self.settings_pages: dict[StageKey, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)
        layout.addLayout(self._build_header())
        layout.addWidget(self._build_workflow())
        layout.addLayout(self._build_run_bar())
        layout.addWidget(self._build_details(), 1)
        self._install_explanatory_tooltips()

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

    def _build_header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(8)
        title = QLabel("Process")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        subtitle = QLabel("Configure and run the reconstruction pipeline.")
        subtitle.setObjectName("pageSubtitle")
        header.addWidget(subtitle)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.dataset_path = QLineEdit()
        self.dataset_path.setPlaceholderText("Dataset folder")
        self.dataset_path.setMinimumWidth(380)
        self.dataset_path.editingFinished.connect(self._path_edited)
        self.browse_button = QPushButton("Choose…")
        self.browse_button.clicked.connect(self._choose_folder)
        row.addWidget(self.dataset_path, 1)
        row.addWidget(self.browse_button)
        header.addLayout(row)

        # Retain the summary as internal state for cross-page synchronisation,
        # without adding another line of explanatory text to the header.
        self.dataset_summary = QLabel("No dataset selected")
        self.dataset_summary.hide()
        return header

    def _build_workflow(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # MarkerTags adds a fifth sparse-cloud step; give the workflow enough
        # vertical room to keep every step visible without a nested scrollbar.
        scroll.setFixedHeight(420)
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(10)

        for index, (title, subtitle, icon, accent, stages) in enumerate(WORKFLOW_GROUPS):
            number = 1 if index == 0 else index + 2
            group = WorkflowGroup(number, title, subtitle, icon, accent, stages)
            self.groups.append(group)
            self.steps.update(group.steps)
            row.addWidget(group, 1)
            if index == 0:
                arrow = QLabel("→")
                arrow.setObjectName("workflowArrow")
                arrow.setProperty("level", "2")
                row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignCenter)
                self.crop_checkpoint = CropCheckpoint()
                self.crop_checkpoint.requested.connect(self.crop_requested)
                row.addWidget(self.crop_checkpoint)
                crop_arrow = QLabel("→")
                crop_arrow.setObjectName("workflowArrow")
                crop_arrow.setProperty("level", "3")
                row.addWidget(crop_arrow, 0, Qt.AlignmentFlag.AlignCenter)
            elif index < len(WORKFLOW_GROUPS) - 1:
                arrow = QLabel("→")
                arrow.setObjectName("workflowArrow")
                arrow.setProperty("level", str(number + 1))
                row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignCenter)
        tiles_arrow = QLabel("→")
        tiles_arrow.setObjectName("workflowArrow")
        tiles_arrow.setProperty("level", "6")
        row.addWidget(tiles_arrow, 0, Qt.AlignmentFlag.AlignCenter)
        self.tileset_checkpoint = TilesetCheckpoint()
        self.tileset_checkpoint.requested.connect(self.tileset_requested)
        row.addWidget(self.tileset_checkpoint)
        scroll.setWidget(container)
        return scroll

    def _build_global_options(self) -> QGroupBox:
        """Single-column controls shared by every reconstruction stage."""
        panel = QGroupBox("Output levels")
        panel.setObjectName("globalOptions")
        panel.setMinimumWidth(240)
        layout = QVBoxLayout(panel)
        layout.setSpacing(9)

        # Resource allocation is automatic in the streamlined Process view.
        # Keep the values available to the pipeline without presenting tuning
        # controls that most users should not need to manage.
        available_cores = max(1, os.cpu_count() or 1)
        self.cores = QSpinBox(self)
        self.cores.setRange(1, available_cores)
        self.cores.setValue(max(1, available_cores - 2))
        self.cores.hide()
        self.memory = QDoubleSpinBox(self)
        self.memory.setRange(0, 256)
        self.memory.setDecimals(0)
        self.memory.setSpecialValueText("Unlimited")
        self.memory.hide()
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
        group = QGroupBox("Processing settings")
        self.settings_group = group
        layout = QVBoxLayout(group)

        pages = (
            (StageKey.FEATURES, self._feature_settings()),
            (StageKey.MATCHING, self._matching_settings()),
            (StageKey.SPARSE, self._information_settings(
                "Sparse reconstruction uses automatic resource allocation. "
                "COLMAP estimates camera positions and creates connected sparse models."
            )),
            (StageKey.MARKERTAGS, self._markertag_settings()),
            (StageKey.UNDISTORT, self._undistort_settings()),
            (StageKey.OPENMVS_IMPORT, self._information_settings(
                "OpenMVS imports the selected COLMAP model and any saved crop. "
                "Processing resources are selected automatically."
            )),
            (StageKey.DENSE, self._dense_settings()),
            (StageKey.MESH, self._information_settings(
                "Surface reconstruction uses each selected dense-cloud level and "
                "automatic resource allocation."
            )),
            (StageKey.TEXTURE, self._texture_settings()),
            (StageKey.GAUSSIAN, self._gaussian_settings()),
        )

        settings_grid = QWidget()
        grid = QGridLayout(settings_grid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        column_count = 3
        for index, (stage, page) in enumerate(pages):
            card = QGroupBox(STAGE_LABELS[stage])
            card.setObjectName("settingsCard")
            card.setProperty("level", str(STAGE_LEVELS[stage]))
            card.setMinimumWidth(280)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.addWidget(page)
            row, column = divmod(index, column_count)
            grid.addWidget(card, row, column)
            self.settings_pages[stage] = card
        for column in range(column_count):
            grid.setColumnStretch(column, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(settings_grid)
        layout.addWidget(scroll, 1)
        return group

    def _build_details(self) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        # Build the detailed controls once; MainWindow places this group on the
        # dedicated Settings page instead of embedding it in Process.
        self._build_settings()
        row.addWidget(self._build_global_options(), 1)
        row.addWidget(self._build_marker_options(), 1)
        row.addWidget(self._build_terminal(), 5)
        return panel

    def _build_marker_options(self) -> QGroupBox:
        group = QGroupBox("Markers")
        group.setMinimumWidth(250)
        layout = QVBoxLayout(group)
        form = QFormLayout()
        self.marker_type = QComboBox()
        self.marker_type.addItem("MarkerTags", "markertags")
        form.addRow("Marker type", self.marker_type)
        layout.addLayout(form)
        self.markertag_preview = QLabel("MarkerTags not scanned")
        self.markertag_preview.setObjectName("markerTagDetectedStatus")
        self.markertag_preview.setWordWrap(True)
        layout.addWidget(self.markertag_preview)
        self.markertag_scale = QLabel("No metric scale yet")
        self.markertag_scale.setObjectName("markerTagScaleStatus")
        self.markertag_scale.setWordWrap(True)
        layout.addWidget(self.markertag_scale)
        layout.addStretch(1)
        return group

    def _feature_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.camera_model = QComboBox()
        self.camera_model.addItems(
            ("SIMPLE_RADIAL", "PINHOLE", "OPENCV", "SIMPLE_RADIAL_FISHEYE")
        )
        self.single_camera = QCheckBox("Use one camera for all images")
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

    def _markertag_settings(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.marker_tag_family = QComboBox()
        self.marker_tag_family.addItems(
            ("tag36h11", "tag36h10", "tag25h9", "tag16h5")
        )
        self.marker_tag_size_mm = QDoubleSpinBox()
        self.marker_tag_size_mm.setRange(1.0, 1000.0)
        self.marker_tag_size_mm.setDecimals(1)
        self.marker_tag_size_mm.setValue(50.0)
        self.marker_tag_size_mm.setSuffix(" mm")
        note = QLabel(
            "Non-permanent MarkerTags are triangulated across registered images. "
            "Scale uses only the encoded square edge; the 90 mm disc, 8 mm thickness, "
            "and 0.6 mm raised face are excluded."
        )
        note.setObjectName("datasetSummary")
        note.setWordWrap(True)
        form.addRow(note)
        form.addRow("AprilTag family", self.marker_tag_family)
        form.addRow("Tag edge", self.marker_tag_size_mm)
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
        self.run_button = QPushButton("Run pipeline")
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
        self.overall_progress.setObjectName("workflowOverallProgress")
        self.overall_progress.setFormat("%v of %m checked steps")
        row.addWidget(self.overall_progress, 1)
        self.elapsed = QLabel("00:00")
        row.addWidget(self.elapsed)
        return row

    def _build_terminal(self) -> QGroupBox:
        group = QGroupBox("Live log")
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

    def _install_explanatory_tooltips(self) -> None:
        """Keep dense workflow guidance available on hover instead of in the layout."""
        tooltips = {
            self.marker_type: "MarkerTags currently use AprilTag tag36h11 with a 50 mm tag edge.",
            self.camera_model: "Camera lens model used when COLMAP extracts image features.",
            self.single_camera: "Share one calibration across images captured by the same camera.",
            self.max_image_size: "Maximum image dimension used for feature detection.",
            self.feature_use_gpu: "Use the GPU to accelerate feature extraction when supported.",
            self.overlap: "Number of nearby frames compared during sequential matching.",
            self.matching_use_gpu: "Use the GPU to accelerate feature matching when supported.",
            self.marker_tag_family: "AprilTag family decoded during the MarkerTag scan.",
            self.marker_tag_size_mm: "Physical edge length of the black-and-white encoded square.",
            self.undistort_max_image_size: "Maximum dimension of images prepared for OpenMVS.",
            self.resolution_level: "0 uses full resolution; each higher level halves it.",
            self.max_resolution: "Maximum image dimension used to reconstruct the dense cloud.",
            self.number_views: "Neighbouring camera views considered for each depth estimate.",
            self.fusion_views: "Views that must agree before a dense point is retained.",
            self.estimate_colors: "Transfer image colour estimates onto dense points.",
            self.estimate_normals: "Estimate local surface directions for dense points.",
            self.texture_resolution_level: "Image downsampling used while building textures.",
            self.max_texture_size: "Maximum width or height of the generated texture atlas.",
            self.texture_sharpness: "Texture sharpening strength; 0 disables sharpening.",
            self.global_seam_leveling: "Balance brightness and colour between texture patches.",
            self.local_seam_leveling: "Blend local boundaries between neighbouring patches.",
            self.gaussian_executable: "Path to the OpenSplat executable used for training.",
            self.gaussian_preset: "Apply a coordinated set of Gaussian training settings.",
            self.gaussian_iterations: "Number of optimisation steps used to train the splat.",
            self.gaussian_downscale: "Reduce training image size to lower memory use.",
            self.gaussian_max_points: "Maximum number of Gaussian splats retained.",
            self.gaussian_save_every: "Training interval between saved checkpoints.",
            self.gaussian_resume: "Continue from the newest compatible checkpoint if present.",
            self.gaussian_low_memory: "Reduce peak memory use at the cost of speed.",
            self.gaussian_cpu: "Run Gaussian training on the CPU when GPU use is unavailable.",
            self.gaussian_center: "Centre the splat output, changing shared model coordinates.",
            self.run_button: "Run every pipeline step currently selected above.",
            self.incomplete_button: "Select only steps whose expected outputs are missing.",
            self.cancel_button: "Stop after safely terminating the active processing command.",
            self.latest_button: "Open the newest model produced by this dataset.",
        }
        for widget, explanation in tooltips.items():
            widget.setToolTip(explanation)

        for checkbox, explanation in (
            (self.dense_original, "Build the full-resolution dense, mesh, and texture outputs."),
            (self.dense_medium, "Also build a lighter output using the selected percentage."),
            (self.dense_low, "Also build a small preview output using the selected percentage."),
        ):
            checkbox.setToolTip(explanation)

    def _update_markertag_panel(self, detail: str) -> None:
        """Show a prominent detection result and separate scale diagnostics."""
        parts = [part.strip() for part in detail.split("·") if part.strip()]
        first = parts[0] if parts else "Not scanned"
        count = 0
        if first.startswith("MarkerTags detected:"):
            try:
                count = int(first.rsplit(":", 1)[1].strip())
            except ValueError:
                count = 0

        detected = count > 0
        if detected:
            headline = f"✓ MarkerTags detected · {count}"
        elif first == "Not scanned":
            headline = "MarkerTags not scanned"
        else:
            headline = "MarkerTags not detected"

        self.markertag_preview.setText(headline)
        self.markertag_preview.setProperty("detected", detected)
        self.markertag_preview.style().unpolish(self.markertag_preview)
        self.markertag_preview.style().polish(self.markertag_preview)
        self.markertag_scale.setText(
            " · ".join(parts[1:]) if len(parts) > 1 else "No metric scale yet"
        )

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
            marker_tag_family=self.marker_tag_family.currentText(),
            marker_tag_size_m=self.marker_tag_size_mm.value() / 1000.0,
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
            self._update_markertag_panel("Not scanned")
            self.tileset_checkpoint.set_available(False, False)
            return
        layout = DatasetLayout.from_path(value)
        self.dataset_summary.setText(f"{layout.image_count():,} images · {layout.root.name}")
        options = self.selected_options()
        for stage, step in self.steps.items():
            complete = stage_output_exists(stage, layout, options)
            detail = markertag_status(layout) if stage == StageKey.MARKERTAGS else None
            state = "complete" if complete else "pending"
            if stage == StageKey.MARKERTAGS and detail and "Unscaled" in detail:
                state = "attention"
            step.set_state(state, detail)
            if stage == StageKey.MARKERTAGS:
                self._update_markertag_panel(detail or "Not scanned")
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
            if step.stage == StageKey.MARKERTAGS and state == "complete":
                value = self.dataset_path.text().strip()
                if value:
                    detail = markertag_status(DatasetLayout.from_path(value))
                    if "Unscaled" in detail:
                        state = "attention"
            if step.stage == StageKey.MARKERTAGS:
                self._update_markertag_panel(detail or state.title())
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

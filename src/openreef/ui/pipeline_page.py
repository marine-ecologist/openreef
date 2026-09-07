"""Pipeline tabs with stage selection, resource controls, and live terminal output."""

from __future__ import annotations

import os
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
    DENSE_STAGES,
    GENERATE_STAGES,
    STAGE_LABELS,
    STAGE_OUTPUTS,
    DatasetLayout,
    PipelineOptions,
    StageKey,
    stage_output_exists,
)


class StageCard(QFrame):
    def __init__(self, stage: StageKey, number: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stage = stage
        self.setObjectName("stageCard")
        self.setMinimumWidth(190)

        layout = QVBoxLayout(self)
        heading = QHBoxLayout()
        index = QLabel(f"{number:02d}")
        index.setObjectName("stageNumber")
        self.checkbox = QCheckBox(STAGE_LABELS[stage])
        self.checkbox.setChecked(True)
        heading.addWidget(index)
        heading.addWidget(self.checkbox, 1)
        layout.addLayout(heading)

        output = QLabel(STAGE_OUTPUTS[stage])
        output.setObjectName("stageOutput")
        output.setWordWrap(True)
        layout.addWidget(output)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.status = QLabel("Waiting")
        self.status.setObjectName("stageStatus")
        layout.addWidget(self.status)

    def set_status(self, state: str, detail: str) -> None:
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)
        if state == "running":
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 1)
            self.progress.setValue(1 if state in ("complete", "ready") else 0)
        self.status.setText(detail)


class PipelinePage(QWidget):
    dataset_path_changed = Signal(str)
    open_artifact_requested = Signal(str)

    def __init__(
        self,
        page_kind: str,
        runner: PipelineRunner,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.page_kind = page_kind
        self.runner = runner
        self.stages = GENERATE_STAGES if page_kind == "generate" else DENSE_STAGES
        self.cards: dict[StageKey, StageCard] = {}
        self._artifact_path: Path | None = None
        self._external_busy = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addLayout(self._build_header())
        layout.addWidget(self._build_stages())
        if self.page_kind == "dense":
            option_row = QHBoxLayout()
            option_row.addWidget(self._build_output_levels())
            option_row.addWidget(self._build_options(), 1)
            layout.addLayout(option_row)
        else:
            layout.addWidget(self._build_options())
        layout.addLayout(self._build_run_bar())
        layout.addWidget(self._build_terminal(), 1)

        self.runner.output_received.connect(self._append_output)
        self.runner.stage_changed.connect(self._stage_changed)
        self.runner.current_stage_changed.connect(self._current_stage_changed)
        self.runner.progress_changed.connect(self._progress_changed)
        self.runner.running_changed.connect(self._running_changed)
        self.runner.job_finished.connect(self._job_finished)
        self.runner.artifact_ready.connect(self._artifact_ready)

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(1000)
        self.elapsed_timer.timeout.connect(self._update_elapsed)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        titles = {
            "generate": (
                "Sparse Cloud",
                "Build the COLMAP sparse cloud and camera solution, then prepare PINHOLE images.",
            ),
            "dense": (
                "Dense Cloud",
                "Import the sparse model into OpenMVS, then generate a dense cloud and mesh.",
            ),
        }
        title, subtitle = titles[self.page_kind]
        title_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header.addLayout(title_box, 1)

        folder_box = QVBoxLayout()
        folder_label = QLabel("DATASET FOLDER")
        folder_label.setObjectName("fieldLabel")
        folder_row = QHBoxLayout()
        self.dataset_path = QLineEdit()
        self.dataset_path.setPlaceholderText("Choose a folder containing images/")
        self.dataset_path.setMinimumWidth(380)
        self.dataset_path.editingFinished.connect(self._path_edited)
        self.browse_button = QPushButton("Choose…")
        self.browse_button.clicked.connect(self._choose_folder)
        folder_row.addWidget(self.dataset_path, 1)
        folder_row.addWidget(self.browse_button)
        self.dataset_summary = QLabel("No dataset selected")
        self.dataset_summary.setObjectName("datasetSummary")
        folder_box.addWidget(folder_label)
        folder_box.addLayout(folder_row)
        folder_box.addWidget(self.dataset_summary)
        header.addLayout(folder_box, 2)
        return header

    def _build_stages(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(148)
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(2, 2, 2, 2)
        for index, stage in enumerate(self.stages, start=1):
            card = StageCard(stage, index)
            self.cards[stage] = card
            row.addWidget(card, 1)
            if index < len(self.stages):
                arrow = QLabel("→")
                arrow.setObjectName("flowArrow")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row.addWidget(arrow)
        scroll.setWidget(container)
        return scroll

    def _build_options(self) -> QGroupBox:
        group = QGroupBox("Processing options")
        grid = QGridLayout(group)
        available_cores = max(1, os.cpu_count() or 1)

        self.cores = QSpinBox()
        self.cores.setRange(1, available_cores)
        self.cores.setValue(max(1, available_cores - 2))
        self.cores.setSuffix(" cores")
        self.cores.setToolTip("Maximum worker threads passed to COLMAP and OpenMVS.")

        self.memory = QDoubleSpinBox()
        self.memory.setRange(0, 256)
        self.memory.setDecimals(0)
        self.memory.setValue(0)
        self.memory.setSpecialValueText("Unlimited")
        self.memory.setSuffix(" GB")
        self.memory.setToolTip(
            "Optional hard process memory ceiling. Leave unlimited unless competing "
            "workloads need it."
        )

        if self.page_kind == "generate":
            self.camera_model = QComboBox()
            self.camera_model.addItems(
                ("SIMPLE_RADIAL", "PINHOLE", "OPENCV", "SIMPLE_RADIAL_FISHEYE")
            )
            self.single_camera = QCheckBox("Treat all images as one camera")
            self.single_camera.setChecked(True)
            self.use_gpu = QCheckBox("Use GPU for features and matching")
            self.use_gpu.setChecked(True)
            self.max_image_size = QSpinBox()
            self.max_image_size.setRange(640, 16384)
            self.max_image_size.setSingleStep(256)
            self.max_image_size.setValue(3200)
            self.max_image_size.setSuffix(" px")
            self.overlap = QSpinBox()
            self.overlap.setRange(2, 100)
            self.overlap.setValue(10)
            form_left = QFormLayout()
            form_left.addRow("CPU budget", self.cores)
            form_left.addRow("RAM limit", self.memory)
            form_left.addRow("Camera model", self.camera_model)
            form_right = QFormLayout()
            form_right.addRow("Max image size", self.max_image_size)
            form_right.addRow("Sequence overlap", self.overlap)
            form_right.addRow(self.single_camera)
            form_right.addRow(self.use_gpu)
        else:
            self.resolution_level = QSpinBox()
            self.resolution_level.setRange(0, 4)
            self.resolution_level.setValue(1)
            self.resolution_level.setToolTip("0 uses full resolution; each higher level halves it.")
            self.max_resolution = QSpinBox()
            self.max_resolution.setRange(640, 16384)
            self.max_resolution.setSingleStep(256)
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
            form_left = QFormLayout()
            form_left.addRow("CPU budget", self.cores)
            form_left.addRow("RAM limit", self.memory)
            form_left.addRow("Resolution level", self.resolution_level)
            form_right = QFormLayout()
            form_right.addRow("Max resolution", self.max_resolution)
            form_right.addRow("Neighbor views", self.number_views)
            form_right.addRow("Fusion agreement", self.fusion_views)
            form_right.addRow(self.estimate_colors)
            form_right.addRow(self.estimate_normals)

        grid.addLayout(form_left, 0, 0)
        grid.addLayout(form_right, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return group

    def _build_output_levels(self) -> QGroupBox:
        group = QGroupBox("Output levels")
        group.setMinimumWidth(280)
        grid = QGridLayout(group)
        grid.addWidget(QLabel("CREATE"), 0, 0)
        grid.addWidget(QLabel("POINTS RETAINED"), 0, 1)

        rows = (
            ("original", "Original", 100, True),
            ("medium", "Medium", 20, False),
            ("low", "Low", 5, False),
        )
        for row, (key, label, percentage, selected) in enumerate(rows, start=1):
            checkbox = QCheckBox(label)
            checkbox.setChecked(selected)
            amount = QSpinBox()
            amount.setRange(1, 100)
            amount.setValue(percentage)
            amount.setSuffix(" %")
            amount.setEnabled(selected)
            checkbox.toggled.connect(amount.setEnabled)
            checkbox.setToolTip(
                "Selected levels are generated as dense clouds and passed into Surface mesh."
            )
            setattr(self, f"dense_{key}", checkbox)
            setattr(self, f"dense_{key}_percent", amount)
            grid.addWidget(checkbox, row, 0)
            grid.addWidget(amount, row, 1)
        return group

    def _build_run_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.run_button = QPushButton("Run selected stages")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self._start_run)
        self.cancel_button = QPushButton("Stop")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.runner.cancel)
        row.addWidget(self.run_button)
        row.addWidget(self.cancel_button)

        self.current_stage = QLabel("Idle")
        self.current_stage.setObjectName("currentStage")
        row.addWidget(self.current_stage)
        self.overall_progress = QProgressBar()
        self.overall_progress.setFormat("%v of %m stages")
        self.overall_progress.setRange(0, len(self.stages))
        self.overall_progress.setValue(0)
        row.addWidget(self.overall_progress, 1)
        self.elapsed = QLabel("00:00")
        self.elapsed.setMinimumWidth(55)
        row.addWidget(self.elapsed)

        self.open_artifact = QPushButton("Open latest model in Viewer")
        self.open_artifact.setVisible(self.page_kind == "dense")
        self.open_artifact.setEnabled(False)
        self.open_artifact.clicked.connect(self._open_artifact)
        row.addWidget(self.open_artifact)
        return row

    def _build_terminal(self) -> QGroupBox:
        group = QGroupBox("Live terminal")
        layout = QVBoxLayout(group)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumBlockCount(5000)
        self.terminal.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.terminal.setPlaceholderText("Process output will appear here in real time.")

        terminal_toolbar = QHBoxLayout()
        hint = QLabel("Streaming process output — Viewer remains available while this runs")
        hint.setObjectName("terminalHint")
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.terminal.clear)
        terminal_toolbar.addWidget(hint, 1)
        terminal_toolbar.addWidget(clear_button)
        layout.addLayout(terminal_toolbar)
        layout.addWidget(self.terminal)
        return group

    def selected_options(self) -> PipelineOptions:
        common = {
            "cores": self.cores.value(),
            "memory_gb": self.memory.value(),
        }
        if self.page_kind == "generate":
            return PipelineOptions(
                **common,
                use_gpu=self.use_gpu.isChecked(),
                camera_model=self.camera_model.currentText(),
                single_camera=self.single_camera.isChecked(),
                max_image_size=self.max_image_size.value(),
                sequential_overlap=self.overlap.value(),
            )
        return PipelineOptions(
            **common,
            resolution_level=self.resolution_level.value(),
            max_resolution=self.max_resolution.value(),
            number_views=self.number_views.value(),
            number_views_fuse=self.fusion_views.value(),
            estimate_colors=self.estimate_colors.isChecked(),
            estimate_normals=self.estimate_normals.isChecked(),
            dense_original=self.dense_original.isChecked(),
            dense_low=self.dense_low.isChecked(),
            dense_medium=self.dense_medium.isChecked(),
            dense_original_percent=self.dense_original_percent.value(),
            dense_medium_percent=self.dense_medium_percent.value(),
            dense_low_percent=self.dense_low_percent.value(),
        )

    def set_external_busy(self, busy: bool) -> None:
        self._external_busy = busy
        self._update_enabled()

    def set_dataset_root(self, path: str | Path) -> None:
        value = str(Path(path).expanduser().resolve()) if str(path).strip() else ""
        self.dataset_path.blockSignals(True)
        self.dataset_path.setText(value)
        self.dataset_path.blockSignals(False)
        if not value:
            self.dataset_summary.setText("No dataset selected")
            return
        layout = DatasetLayout.from_path(value)
        count = layout.image_count()
        self.dataset_summary.setText(f"{count:,} images found in {layout.images}")
        for stage, card in self.cards.items():
            if stage_output_exists(stage, layout):
                card.set_status("ready", "Existing output found")
            else:
                card.set_status("waiting", "Waiting")
        if self.page_kind == "dense" and layout.dense_cloud.is_file():
            self._artifact_ready(str(layout.dense_cloud))

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

    def _start_run(self) -> None:
        stages = [stage for stage, card in self.cards.items() if card.checkbox.isChecked()]
        self.runner.run(self.dataset_path.text(), stages, self.selected_options())

    def _append_output(self, text: str) -> None:
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _stage_changed(self, key: str, state: str, detail: str) -> None:
        try:
            stage = StageKey(key)
        except ValueError:
            return
        card = self.cards.get(stage)
        if card:
            card.set_status(state, detail)

    def _current_stage_changed(self, label: str) -> None:
        self.current_stage.setText(label)

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
        self.dataset_path.setEnabled(not locked)
        self.browse_button.setEnabled(not locked)
        for card in self.cards.values():
            card.checkbox.setEnabled(not locked)

    def _job_finished(self, success: bool, message: str) -> None:
        self.current_stage.setText(message)
        self.current_stage.setProperty("success", success)

    def _update_elapsed(self) -> None:
        self.elapsed.setText(format_elapsed(self.runner.elapsed_seconds))

    def _artifact_ready(self, path: str) -> None:
        artifact = Path(path)
        if artifact.is_file():
            self._artifact_path = artifact
            self.open_artifact.setEnabled(True)
            self.open_artifact.setToolTip(str(artifact))

    def _open_artifact(self) -> None:
        if self._artifact_path:
            self.open_artifact_requested.emit(str(self._artifact_path))

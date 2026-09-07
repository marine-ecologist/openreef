"""Input image and video ingestion, preview, and color-correction UI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QFontDatabase, QIcon, QImageReader, QPixmap, QTextCursor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from openreef.pipeline.input_runner import InputJob, InputRunner
from openreef.pipeline.stages import IMAGE_EXTENSIONS, DatasetLayout

VIDEO_FILTER = "Video files (*.mp4 *.mov *.m4v *.avi *.mkv *.mts *.m2ts *.webm)"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mts", ".m2ts", ".webm"}


class InputImagesPage(QWidget):
    dataset_path_changed = Signal(str)
    images_ready = Signal(str)

    def __init__(self, runner: InputRunner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.runner = runner
        self._source: Path | None = None
        self._preview_path: Path | None = None
        self._pipeline_busy = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addLayout(self._build_header())

        content = QSplitter(Qt.Orientation.Horizontal)
        content.addWidget(self._build_settings())
        content.addWidget(self._build_preview())
        content.setStretchFactor(0, 0)
        content.setStretchFactor(1, 1)
        content.setSizes([360, 1000])
        layout.addWidget(content, 3)
        layout.addWidget(self._build_terminal(), 2)

        self.runner.output_received.connect(self._append_output)
        self.runner.phase_changed.connect(self.phase_label.setText)
        self.runner.progress_changed.connect(self._set_progress)
        self.runner.running_changed.connect(self._running_changed)
        self.runner.job_finished.connect(self._job_finished)
        self.runner.images_ready.connect(self._images_ready)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Input Images")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Review source media, preserve originals, and prepare the images sent to COLMAP."
        )
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        dataset_box = QVBoxLayout()
        label = QLabel("DATASET FOLDER")
        label.setObjectName("fieldLabel")
        row = QHBoxLayout()
        self.dataset_path = QLineEdit()
        self.dataset_path.setPlaceholderText("Choose the dataset output folder")
        self.dataset_path.setMinimumWidth(420)
        self.dataset_path.editingFinished.connect(self._dataset_edited)
        self.dataset_button = QPushButton("Choose…")
        self.dataset_button.clicked.connect(self._choose_dataset)
        row.addWidget(self.dataset_path, 1)
        row.addWidget(self.dataset_button)
        self.folder_contract = QLabel("original/ → optional color correction → images/ → COLMAP")
        self.folder_contract.setObjectName("datasetSummary")
        dataset_box.addWidget(label)
        dataset_box.addLayout(row)
        dataset_box.addWidget(self.folder_contract)
        header.addLayout(dataset_box, 2)
        return header

    def _build_settings(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(420)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 12, 0)

        source_group = QGroupBox("Source")
        source_form = QFormLayout(source_group)
        self.source_kind = QComboBox()
        self.source_kind.addItem("Existing dataset images", "existing")
        self.source_kind.addItem("Photo folder", "photos")
        self.source_kind.addItem("Video file", "video")
        self.source_kind.currentIndexChanged.connect(self._source_kind_changed)
        source_form.addRow("Input type", self.source_kind)
        self.source_path = QLineEdit()
        self.source_path.setReadOnly(True)
        self.source_path.setPlaceholderText("No source selected")
        source_form.addRow("Selected", self.source_path)
        self.source_button = QPushButton("Use dataset images")
        self.source_button.clicked.connect(self._choose_source)
        source_form.addRow(self.source_button)
        layout.addWidget(source_group)

        options_group = QGroupBox("Preparation")
        options_form = QFormLayout(options_group)
        self.video_interval = QDoubleSpinBox()
        self.video_interval.setRange(0.1, 60.0)
        self.video_interval.setDecimals(1)
        self.video_interval.setValue(1.0)
        self.video_interval.setSuffix(" seconds")
        self.video_interval.setEnabled(False)
        self.video_interval.setToolTip("Time between extracted video frames.")
        options_form.addRow("Sample every", self.video_interval)
        self.color_correct = QCheckBox("Apply conservative underwater color correction")
        self.color_correct.setChecked(False)
        self.color_correct.setToolTip(
            "Red compensation, gray-world balance, luminance CLAHE, gamma, and mild sharpening."
        )
        options_form.addRow(self.color_correct)
        self.jpeg_quality = QSpinBox()
        self.jpeg_quality.setRange(80, 100)
        self.jpeg_quality.setValue(98)
        self.jpeg_quality.setSuffix("%")
        options_form.addRow("JPEG quality", self.jpeg_quality)
        layout.addWidget(options_group)

        note = QLabel(
            "Original photos and extracted video frames are preserved under original/. "
            "Sparse Cloud always reads images/. Existing images are adopted safely before rebuild."
        )
        note.setObjectName("pageSubtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.prepare_button = QPushButton("Prepare Input Images")
        self.prepare_button.setObjectName("primaryButton")
        self.prepare_button.clicked.connect(self._prepare)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.runner.stop)
        action_row = QHBoxLayout()
        action_row.addWidget(self.prepare_button, 1)
        action_row.addWidget(self.stop_button)
        layout.addLayout(action_row)

        self.phase_label = QLabel("Ready")
        self.phase_label.setObjectName("currentStage")
        self.phase_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.phase_label)
        layout.addWidget(self.progress)
        layout.addStretch(1)
        return panel

    def _build_preview(self) -> QGroupBox:
        group = QGroupBox("Media preview")
        layout = QVBoxLayout(group)
        self.preview_stack = QStackedWidget()

        photo_panel = QSplitter(Qt.Orientation.Horizontal)
        self.photo_list = QListWidget()
        self.photo_list.setViewMode(QListView.ViewMode.IconMode)
        self.photo_list.setIconSize(QSize(128, 84))
        self.photo_list.setGridSize(QSize(154, 116))
        self.photo_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.photo_list.currentItemChanged.connect(self._photo_selected)
        self.photo_preview = QLabel(
            "Choose a photo folder or prepare the dataset to preview images."
        )
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setMinimumSize(440, 300)
        self.photo_preview.setWordWrap(True)
        self.photo_preview.setObjectName("mediaPreview")
        photo_panel.addWidget(self.photo_list)
        photo_panel.addWidget(self.photo_preview)
        photo_panel.setStretchFactor(0, 1)
        photo_panel.setStretchFactor(1, 2)
        self.preview_stack.addWidget(photo_panel)

        video_panel = QWidget()
        video_layout = QVBoxLayout(video_panel)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(340)
        video_layout.addWidget(self.video_widget, 1)
        video_controls = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_video)
        self.video_position = QSlider(Qt.Orientation.Horizontal)
        self.video_position.setRange(0, 0)
        self.video_position.sliderMoved.connect(self.player_set_position)
        self.video_time = QLabel("00:00 / 00:00")
        video_controls.addWidget(self.play_button)
        video_controls.addWidget(self.video_position, 1)
        video_controls.addWidget(self.video_time)
        video_layout.addLayout(video_controls)
        self.preview_stack.addWidget(video_panel)

        self.audio_output = QAudioOutput(self)
        self.audio_output.setMuted(True)
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self._video_position_changed)
        self.media_player.durationChanged.connect(self._video_duration_changed)
        self.media_player.playbackStateChanged.connect(self._video_state_changed)

        layout.addWidget(self.preview_stack)
        self.preview_summary = QLabel("No media selected")
        self.preview_summary.setObjectName("datasetSummary")
        layout.addWidget(self.preview_summary)
        return group

    def _build_terminal(self) -> QGroupBox:
        group = QGroupBox("Input processing terminal")
        layout = QVBoxLayout(group)
        toolbar = QHBoxLayout()
        hint = QLabel("FFmpeg extraction and image preparation output")
        hint.setObjectName("terminalHint")
        clear = QPushButton("Clear")
        toolbar.addWidget(hint, 1)
        toolbar.addWidget(clear)
        layout.addLayout(toolbar)
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumBlockCount(5000)
        self.terminal.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        clear.clicked.connect(self.terminal.clear)
        layout.addWidget(self.terminal)
        return group

    def set_dataset_root(self, path: str | Path) -> None:
        if not str(path).strip():
            return
        root = Path(path).expanduser().resolve()
        self.dataset_path.blockSignals(True)
        self.dataset_path.setText(str(root))
        self.dataset_path.blockSignals(False)
        layout = DatasetLayout(root)
        if self.source_kind.currentData() == "existing" or self._source is None:
            source = layout.images if layout.images.is_dir() else layout.original
            self._set_source(source)
        else:
            preview = layout.images if layout.images.is_dir() else layout.original
            self._load_photos(preview)

    def set_pipeline_busy(self, busy: bool) -> None:
        self._pipeline_busy = busy
        self._update_enabled()

    def _choose_dataset(self) -> None:
        start = self.dataset_path.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose OpenReef dataset", start)
        if selected:
            self.set_dataset_root(selected)
            self.dataset_path_changed.emit(selected)

    def _dataset_edited(self) -> None:
        value = self.dataset_path.text().strip()
        self.set_dataset_root(value)
        self.dataset_path_changed.emit(value)

    def _source_kind_changed(self) -> None:
        kind = self.source_kind.currentData()
        self.video_interval.setEnabled(kind == "video")
        labels = {
            "existing": "Use dataset images",
            "photos": "Choose photo folder…",
            "video": "Choose video…",
        }
        self.source_button.setText(labels[kind])
        if kind == "existing":
            root = Path(self.dataset_path.text()) if self.dataset_path.text() else None
            if root:
                layout = DatasetLayout(root)
                self._set_source(layout.images if layout.images.is_dir() else layout.original)
        else:
            self._source = None
            self.source_path.clear()

    def _choose_source(self) -> None:
        kind = self.source_kind.currentData()
        if kind == "existing":
            if not self.dataset_path.text():
                self.phase_label.setText("Choose a dataset first")
                return
            layout = DatasetLayout.from_path(self.dataset_path.text())
            self._set_source(layout.images if layout.images.is_dir() else layout.original)
        elif kind == "photos":
            selected = QFileDialog.getExistingDirectory(
                self, "Choose source photo folder", str(Path.home())
            )
            if selected:
                self._set_source(Path(selected))
        else:
            selected, _ = QFileDialog.getOpenFileName(
                self, "Choose source video", str(Path.home()), VIDEO_FILTER
            )
            if selected:
                self._set_source(Path(selected))

    def _set_source(self, path: Path) -> None:
        self._source = path
        self.source_path.setText(str(path))
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            self.preview_stack.setCurrentIndex(1)
            self.media_player.setSource(QUrl.fromLocalFile(str(path)))
            self.preview_summary.setText(path.name)
        else:
            self.media_player.stop()
            self.preview_stack.setCurrentIndex(0)
            self._load_photos(path)

    def _load_photos(self, folder: Path) -> None:
        self.photo_list.clear()
        if not folder.is_dir():
            self.preview_summary.setText("No image folder available")
            return
        files = sorted(
            path
            for path in folder.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        shown = files[:300]
        for path in shown:
            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            reader.setScaledSize(QSize(128, 84))
            image = reader.read()
            item = QListWidgetItem(QIcon(QPixmap.fromImage(image)), path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.photo_list.addItem(item)
        suffix = f" (showing first {len(shown):,})" if len(files) > len(shown) else ""
        self.preview_summary.setText(f"{len(files):,} images in {folder}{suffix}")
        if self.photo_list.count():
            self.photo_list.setCurrentRow(0)

    def _photo_selected(self, current: QListWidgetItem | None) -> None:
        if current is None:
            return
        self._preview_path = Path(current.data(Qt.ItemDataRole.UserRole))
        pixmap = QPixmap(str(self._preview_path))
        if pixmap.isNull():
            self.photo_preview.setText(f"Could not preview {self._preview_path.name}")
            return
        target = self.photo_preview.size() - QSize(20, 20)
        self.photo_preview.setPixmap(
            pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _prepare(self) -> None:
        if not self.dataset_path.text() or self._source is None:
            self.phase_label.setText("Choose a dataset and input source first")
            return
        source_kind = str(self.source_kind.currentData())
        if source_kind == "existing" and self._source.name == "original":
            source_kind = "photos"
        job = InputJob(
            dataset=Path(self.dataset_path.text()).expanduser().resolve(),
            source_kind=source_kind,
            source=self._source,
            interval=self.video_interval.value(),
            color_correct=self.color_correct.isChecked(),
            jpeg_quality=self.jpeg_quality.value(),
        )
        self.runner.start(job)

    def _set_progress(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
            self.progress.setFormat("%v / %m")

    def _running_changed(self, running: bool) -> None:
        self.stop_button.setEnabled(running)
        self._update_enabled()

    def _update_enabled(self) -> None:
        locked = self.runner.is_running or self._pipeline_busy
        self.prepare_button.setEnabled(not locked)
        self.dataset_path.setEnabled(not locked)
        self.dataset_button.setEnabled(not locked)
        self.source_kind.setEnabled(not locked)
        self.source_button.setEnabled(not locked)

    def _job_finished(self, success: bool, message: str) -> None:
        if not success:
            self.phase_label.setText(message)

    def _images_ready(self, images: str) -> None:
        folder = Path(images)
        self._set_source(folder)
        self.source_kind.setCurrentIndex(0)
        self.images_ready.emit(str(folder.parent))

    def _append_output(self, text: str) -> None:
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _toggle_video(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def player_set_position(self, position: int) -> None:
        self.media_player.setPosition(position)

    def _video_position_changed(self, position: int) -> None:
        if not self.video_position.isSliderDown():
            self.video_position.setValue(position)
        self._update_video_time(position, self.media_player.duration())

    def _video_duration_changed(self, duration: int) -> None:
        self.video_position.setRange(0, duration)
        self._update_video_time(self.media_player.position(), duration)

    def _video_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.setText(
            "Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "Play"
        )

    def _update_video_time(self, position: int, duration: int) -> None:
        self.video_time.setText(
            f"{_format_milliseconds(position)} / {_format_milliseconds(duration)}"
        )


def _format_milliseconds(value: int) -> str:
    seconds = max(0, value // 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

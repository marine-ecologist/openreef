"""Viewer side-panel controls."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from openreef.core.scene import DISPLAY_MODES


class ViewerControls(QWidget):
    open_requested = Signal()
    save_requested = Signal()
    fit_requested = Signal()
    projection_changed = Signal(bool)
    display_mode_changed = Signal(str)
    point_size_changed = Signal(int)
    standard_view_requested = Signal(str)
    lasso_requested = Signal(str)
    undo_requested = Signal()
    reset_requested = Signal()
    complexity_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("OPENREEF")
        heading.setObjectName("heading")
        subtitle = QLabel("Viewer 0.2")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        file_row = QHBoxLayout()
        self.open_button = QPushButton("Open model…")
        self.open_button.setObjectName("primaryButton")
        self.open_button.clicked.connect(self.open_requested)
        self.save_button = QPushButton("Save as…")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_requested)
        file_row.addWidget(self.open_button, 1)
        file_row.addWidget(self.save_button, 1)
        layout.addLayout(file_row)

        view_group = QGroupBox("View")
        view_layout = QVBoxLayout(view_group)
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
            view_grid.addWidget(button, index // 2, index % 2)
        view_layout.addLayout(view_grid)
        layout.addWidget(view_group)

        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        self.display_mode = QComboBox()
        self.display_mode.addItems(DISPLAY_MODES)
        self.display_mode.setCurrentText("Wireframe")
        self.display_mode.currentTextChanged.connect(self.display_mode_changed)
        display_layout.addRow("Mesh mode", self.display_mode)

        point_size_container = QWidget()
        point_size_layout = QGridLayout(point_size_container)
        point_size_layout.setContentsMargins(0, 0, 0, 0)
        self.point_size = QSlider()
        self.point_size.setOrientation(Qt.Orientation.Horizontal)
        self.point_size.setRange(1, 20)
        self.point_size.setValue(5)
        self.point_size_value = QLabel("5 px")
        self.point_size.valueChanged.connect(self._on_point_size_changed)
        point_size_layout.addWidget(self.point_size, 0, 0)
        point_size_layout.addWidget(self.point_size_value, 0, 1)
        display_layout.addRow("Point size", point_size_container)
        layout.addWidget(display_group)

        edit_group = QGroupBox("Crop and mesh complexity")
        edit_layout = QVBoxLayout(edit_group)
        complexity_row = QGridLayout()
        self.complexity = QSlider(Qt.Orientation.Horizontal)
        self.complexity.setRange(5, 100)
        self.complexity.setValue(100)
        self.complexity.setSingleStep(5)
        self.complexity.setPageStep(10)
        self.complexity.setEnabled(False)
        self.complexity.valueChanged.connect(self._complexity_value_changed)
        self.complexity.sliderReleased.connect(self._request_complexity)
        self.complexity_value = QLabel("100%")
        complexity_row.addWidget(QLabel("Mesh complexity"), 0, 0)
        complexity_row.addWidget(self.complexity, 1, 0)
        complexity_row.addWidget(self.complexity_value, 1, 1)
        edit_layout.addLayout(complexity_row)

        self.operation = QComboBox()
        self.operation.addItem("Keep inside lasso", "keep")
        self.operation.addItem("Delete inside lasso", "delete")
        edit_layout.addWidget(self.operation)
        self.draw_button = QPushButton("Draw lasso")
        self.draw_button.setEnabled(False)
        self.draw_button.clicked.connect(self._request_lasso)
        edit_layout.addWidget(self.draw_button)
        history_row = QHBoxLayout()
        self.undo_button = QPushButton("Undo")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_requested)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.reset_requested)
        history_row.addWidget(self.undo_button)
        history_row.addWidget(self.reset_button)
        edit_layout.addLayout(history_row)
        self.edit_status = QLabel("Open a model to enable editing.")
        self.edit_status.setObjectName("pageSubtitle")
        self.edit_status.setWordWrap(True)
        edit_layout.addWidget(self.edit_status)
        layout.addWidget(edit_group)

        stats_group = QGroupBox("Model statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats = QTextEdit()
        self.stats.setReadOnly(True)
        self.stats.setMinimumHeight(150)
        self.stats.setPlainText("No model loaded")
        stats_layout.addWidget(self.stats)
        layout.addWidget(stats_group, 1)

    def set_stats(self, text: str) -> None:
        self.stats.setPlainText(text)

    def set_model_available(self, available: bool, description: str = "") -> None:
        self.save_button.setEnabled(available)
        self.draw_button.setEnabled(available)
        if available:
            self.edit_status.setText(description or "Ready to edit.")
        else:
            self.edit_status.setText("Open a model to enable editing.")

    def set_mesh_available(self, available: bool) -> None:
        self.complexity.setEnabled(available)
        self.complexity.setToolTip(
            "Release the slider to build a non-destructive simplified mesh."
            if available
            else "Mesh complexity is available for triangle meshes, not point clouds."
        )

    def set_history_available(self, available: bool) -> None:
        self.undo_button.setEnabled(available)
        self.reset_button.setEnabled(available)

    def set_edit_status(self, message: str) -> None:
        self.edit_status.setText(message)

    def set_complexity(self, percent: int) -> None:
        self.complexity.blockSignals(True)
        self.complexity.setValue(percent)
        self.complexity.blockSignals(False)
        self.complexity_value.setText(f"{percent}%")

    def _on_point_size_changed(self, value: int) -> None:
        self.point_size_value.setText(f"{value} px")
        self.point_size_changed.emit(value)

    def _complexity_value_changed(self, value: int) -> None:
        self.complexity_value.setText(f"{value}%")

    def _request_complexity(self) -> None:
        self.complexity_requested.emit(self.complexity.value())

    def _request_lasso(self) -> None:
        self.lasso_requested.emit(str(self.operation.currentData()))

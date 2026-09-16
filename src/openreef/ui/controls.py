"""Viewer side-panel controls."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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

from openreef.core.scene import DISPLAY_MODES, SPLAT_DISPLAY_MODE
from openreef.ui.model_catalog import ModelCatalogSection


class ViewerControls(QWidget):
    content_mode_changed = Signal(str)
    open_requested = Signal()
    save_requested = Signal()
    use_crop_requested = Signal()
    web_export_requested = Signal()
    compact_web_export_requested = Signal()
    open_web_requested = Signal()
    fit_requested = Signal()
    projection_changed = Signal(bool)
    display_mode_changed = Signal(str)
    point_size_changed = Signal(int)
    standard_view_requested = Signal(str)
    lasso_requested = Signal(str)
    undo_requested = Signal()
    reset_requested = Signal()
    complexity_requested = Signal(int)
    splat_cleanup_requested = Signal()
    splat_cleanup_reset_requested = Signal()
    splat_cleanup_save_requested = Signal()
    orthomosaic_angle_requested = Signal()
    orthomosaic_export_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("OPENREEF")
        heading.setObjectName("heading")
        subtitle = QLabel("Viewer 0.5")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.content_mode = QComboBox()
        self.content_mode.setToolTip("Models found in the selected dataset's models folder")
        self.content_mode.addItem("Choose a model…", "")
        self.content_mode.currentIndexChanged.connect(self._content_mode_changed)
        layout.addWidget(self.content_mode)

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

        self.view_group = QGroupBox("View")
        view_layout = QVBoxLayout(self.view_group)
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

        self.orthomosaic_group = QGroupBox("Orthomosaic image")
        orthomosaic_layout = QVBoxLayout(self.orthomosaic_group)
        self.orthomosaic_angle_button = QPushButton("1. Set current viewing angle")
        self.orthomosaic_angle_button.setEnabled(False)
        self.orthomosaic_angle_button.setToolTip(
            "Rotate the model first, then save that direction for the orthographic export."
        )
        self.orthomosaic_angle_button.clicked.connect(self.orthomosaic_angle_requested)
        orthomosaic_layout.addWidget(self.orthomosaic_angle_button)
        orthomosaic_form = QFormLayout()
        self.orthomosaic_resolution = QComboBox()
        for label, pixels in (("2K", 2048), ("4K", 4096), ("8K", 8192)):
            self.orthomosaic_resolution.addItem(f"{label} ({pixels:,} px)", pixels)
        self.orthomosaic_resolution.setCurrentIndex(1)
        orthomosaic_form.addRow("Longest edge", self.orthomosaic_resolution)
        orthomosaic_layout.addLayout(orthomosaic_form)
        self.orthomosaic_transparent = QCheckBox("Transparent background")
        self.orthomosaic_transparent.setChecked(True)
        orthomosaic_layout.addWidget(self.orthomosaic_transparent)
        self.orthomosaic_export_button = QPushButton("2. Export orthomosaic PNG…")
        self.orthomosaic_export_button.setEnabled(False)
        self.orthomosaic_export_button.clicked.connect(self.orthomosaic_export_requested)
        orthomosaic_layout.addWidget(self.orthomosaic_export_button)
        self.orthomosaic_status = QLabel(
            "Set an angle first. Output is visual and unscaled until scaling is added."
        )
        self.orthomosaic_status.setObjectName("pageSubtitle")
        self.orthomosaic_status.setWordWrap(True)
        orthomosaic_layout.addWidget(self.orthomosaic_status)
        self.display_group = QGroupBox("Display")
        display_layout = QFormLayout(self.display_group)
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
        self.point_size.setValue(1)
        self.point_size_value = QLabel("1 px")
        self._splat_mode = False
        self._tileset_mode = False
        self.point_size.valueChanged.connect(self._on_point_size_changed)
        point_size_layout.addWidget(self.point_size, 0, 0)
        point_size_layout.addWidget(self.point_size_value, 0, 1)
        self.point_size_label = QLabel("Point size")
        display_layout.addRow(self.point_size_label, point_size_container)
        layout.addWidget(self.display_group)

        self.edit_group = QGroupBox("Crop and mesh")
        edit_layout = QVBoxLayout(self.edit_group)
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
        self.use_crop_button = QPushButton("Use crop in next stage")
        self.use_crop_button.setEnabled(False)
        self.use_crop_button.clicked.connect(self.use_crop_requested)
        edit_layout.addWidget(self.use_crop_button)
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
        layout.addWidget(self.edit_group)
        layout.addWidget(self.orthomosaic_group)

        self.splat_cleanup_group = QGroupBox("Gaussian cleanup")
        cleanup_layout = QVBoxLayout(self.splat_cleanup_group)
        cleanup_form = QFormLayout()
        self.splat_minimum_opacity = QDoubleSpinBox()
        self.splat_minimum_opacity.setRange(0.0, 100.0)
        self.splat_minimum_opacity.setDecimals(1)
        self.splat_minimum_opacity.setSingleStep(1.0)
        self.splat_minimum_opacity.setValue(2.0)
        self.splat_minimum_opacity.setSuffix(" %")
        cleanup_form.addRow("Minimum opacity", self.splat_minimum_opacity)
        self.splat_maximum_scale = QDoubleSpinBox()
        self.splat_maximum_scale.setRange(90.0, 100.0)
        self.splat_maximum_scale.setDecimals(1)
        self.splat_maximum_scale.setSingleStep(0.5)
        self.splat_maximum_scale.setValue(98.5)
        self.splat_maximum_scale.setSuffix(" %ile")
        cleanup_form.addRow("Maximum size", self.splat_maximum_scale)
        self.splat_maximum_aspect = QDoubleSpinBox()
        self.splat_maximum_aspect.setRange(1.0, 1000.0)
        self.splat_maximum_aspect.setDecimals(0)
        self.splat_maximum_aspect.setSingleStep(5.0)
        self.splat_maximum_aspect.setValue(50.0)
        self.splat_maximum_aspect.setSuffix("×")
        cleanup_form.addRow("Maximum stretch", self.splat_maximum_aspect)
        cleanup_layout.addLayout(cleanup_form)
        self.splat_use_roi = QCheckBox("Keep only the saved crop area")
        self.splat_use_roi.setChecked(True)
        cleanup_layout.addWidget(self.splat_use_roi)
        cleanup_buttons = QHBoxLayout()
        self.splat_preview_button = QPushButton("Preview")
        self.splat_preview_button.clicked.connect(self.splat_cleanup_requested)
        self.splat_reset_button = QPushButton("Original")
        self.splat_reset_button.clicked.connect(self.splat_cleanup_reset_requested)
        cleanup_buttons.addWidget(self.splat_preview_button)
        cleanup_buttons.addWidget(self.splat_reset_button)
        cleanup_layout.addLayout(cleanup_buttons)
        self.splat_save_button = QPushButton("Save cleaned splat…")
        self.splat_save_button.clicked.connect(self.splat_cleanup_save_requested)
        cleanup_layout.addWidget(self.splat_save_button)
        self.splat_cleanup_status = QLabel(
            "Removes faint and unusually large splats. The source file is unchanged."
        )
        self.splat_cleanup_status.setObjectName("pageSubtitle")
        self.splat_cleanup_status.setWordWrap(True)
        cleanup_layout.addWidget(self.splat_cleanup_status)
        self.splat_cleanup_group.setVisible(False)
        layout.addWidget(self.splat_cleanup_group)

        stats_group = QGroupBox("Model statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats = QTextEdit()
        self.stats.setReadOnly(True)
        self.stats.setMinimumHeight(150)
        self.stats.setPlainText("No model loaded")
        stats_layout.addWidget(self.stats)
        layout.addWidget(stats_group, 1)

        self.web_group = QGroupBox("OpenReef Web")
        web_layout = QVBoxLayout(self.web_group)
        self.web_export_button = QPushButton("Export current model…")
        self.web_export_button.setEnabled(False)
        self.web_export_button.clicked.connect(self.web_export_requested)
        self.compact_web_export_button = QPushButton("Export compact")
        self.compact_web_export_button.setEnabled(False)
        self.compact_web_export_button.setToolTip(
            "Compress GLB textures into a GitHub Pages-ready export without changing the original."
        )
        self.compact_web_export_button.clicked.connect(self.compact_web_export_requested)
        self.open_web_button = QPushButton("Open latest openreef-web")
        self.open_web_button.setEnabled(False)
        self.open_web_button.clicked.connect(self.open_web_requested)
        self.web_status = QLabel("Exports the current model as one browser-loaded file.")
        self.web_status.setObjectName("pageSubtitle")
        self.web_status.setWordWrap(True)
        web_layout.addWidget(self.web_export_button)
        web_layout.addWidget(self.compact_web_export_button)
        web_layout.addWidget(self.open_web_button)
        web_layout.addWidget(self.web_status)
        layout.addWidget(self.web_group)

    def set_stats(self, text: str) -> None:
        self.stats.setPlainText(text)

    def set_model_available(
        self,
        available: bool,
        description: str = "",
        *,
        editable: bool = True,
        exportable: bool = True,
    ) -> None:
        self.save_button.setEnabled(available and editable)
        self.draw_button.setEnabled(available and editable)
        self.web_export_button.setEnabled(available and exportable)
        self.compact_web_export_button.setEnabled(available and exportable)
        self.orthomosaic_angle_button.setEnabled(available and exportable)
        if not (available and exportable):
            self.reset_orthomosaic_angle()
        if available:
            self.edit_status.setText(description or "Ready to edit.")
        else:
            self.edit_status.setText("Open a model to enable editing.")

    def set_model_catalog(
        self,
        sections: tuple[ModelCatalogSection, ...],
        selected: Path | None = None,
    ) -> None:
        """Populate the one-column selector with disabled headings and indented models."""
        selected_value = f"model:{selected.resolve()}" if selected is not None else ""
        self.content_mode.blockSignals(True)
        self.content_mode.clear()
        self.content_mode.addItem("Choose a model…", "")
        selected_index = 0
        for section in sections:
            self.content_mode.addItem(section.title, "")
            heading_index = self.content_mode.count() - 1
            heading = self.content_mode.model().item(heading_index)
            if heading is not None:
                heading.setEnabled(False)
                font = heading.font()
                font.setBold(True)
                heading.setFont(font)
            for item in section.items:
                value = (
                    "view:sparse"
                    if item.label == "Points + cameras" and item.path.is_dir()
                    else f"model:{item.path}"
                )
                self.content_mode.addItem(f"    {item.label}", value)
                index = self.content_mode.count() - 1
                self.content_mode.setItemData(index, str(item.path), Qt.ItemDataRole.ToolTipRole)
                if value == selected_value:
                    selected_index = index
        self.content_mode.setCurrentIndex(selected_index)
        self.content_mode.blockSignals(False)

    def select_model(self, path: Path) -> None:
        wanted = f"model:{path.resolve()}"
        for index in range(self.content_mode.count()):
            if self.content_mode.itemData(index) == wanted:
                self.content_mode.blockSignals(True)
                self.content_mode.setCurrentIndex(index)
                self.content_mode.blockSignals(False)
                return

    def select_sparse_view(self) -> None:
        for index in range(self.content_mode.count()):
            if self.content_mode.itemData(index) == "view:sparse":
                self.content_mode.blockSignals(True)
                self.content_mode.setCurrentIndex(index)
                self.content_mode.blockSignals(False)
                return

    def set_splat_mode(self, enabled: bool) -> None:
        """Show that Gaussian files use the dedicated renderer, without making it selectable."""
        self._splat_mode = enabled
        self.display_mode.blockSignals(True)
        splat_index = self.display_mode.findText(SPLAT_DISPLAY_MODE)
        if enabled:
            if splat_index < 0:
                self.display_mode.addItem(SPLAT_DISPLAY_MODE)
            self.display_mode.setCurrentText(SPLAT_DISPLAY_MODE)
            self.display_mode.setEnabled(False)
            self.view_group.setVisible(False)
            self.orthomosaic_group.setVisible(False)
            self.display_group.setVisible(False)
            self.edit_group.setVisible(False)
            self.splat_cleanup_group.setVisible(True)
        else:
            if splat_index >= 0:
                self.display_mode.removeItem(splat_index)
            self.display_mode.setEnabled(True)
            self.display_mode.setCurrentText("Wireframe")
            self.point_size_label.setText("Point size")
            self.point_size_value.setText(f"{self.point_size.value()} px")
            self.view_group.setVisible(True)
            self.orthomosaic_group.setVisible(True)
            self.display_group.setVisible(True)
            self.edit_group.setVisible(True)
            self.splat_cleanup_group.setVisible(False)
        self.display_mode.blockSignals(False)

    def set_tileset_mode(self, enabled: bool) -> None:
        """Hide native-model tools while the embedded streaming viewer is active."""
        self._tileset_mode = enabled
        if enabled:
            self.view_group.setVisible(False)
            self.orthomosaic_group.setVisible(False)
            self.display_group.setVisible(False)
            self.edit_group.setVisible(False)
            self.splat_cleanup_group.setVisible(False)
            self.web_group.setVisible(False)
        elif not self._splat_mode:
            self.view_group.setVisible(True)
            self.orthomosaic_group.setVisible(True)
            self.display_group.setVisible(True)
            self.edit_group.setVisible(True)
            self.web_group.setVisible(True)

    def set_splat_cleanup_available(self, available: bool, roi_available: bool) -> None:
        self.splat_preview_button.setEnabled(available)
        self.splat_reset_button.setEnabled(available)
        self.splat_save_button.setEnabled(available)
        self.splat_use_roi.setEnabled(roi_available)
        self.splat_use_roi.setChecked(roi_available)
        self.splat_use_roi.setToolTip(
            "Uses the crop saved after sparse reconstruction."
            if roi_available
            else "No saved sparse crop was found for this dataset."
        )

    def splat_cleanup_options(self) -> tuple[float, float, float, bool]:
        return (
            self.splat_minimum_opacity.value() / 100.0,
            self.splat_maximum_scale.value(),
            self.splat_maximum_aspect.value(),
            self.splat_use_roi.isChecked() and self.splat_use_roi.isEnabled(),
        )

    def set_splat_cleanup_status(self, message: str) -> None:
        self.splat_cleanup_status.setText(message)

    def set_orthomosaic_angle_ready(self) -> None:
        self.orthomosaic_export_button.setEnabled(True)
        self.orthomosaic_status.setText(
            "Angle saved. Rotate freely; export will use the saved direction."
        )

    def reset_orthomosaic_angle(self) -> None:
        self.orthomosaic_export_button.setEnabled(False)
        self.orthomosaic_status.setText(
            "Set an angle first. Output is visual and unscaled until scaling is added."
        )

    def orthomosaic_options(self) -> tuple[int, bool]:
        return (
            int(self.orthomosaic_resolution.currentData()),
            self.orthomosaic_transparent.isChecked(),
        )

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

    def set_workflow_crop_stage(self, stage: str | None) -> None:
        labels = {
            "dense": "Use crop for Surface Mesh",
            "textured": "Save cropped textured GLB…",
        }
        self.use_crop_button.setText(labels.get(stage, "Use crop in next stage"))
        self.use_crop_button.setEnabled(stage in labels)

    def set_web_export_ready(self, path: str | None) -> None:
        self.open_web_button.setEnabled(bool(path))
        self.web_status.setText(
            f"Ready: {path}" if path else "Exports into an openreef-web folder."
        )

    def set_edit_status(self, message: str) -> None:
        self.edit_status.setText(message)

    def set_complexity(self, percent: int) -> None:
        self.complexity.blockSignals(True)
        self.complexity.setValue(percent)
        self.complexity.blockSignals(False)
        self.complexity_value.setText(f"{percent}%")

    def _on_point_size_changed(self, value: int) -> None:
        self.point_size_value.setText(f"{value}×" if self._splat_mode else f"{value} px")
        self.point_size_changed.emit(value)

    def _complexity_value_changed(self, value: int) -> None:
        self.complexity_value.setText(f"{value}%")

    def _request_complexity(self) -> None:
        self.complexity_requested.emit(self.complexity.value())

    def _request_lasso(self) -> None:
        self.lasso_requested.emit(str(self.operation.currentData()))

    def _content_mode_changed(self) -> None:
        self.content_mode_changed.emit(str(self.content_mode.currentData()))

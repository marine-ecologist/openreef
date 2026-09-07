"""OpenReef's main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from openreef.core.camera import CameraView
from openreef.core.mesh_edit import (
    LassoOperation,
    apply_lasso_operation,
    create_low_res_document,
    save_document,
)
from openreef.core.model import ModelDocument
from openreef.core.scene import SceneController
from openreef.io.model_loader import ModelLoadError, load_model
from openreef.pipeline.input_runner import InputRunner
from openreef.pipeline.runner import PipelineRunner
from openreef.pipeline.stages import DatasetLayout, dataset_label, sync_model_links
from openreef.ui.controls import ViewerControls
from openreef.ui.input_images_page import InputImagesPage
from openreef.ui.pipeline_page import PipelinePage
from openreef.ui.points_viewer_page import PointsViewerPage
from openreef.ui.viewport import ReefInteractor

MODEL_FILTER = "3D models (*.ply *.obj *.glb);;PLY (*.ply);;OBJ (*.obj);;GLB (*.glb)"
IMAGE_FILTER = "PNG image (*.png);;JPEG image (*.jpg *.jpeg)"
VIEW_FILTER = "OpenReef viewpoint (*.json)"
EDITED_MODEL_FILTER = "PLY mesh (*.ply);;VTK PolyData (*.vtp)"


class MainWindow(QMainWindow):
    def __init__(self, initial_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("OpenReef 0.2")
        self.resize(1440, 920)

        self.runner = PipelineRunner(self)
        self.input_runner = InputRunner(self)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self.input_page = InputImagesPage(self.input_runner)
        self.generate_page = PipelinePage("generate", self.runner)
        self.points_page = PointsViewerPage()
        self.dense_page = PipelinePage("dense", self.runner)
        self._dataset_root: Path | None = None
        self._edit_full_resolution: ModelDocument | None = None
        self._edit_history: list[tuple[ModelDocument, tuple[LassoOperation, ...]]] = []
        self._edit_operations: list[LassoOperation] = []
        self._complexity_percent = 100
        self._lasso_mode = "keep"

        self.viewer_page = QWidget()
        layout = QHBoxLayout(self.viewer_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.plotter = ReefInteractor(self.viewer_page)
        self.controls = ViewerControls(self.viewer_page)
        layout.addWidget(self.plotter.interactor, 1)
        layout.addWidget(self.controls)

        self.tabs.addTab(self.input_page, "Input Images")
        self.tabs.addTab(self.generate_page, "Sparse Cloud")
        self.tabs.addTab(self.points_page, "Points Viewer")
        self.tabs.addTab(self.dense_page, "Dense Cloud")
        self.tabs.addTab(self.viewer_page, "3D Viewer")

        self.scene = SceneController(self.plotter)
        self._connect_controls()
        self._create_actions()
        self._create_menus()
        self.statusBar().showMessage("Ready — choose a dataset or open a PLY, OBJ, or GLB model")

        if initial_path is not None:
            if initial_path.expanduser().is_dir():
                self.set_dataset_root(initial_path)
            else:
                self.load_path(initial_path)

    def _connect_controls(self) -> None:
        self.controls.fit_requested.connect(self.scene.fit_to_view)
        self.controls.projection_changed.connect(self.scene.set_parallel_projection)
        self.controls.display_mode_changed.connect(self.scene.set_display_mode)
        self.controls.point_size_changed.connect(self.scene.set_point_size)
        self.controls.standard_view_requested.connect(self.scene.set_standard_view)
        self.controls.open_requested.connect(self.open_model)
        self.controls.save_requested.connect(self._save_edited_model)
        self.controls.lasso_requested.connect(self._begin_lasso)
        self.controls.undo_requested.connect(self._undo_edit)
        self.controls.reset_requested.connect(self._reset_edits)
        self.controls.complexity_requested.connect(self._set_mesh_complexity)
        self.input_page.dataset_path_changed.connect(self._sync_dataset_root)
        self.input_page.images_ready.connect(self._input_images_ready)
        self.generate_page.dataset_path_changed.connect(self._sync_dataset_root)
        self.dense_page.dataset_path_changed.connect(self._sync_dataset_root)
        self.dense_page.open_artifact_requested.connect(self.load_path)
        self.points_page.roi_changed.connect(self._roi_changed)
        self.plotter.lasso_finished.connect(self._finish_lasso)
        self.plotter.lasso_cancelled.connect(self._lasso_cancelled)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.runner.artifact_ready.connect(self._dense_artifact_ready)
        self.runner.job_finished.connect(self._pipeline_finished)
        self.runner.running_changed.connect(self.input_page.set_pipeline_busy)
        self.input_runner.running_changed.connect(self.generate_page.set_external_busy)
        self.input_runner.running_changed.connect(self.dense_page.set_external_busy)

    def _create_actions(self) -> None:
        self.dataset_action = QAction("Choose &dataset…", self)
        self.dataset_action.setShortcut("Ctrl+Shift+O")
        self.dataset_action.triggered.connect(self.choose_dataset)

        self.open_action = QAction("&Open model…", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_model)

        self.screenshot_action = QAction("Save &screenshot…", self)
        self.screenshot_action.setShortcut("Ctrl+Shift+S")
        self.screenshot_action.triggered.connect(self.save_screenshot)

        self.save_view_action = QAction("Save viewpoint…", self)
        self.save_view_action.triggered.connect(self.save_viewpoint)
        self.load_view_action = QAction("Load viewpoint…", self)
        self.load_view_action.triggered.connect(self.load_viewpoint)

        self.quit_action = QAction("&Quit", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.quit_action.triggered.connect(self.close)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.dataset_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.screenshot_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        camera_menu = self.menuBar().addMenu("&Camera")
        camera_menu.addAction(self.save_view_action)
        camera_menu.addAction(self.load_view_action)

    def choose_dataset(self) -> None:
        current = self.input_page.dataset_path.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose OpenReef dataset", current)
        if selected:
            self.set_dataset_root(selected)

    def set_dataset_root(self, path: str | Path) -> None:
        if not str(path).strip():
            return
        root = Path(path).expanduser().resolve()
        self._dataset_root = root
        self._sync_dataset_root(root)
        self.tabs.setCurrentWidget(self.input_page)
        self.setWindowTitle(f"{root.name} — OpenReef 0.2")
        self.statusBar().showMessage(f"Dataset: {root}")

    def _sync_dataset_root(self, path: str | Path) -> None:
        if not str(path).strip():
            return
        root = Path(path).expanduser().resolve()
        self.input_page.set_dataset_root(root)
        self.generate_page.set_dataset_root(root)
        self.points_page.set_dataset_root(root)
        self.dense_page.set_dataset_root(root)
        try:
            sync_model_links(DatasetLayout(root))
        except OSError as exc:
            self.statusBar().showMessage(f"Dataset selected; mesh shortcuts unavailable: {exc}")
        self.setWindowTitle(f"{root.name} — OpenReef 0.2")
        self.statusBar().showMessage(f"Dataset: {root}")

    def _input_images_ready(self, dataset: str) -> None:
        self._sync_dataset_root(dataset)
        count = self.generate_page.dataset_summary.text()
        self.statusBar().showMessage(f"Input images ready — {count}")

    def open_model(self) -> None:
        start = str(self._dataset_root / "models") if self._dataset_root else ""
        filename, _ = QFileDialog.getOpenFileName(self, "Open reef model", start, MODEL_FILTER)
        if filename:
            self.load_path(Path(filename))

    def load_path(self, path: Path) -> None:
        try:
            document = load_model(path)
            self.scene.set_document(document)
        except ModelLoadError as exc:
            QMessageBox.critical(self, "Could not open model", str(exc))
            self.statusBar().showMessage("Model could not be opened")
            return
        self.controls.set_stats(document.stats.as_text())
        self._edit_full_resolution = document
        self._edit_history.clear()
        self._edit_operations.clear()
        self._complexity_percent = 100
        self.controls.set_complexity(100)
        self.controls.set_model_available(
            True,
            f"Ready — {document.stats.points:,} points and {document.stats.cells:,} cells.",
        )
        self.controls.set_mesh_available(any(part.kind == "mesh" for part in document.parts))
        self.controls.set_history_available(False)
        self.setWindowTitle(f"{document.source.name} — OpenReef Viewer 0.2")
        self.statusBar().showMessage(f"Loaded {document.source}")
        self.tabs.setCurrentIndex(4)

    def _begin_lasso(self, mode: str) -> None:
        if self.scene.document is None:
            QMessageBox.information(self, "No model", "Open a model before drawing a lasso.")
            return
        self._lasso_mode = mode
        self.tabs.setCurrentWidget(self.viewer_page)
        self.plotter.begin_lasso()
        action = "keep what is inside" if mode == "keep" else "delete what is inside"
        message = f"Draw around the model area to {action}. Release to apply; Esc cancels."
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _tab_changed(self, index: int) -> None:
        if self.tabs.widget(index) is self.points_page and self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
        if self.tabs.widget(index) is not self.viewer_page:
            self.plotter.cancel_lasso()

    def _finish_lasso(self, points: object) -> None:
        document = self.scene.document
        if document is None or not isinstance(points, list):
            return
        viewpoint = CameraView.capture(self.plotter)
        before = document.stats
        self.controls.set_edit_status("Applying lasso trim…")
        try:
            operation = LassoOperation.capture(
                self.plotter.camera,
                (self.plotter.width(), self.plotter.height()),
                points,
                keep_inside=self._lasso_mode == "keep",
            )
            result = apply_lasso_operation(document, operation)
        except (TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, "Lasso could not be applied", str(exc))
            self.controls.set_edit_status("No change made. Adjust the view and try another lasso.")
            return

        self._edit_history.append((document, tuple(self._edit_operations)))
        self._edit_operations.append(operation)
        self._show_edited_document(result.document, viewpoint)
        self.controls.set_history_available(True)
        after = result.document.stats
        message = (
            f"Trim applied — {before.points:,} → {after.points:,} points; "
            f"{before.cells:,} → {after.cells:,} cells."
        )
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _lasso_cancelled(self) -> None:
        message = "Lasso cancelled — no change made."
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _show_edited_document(self, document: ModelDocument, viewpoint: CameraView) -> None:
        self.scene.set_document(document)
        viewpoint.apply(self.plotter)
        self.controls.set_stats(document.stats.as_text())
        self.setWindowTitle(f"{document.source.name} — OpenReef Viewer 0.2")

    def _undo_edit(self) -> None:
        if not self._edit_history:
            return
        viewpoint = CameraView.capture(self.plotter)
        document, operations = self._edit_history.pop()
        self._edit_operations = list(operations)
        self._show_edited_document(document, viewpoint)
        self.controls.set_history_available(bool(self._edit_history))
        message = "Last lasso trim undone."
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _reset_edits(self) -> None:
        if self.scene.document is None or self._edit_full_resolution is None:
            return
        if not self._edit_operations:
            return
        self._edit_history.append((self.scene.document, tuple(self._edit_operations)))
        self._edit_operations.clear()
        self._display_complexity(self._complexity_percent, clear_history=False)
        self.controls.set_history_available(True)
        message = "Restored the originally opened model. Undo can restore the edited version."
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _save_edited_model(self) -> None:
        document = self.scene.document
        if document is None:
            return
        if self._dataset_root:
            layout = DatasetLayout(self._dataset_root)
            layout.models.mkdir(parents=True, exist_ok=True)
            suffix = (
                f"mesh_{self._complexity_percent}pct"
                if self._complexity_percent < 100
                else "mesh_edited"
            )
            suggested = layout.models / f"{dataset_label(layout)}_{suffix}.ply"
        else:
            suggested = document.source.with_name(f"{document.source.stem}_edited.ply")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save edited model",
            str(suggested),
            EDITED_MODEL_FILTER,
        )
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(".ply")
        try:
            self.controls.set_edit_status("Preparing model at the selected complexity…")
            QApplication.processEvents()
            export_document = self._document_at_complexity(self._complexity_percent)
            destination = save_document(export_document, path)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not save edited model", str(exc))
            return
        message = f"Saved edited model to {destination}"
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _set_mesh_complexity(self, percent: int) -> None:
        if self._edit_full_resolution is None:
            return
        self._display_complexity(percent, clear_history=True)

    def _display_complexity(self, percent: int, *, clear_history: bool) -> None:
        source = self._edit_full_resolution
        if source is None:
            return
        percent = max(5, min(int(percent), 100))
        self.controls.set_edit_status("Updating mesh complexity…")
        QApplication.processEvents()
        try:
            displayed = self._document_at_complexity(percent)
            if percent < 100 and self._dataset_root:
                layout = DatasetLayout(self._dataset_root)
                layout.models.mkdir(parents=True, exist_ok=True)
                preview_path = layout.models / f"{dataset_label(layout)}_mesh_lores.ply"
                save_document(displayed, preview_path)
                displayed = ModelDocument(source=preview_path, parts=displayed.parts)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, "Could not change mesh complexity", str(exc))
            self.controls.set_complexity(self._complexity_percent)
            self.controls.set_edit_status("Mesh complexity was not changed.")
            return

        viewpoint = CameraView.capture(self.plotter)
        self._complexity_percent = percent
        self._show_edited_document(displayed, viewpoint)
        self.controls.set_complexity(percent)
        if clear_history:
            self._edit_history.clear()
            self.controls.set_history_available(False)
        message = (
            f"Mesh complexity: {percent}% · {displayed.stats.cells:,} cells. "
            "Save As writes this complexity while preserving lasso edits."
        )
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _document_at_complexity(self, percent: int) -> ModelDocument:
        if self._edit_full_resolution is None:
            raise ValueError("The full-resolution source model is no longer available")
        document = self._edit_full_resolution
        for operation in self._edit_operations:
            document = apply_lasso_operation(document, operation).document
        if percent >= 100:
            return document
        source_cells = sum(
            int(part.dataset.n_cells) for part in document.parts if part.kind == "mesh"
        )
        target_cells = max(1_000, round(source_cells * percent / 100))
        return create_low_res_document(document, target_cells)

    def _roi_changed(self, path: str) -> None:
        if self._dataset_root is None:
            return
        self.generate_page.set_dataset_root(self._dataset_root)
        self.dense_page.set_dataset_root(self._dataset_root)
        message = (
            "Processing ROI saved; rerun OpenMVS import and later stages."
            if path
            else "Processing ROI cleared; rerun OpenMVS import for the complete model."
        )
        self.statusBar().showMessage(message)

    def _dense_artifact_ready(self, path: str) -> None:
        self.statusBar().showMessage(f"Model ready for 3D Viewer: {path}")

    def _pipeline_finished(self, success: bool, message: str) -> None:
        if success and self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
            self.generate_page.set_dataset_root(self._dataset_root)
            self.dense_page.set_dataset_root(self._dataset_root)
        self.statusBar().showMessage(message)

    def save_screenshot(self) -> None:
        if self.scene.document is None:
            QMessageBox.information(self, "No model", "Open a model before taking a screenshot.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save screenshot", "openreef.png", IMAGE_FILTER
        )
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(".png")
        try:
            self.plotter.screenshot(str(path))
        except Exception as exc:
            QMessageBox.critical(self, "Could not save screenshot", str(exc))
            return
        self.statusBar().showMessage(f"Saved screenshot to {path}")

    def save_viewpoint(self) -> None:
        if self.scene.document is None:
            QMessageBox.information(self, "No model", "Open a model before saving a viewpoint.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save viewpoint", "viewpoint.json", VIEW_FILTER
        )
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(".json")
        try:
            CameraView.capture(self.plotter).save(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not save viewpoint", str(exc))
            return
        self.statusBar().showMessage(f"Saved viewpoint to {path}")

    def load_viewpoint(self) -> None:
        if self.scene.document is None:
            QMessageBox.information(self, "No model", "Open a model before loading a viewpoint.")
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Load viewpoint", "", VIEW_FILTER)
        if not filename:
            return
        try:
            viewpoint = CameraView.load(Path(filename))
            viewpoint.apply(self.plotter)
        except ValueError as exc:
            QMessageBox.critical(self, "Could not load viewpoint", str(exc))
            return
        self.controls.projection.blockSignals(True)
        self.controls.projection.setChecked(viewpoint.parallel_projection)
        self.controls.projection.blockSignals(False)
        self.statusBar().showMessage(f"Loaded viewpoint from {filename}")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API name
        if self.runner.is_running or self.input_runner.is_running:
            answer = QMessageBox.question(
                self,
                "Processing is still running",
                "Stop the active reconstruction stage and close OpenReef?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.runner.cancel()
            self.input_runner.stop()
        self.plotter.close()
        self.points_page.plotter.close()
        event.accept()

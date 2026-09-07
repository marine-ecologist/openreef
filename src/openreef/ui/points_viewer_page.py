"""Fast COLMAP sparse-point and registered-camera quality-control viewer."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pyvista as pv
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from openreef.core.scene import SceneController
from openreef.io.colmap_model import (
    CameraPose,
    SparseROI,
    lasso_roi,
    read_camera_poses,
    save_camera_manifest,
)
from openreef.io.model_loader import ModelLoadError, load_model
from openreef.pipeline.stages import (
    DatasetLayout,
    dataset_label,
    resolve_executable,
    sparse_model_counts,
    sync_model_links,
)
from openreef.ui.viewport import ReefInteractor


class PointsViewerPage(QWidget):
    roi_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout: DatasetLayout | None = None
        self._roi: SparseROI | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Points Viewer")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Inspect COLMAP sparse points and registered camera positions.")
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        self.model_selector = QComboBox()
        self.model_selector.setMinimumWidth(260)
        self.model_selector.setToolTip(
            "Each entry is a separate connected COLMAP reconstruction folder."
        )
        self.model_selector.currentIndexChanged.connect(self._model_selected)
        header.addWidget(QLabel("Sparse model"))
        header.addWidget(self.model_selector)
        self.fit_button = QPushButton("Fit to view")
        self.fit_button.clicked.connect(self._fit)
        self.parallel = QCheckBox("Orthographic")
        self.parallel.toggled.connect(self._set_projection)
        self.roi_button = QPushButton("Draw processing ROI")
        self.roi_button.setObjectName("primaryButton")
        self.roi_button.setEnabled(False)
        self.roi_button.clicked.connect(self._begin_roi)
        self.clear_roi_button = QPushButton("Clear ROI")
        self.clear_roi_button.setEnabled(False)
        self.clear_roi_button.clicked.connect(self._clear_roi)
        header.addWidget(self.fit_button)
        header.addWidget(self.parallel)
        header.addWidget(self.roi_button)
        header.addWidget(self.clear_roi_button)
        layout.addLayout(header)

        views = QHBoxLayout()
        for name in ("Top", "Front", "Right"):
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, value=name: self._standard_view(value))
            views.addWidget(button)
        self.summary = QLabel("Run Sparse reconstruction to inspect points and cameras.")
        self.summary.setObjectName("datasetSummary")
        views.addWidget(self.summary, 1)
        layout.addLayout(views)

        self.plotter = ReefInteractor(self)
        self.scene = SceneController(self.plotter)
        self.plotter.lasso_finished.connect(self._finish_roi)
        self.plotter.lasso_cancelled.connect(self._cancel_roi)
        layout.addWidget(self.plotter.interactor, 1)

    def set_dataset_root(self, path: str | Path) -> None:
        self._layout = DatasetLayout.from_path(path)
        models = self._layout.sparse_models()
        selected = self._layout.sparse_model()
        recommended_model = max(models, key=sparse_model_counts) if models else None
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        for model in models:
            images, points = sparse_model_counts(model)
            recommended = (
                " · recommended" if recommended_model and model == recommended_model else ""
            )
            self.model_selector.addItem(
                f"Model {model.name} · {images:,} images · {points:,} points{recommended}",
                str(model),
            )
        if selected is not None:
            selected_path = str(selected.resolve())
            for index in range(self.model_selector.count()):
                if self.model_selector.itemData(index) == selected_path:
                    self.model_selector.setCurrentIndex(index)
                    break
            try:
                self._layout.select_sparse_model(selected)
            except (OSError, ValueError):
                pass
        self.model_selector.blockSignals(False)
        self.model_selector.setEnabled(bool(models))
        if selected is None:
            self._show_missing_cloud("Sparse cloud not available yet.")
            return
        self._load_sparse_model(selected)

    def _model_selected(self, index: int) -> None:
        if self._layout is None or index < 0:
            return
        model = Path(str(self.model_selector.itemData(index)))
        try:
            self._layout.select_sparse_model(model)
        except (OSError, ValueError) as exc:
            self.summary.setText(f"Could not select sparse model: {exc}")
            return
        self._load_sparse_model(model)

    def _load_sparse_model(self, model: Path) -> None:
        assert self._layout is not None
        sparse_cloud = model / "points3D.ply"
        if not sparse_cloud.is_file():
            try:
                executable = resolve_executable("colmap")
                result = subprocess.run(
                    [
                        executable,
                        "model_converter",
                        "--input_path",
                        str(model),
                        "--output_path",
                        str(sparse_cloud),
                        "--output_type",
                        "PLY",
                    ],
                    check=False,
                )
            except OSError as exc:
                self._show_missing_cloud(f"Could not export sparse model {model.name}: {exc}")
                return
            if result.returncode != 0 or not sparse_cloud.is_file():
                self._show_missing_cloud(f"Could not export sparse model {model.name} to PLY.")
                return
        try:
            sync_model_links(self._layout)
        except OSError:
            pass
        try:
            document = load_model(sparse_cloud)
        except ModelLoadError as exc:
            self.summary.setText(str(exc))
            self.roi_button.setEnabled(False)
            return

        self.scene.set_document(document)
        poses = self._load_cameras(model)
        if poses:
            camera_lines = _camera_wireframe(poses, document.stats.bounds)
            self.plotter.add_mesh(
                camera_lines,
                name="colmap-cameras",
                color="#ffad78",
                line_width=2,
                render_lines_as_tubes=True,
            )
            manifest = self._layout.models / f"{dataset_label(self._layout)}_cameras.json"
            try:
                save_camera_manifest(poses, manifest)
            except OSError:
                pass
        self._roi = self._load_roi(self._layout.roi, model.name)
        self._show_roi()
        self.roi_button.setEnabled(True)
        self.clear_roi_button.setEnabled(self._roi is not None)
        self.summary.setText(
            f"Model {model.name} · {document.stats.points:,} sparse points · "
            f"{len(poses):,} of {self._layout.image_count():,} images registered"
            + (" · processing ROI active" if self._roi else "")
        )
        self.scene.fit_to_view()

    def _show_missing_cloud(self, message: str) -> None:
        self.scene.document = None
        self.plotter.clear()
        self.plotter.add_axes(line_width=2)
        self.roi_button.setEnabled(False)
        self.summary.setText(message)

    def _load_cameras(self, model: Path) -> tuple[CameraPose, ...]:
        images_binary = model / "images.bin"
        if not images_binary.is_file():
            return ()
        try:
            return read_camera_poses(images_binary)
        except (OSError, ValueError):
            return ()

    def _begin_roi(self) -> None:
        self.summary.setText(
            "Draw around the sparse points to retain for dense processing; release to save."
        )
        self.plotter.begin_lasso()

    def _finish_roi(self, points: object) -> None:
        document = self.scene.document
        if document is None or self._layout is None or not isinstance(points, list):
            return
        try:
            roi = lasso_roi(
                document,
                self.plotter.camera,
                (self.plotter.width(), self.plotter.height()),
                points,
                sparse_model=self._layout.sparse_model().name,
            )
            roi.save(self._layout.roi)
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Could not create ROI", str(exc))
            self.summary.setText("ROI was not changed.")
            return
        self._roi = roi
        self._show_roi()
        self.clear_roi_button.setEnabled(True)
        self.summary.setText(
            f"ROI saved · {roi.selected_points:,} of {roi.total_points:,} sparse points retained"
        )
        self.roi_changed.emit(str(self._layout.roi))

    def _clear_roi(self) -> None:
        if self._layout is None:
            return
        try:
            self._layout.roi.unlink(missing_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "Could not clear ROI", str(exc))
            return
        self._roi = None
        self.plotter.remove_actor("processing-roi", reset_camera=False, render=True)
        self.clear_roi_button.setEnabled(False)
        self.summary.setText("Processing ROI cleared; OpenMVS will use the complete sparse model.")
        self.roi_changed.emit("")

    def _show_roi(self) -> None:
        self.plotter.remove_actor("processing-roi", reset_camera=False, render=False)
        if self._roi is not None:
            self.plotter.add_mesh(
                pv.Box(bounds=self._roi.bounds),
                name="processing-roi",
                style="wireframe",
                color="#72e3c0",
                line_width=3,
            )
        self.plotter.render()

    def _load_roi(self, path: Path, sparse_model: str) -> SparseROI | None:
        if not path.is_file():
            return None
        try:
            roi = SparseROI.load(path)
            return roi if not roi.sparse_model or roi.sparse_model == sparse_model else None
        except (OSError, ValueError, KeyError):
            return None

    def _fit(self) -> None:
        self.scene.fit_to_view()

    def _set_projection(self, enabled: bool) -> None:
        self.scene.set_parallel_projection(enabled)

    def _standard_view(self, name: str) -> None:
        self.scene.set_standard_view(name)

    def _cancel_roi(self) -> None:
        self.summary.setText("ROI drawing cancelled.")

    def close(self) -> bool:
        self.plotter.close()
        return super().close()


def _camera_wireframe(
    poses: tuple[CameraPose, ...],
    bounds: tuple[float, float, float, float, float, float],
) -> pv.PolyData:
    extent = np.asarray((bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]))
    scale = max(float(np.linalg.norm(extent)) * 0.025, 1.0e-4)
    points: list[np.ndarray] = []
    lines: list[list[int]] = []
    for pose in poses:
        center = np.asarray(pose.center)
        right = np.asarray(pose.right)
        up = np.asarray(pose.up)
        forward = np.asarray(pose.forward)
        plane = center + forward * scale
        corners = (
            plane - right * scale * 0.65 - up * scale * 0.42,
            plane + right * scale * 0.65 - up * scale * 0.42,
            plane + right * scale * 0.65 + up * scale * 0.42,
            plane - right * scale * 0.65 + up * scale * 0.42,
        )
        start = len(points)
        points.extend((center, *corners))
        for corner in range(1, 5):
            lines.append([2, start, start + corner])
        for first, second in ((1, 2), (2, 3), (3, 4), (4, 1)):
            lines.append([2, start + first, start + second])
    geometry = pv.PolyData(np.asarray(points))
    geometry.lines = np.asarray(lines, dtype=np.int64).ravel()
    return geometry

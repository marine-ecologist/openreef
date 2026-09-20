"""OpenReef's main application window."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QProcess, QProcessEnvironment, QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from openreef.core.camera import CameraOrientation, CameraView, orthomosaic_image_size
from openreef.core.mesh_edit import (
    LassoOperation,
    apply_lasso_operation,
    create_low_res_document,
    save_document,
)
from openreef.core.model import ModelDocument
from openreef.core.scene import SceneController, is_gaussian_splat
from openreef.io.colmap_model import SparseROI
from openreef.io.gaussian_ply import clean_gaussian_document, write_gaussian_ply
from openreef.io.markertags import (
    format_viewer_diagnostics,
    has_metric_scale,
    read_viewer_metadata,
)
from openreef.io.model_loader import ModelLoadError, load_model
from openreef.pipeline.input_runner import InputRunner
from openreef.pipeline.runner import PipelineRunner
from openreef.pipeline.stages import (
    DatasetLayout,
    StageKey,
    dataset_label,
    dense_crop_for_output,
    stage_output_exists,
    sync_model_links,
)
from openreef.ui.controls import ViewerControls
from openreef.ui.input_images_page import InputImagesPage
from openreef.ui.measurements import MeasurementController
from openreef.ui.model_catalog import (
    ModelCatalogSection,
    discover_model_catalog,
    preferred_model_path,
)
from openreef.ui.points_viewer_page import PointsViewerPage
from openreef.ui.render_images_page import RenderImagesPage
from openreef.ui.splat_viewer_page import SplatViewerPage
from openreef.ui.theme import ASSET_FOLDER, application_stylesheet, bootstrap_icon, icon_color
from openreef.ui.tileset_viewer_page import TilesetViewerPage
from openreef.ui.viewport import ReefInteractor
from openreef.web_export import (
    GITHUB_REGULAR_FILE_LIMIT,
    export_web_viewer,
    read_tiled_model_manifest,
)

MODEL_FILTER = (
    "OpenReef models (*.ply *.obj *.glb *_3d_tiles.json);;"
    "3D Tiles entries (*_3d_tiles.json);;PLY (*.ply);;OBJ (*.obj);;GLB (*.glb)"
)
IMAGE_FILTER = "PNG image (*.png);;JPEG image (*.jpg *.jpeg)"
VIEW_FILTER = "OpenReef viewpoint (*.json)"
EDITED_MODEL_FILTER = "PLY mesh (*.ply);;VTK PolyData (*.vtp)"
EDITED_GLB_FILTER = "Textured GLB (*.glb)"


class MainWindow(QMainWindow):
    def __init__(
        self,
        initial_path: Path | None = None,
        *,
        restore_last_dataset: bool = True,
    ) -> None:
        super().__init__()
        self.setWindowTitle("OpenReef 0.6.2")
        # The wider default leaves the embedded streaming 3D Tiles canvas useful
        # alongside the viewer controls without changing the compact dark layout.
        self.resize(1848, 1104)

        self.runner = PipelineRunner(self)
        self.input_runner = InputRunner(self)
        # Keep the historical name internally because viewer and pipeline actions
        # already switch this workspace. The visible tab bar is replaced by the
        # macOS-style sidebar below.
        self.tabs = QStackedWidget()
        self.tabs.setObjectName("workspaceStack")

        self.input_page = InputImagesPage(self.input_runner)
        self.render_page = RenderImagesPage(self.runner)
        self.input_scroll = self._workspace_scroll(self.input_page)
        self.render_scroll = self._workspace_scroll(self.render_page)
        self.points_page = PointsViewerPage()
        self._dataset_root: Path | None = None
        self._edit_full_resolution: ModelDocument | None = None
        self._edit_history: list[tuple[ModelDocument, tuple[LassoOperation, ...]]] = []
        self._edit_operations: list[LassoOperation] = []
        self._complexity_percent = 100
        self._lasso_mode = "keep"
        self._last_web_export: Path | None = None
        self._tile_build_layout: DatasetLayout | None = None
        self._tile_build_buffer = ""
        self._tile_build_log: list[str] = []
        self._tile_process = QProcess(self)
        self._tile_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._tile_process.readyReadStandardOutput.connect(self._tile_build_output_ready)
        self._tile_process.finished.connect(self._tile_build_finished)
        self._tile_process.errorOccurred.connect(self._tile_build_error)
        self._orthomosaic_view: CameraView | None = None
        self._orthographic_orientation = self._load_orthographic_orientation()
        self._splat_preview_folder = TemporaryDirectory(prefix="openreef-splat-")

        self.viewer_page = QWidget()
        layout = QHBoxLayout(self.viewer_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.plotter = ReefInteractor(self.viewer_page)
        self.controls = ViewerControls(self.viewer_page)
        self.controls_scroll = QScrollArea(self.viewer_page)
        self.controls_scroll.setObjectName("viewerControlsScroll")
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.controls_scroll.setMinimumWidth(280)
        self.controls_scroll.setMaximumWidth(360)
        self.controls_scroll.setWidget(self.controls)
        self.viewer_stack = QStackedWidget(self.viewer_page)
        self.viewer_stack.addWidget(self.plotter.interactor)
        self.viewer_stack.addWidget(self.points_page)
        self.splat_page = SplatViewerPage(self.viewer_page)
        self.viewer_stack.addWidget(self.splat_page)
        self.tileset_page = TilesetViewerPage(self.viewer_page)
        self.viewer_stack.addWidget(self.tileset_page)
        layout.addWidget(self.viewer_stack, 1)
        layout.addWidget(self.controls_scroll)

        self.projects_page = self._build_projects_page()
        self.markertags_page = self._build_markertags_page()
        self.settings_page = self._build_settings_page()
        for page in (
            self.render_scroll,
            self.input_scroll,
            self.viewer_page,
            self.projects_page,
            self.markertags_page,
            self.settings_page,
        ):
            self.tabs.addWidget(page)

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_sidebar())
        shell_layout.addWidget(self.tabs, 1)
        self.setCentralWidget(shell)

        self.scene = SceneController(self.plotter)
        self.measurements = MeasurementController(self.plotter)
        self._dark_mode = QSettings().value("appearance/dark", True, type=bool)
        self._apply_theme()
        self._connect_controls()
        self._create_actions()
        self._create_menus()
        self.controls.set_preferred_view_ready(self._orthographic_orientation is not None)
        self.statusBar().showMessage("Ready — choose a dataset or open a PLY, OBJ, or GLB model")

        if initial_path is not None:
            if initial_path.expanduser().is_dir():
                self.set_dataset_root(initial_path)
            else:
                self.load_path(initial_path)
        elif restore_last_dataset:
            saved_dataset = QSettings().value("workspace/last_dataset", "", type=str)
            if saved_dataset and Path(saved_dataset).is_dir():
                self.set_dataset_root(saved_dataset)
        QTimer.singleShot(0, self._center_on_screen)

    def _center_on_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        frame = self.frameGeometry()
        frame.moveCenter(screen.availableGeometry().center())
        self.move(frame.topLeft())

    def _workspace_scroll(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea(self.tabs)
        scroll.setObjectName("workspacePageScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("appSidebar")
        sidebar.setFixedWidth(224)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(4)

        traffic_lights = QHBoxLayout()
        traffic_lights.setSpacing(8)
        for name in ("trafficRed", "trafficYellow", "trafficGreen"):
            light = QLabel()
            light.setObjectName(name)
            light.setFixedSize(12, 12)
            traffic_lights.addWidget(light)
        traffic_lights.addStretch(1)
        layout.addLayout(traffic_lights)
        layout.addSpacing(22)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        logo = QLabel()
        logo.setObjectName("sidebarLogo")
        logo_path = ASSET_FOLDER / "openreef-icon.png"
        if logo_path.is_file():
            logo.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    44,
                    44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        brand.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)
        name_box = QVBoxLayout()
        name_box.setSpacing(1)
        name = QLabel("OpenReef")
        name.setObjectName("appTitle")
        caption = QLabel("REEF PHOTOGRAMMETRY")
        caption.setObjectName("appCaption")
        name_box.addWidget(name)
        name_box.addWidget(caption)
        brand.addLayout(name_box, 1)
        layout.addLayout(brand)
        layout.addSpacing(24)

        self.navigation_buttons: dict[QWidget, QPushButton] = {}
        layout.addWidget(self._sidebar_button("Projects", self.projects_page))

        layout.addSpacing(14)
        layout.addWidget(self._sidebar_divider())
        layout.addSpacing(14)
        layout.addWidget(self._sidebar_section("WORKFLOW"))
        for label, page in (
            ("Images", self.input_scroll),
            ("Process", self.render_scroll),
            ("Viewer", self.viewer_page),
        ):
            layout.addWidget(self._sidebar_button(label, page))

        layout.addSpacing(14)
        layout.addWidget(self._sidebar_divider())
        layout.addSpacing(14)
        layout.addWidget(self._sidebar_section("TOOLS"))
        layout.addWidget(self._sidebar_button("MarkerTags", self.markertags_page))
        layout.addWidget(self._sidebar_button("Settings", self.settings_page))

        layout.addSpacing(14)
        layout.addWidget(self._sidebar_divider())
        layout.addSpacing(14)
        layout.addWidget(self._sidebar_section("HELP"))
        for label, url in (
            ("Documentation", "https://github.com/marine-ecologist/openreef#readme"),
            ("Examples", "https://github.com/marine-ecologist/openreef"),
            ("Report issue", "https://github.com/marine-ecologist/openreef/issues/new"),
        ):
            button = QPushButton(label)
            button.setObjectName("sidebarLink")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, destination=url: QDesktopServices.openUrl(QUrl(destination))
            )
            layout.addWidget(button)
        layout.addStretch(1)
        version = QLabel("OpenReef v0.6.2")
        version.setObjectName("sidebarVersion")
        layout.addWidget(version)
        self._sync_navigation()
        return sidebar

    @staticmethod
    def _sidebar_section(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sidebarSection")
        return label

    @staticmethod
    def _sidebar_divider() -> QFrame:
        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        return divider

    def _sidebar_button(self, label: str, page: QWidget) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("sidebarNav")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False, target=page: self._navigate(target))
        self.navigation_buttons[page] = button
        return button

    def _navigate(self, page: QWidget) -> None:
        self.tabs.setCurrentWidget(page)
        self._sync_navigation()

    def _sync_navigation(self) -> None:
        if not hasattr(self, "navigation_buttons"):
            return
        current = self.tabs.currentWidget()
        for page, button in self.navigation_buttons.items():
            button.setChecked(page is current)

    def _show_markertags(self) -> None:
        self._navigate(self.markertags_page)

    def _build_projects_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("projectsPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(14)
        title = QLabel("Projects")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel(
            "Open or switch the survey workspace used across Data, Process, and Viewer."
        )
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)
        card = QFrame()
        card.setObjectName("projectCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        self.project_name = QLabel("No project selected")
        self.project_name.setObjectName("projectName")
        self.project_path = QLabel("Choose a dataset folder to begin.")
        self.project_path.setObjectName("pageSubtitle")
        self.project_path.setWordWrap(True)
        choose = QPushButton("Choose project…")
        choose.setObjectName("primaryButton")
        choose.clicked.connect(self.choose_dataset)
        card_layout.addWidget(self.project_name)
        card_layout.addWidget(self.project_path)
        card_layout.addSpacing(8)
        card_layout.addWidget(choose, 0, Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card)
        outer.addStretch(1)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(14)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel("Detailed processing controls for workflow steps 1–6")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        outer.addWidget(self.render_page.settings_group, 1)

        card = QFrame()
        card.setObjectName("projectCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        self.theme_button = QPushButton("Use light appearance")
        self.theme_button.clicked.connect(self._toggle_theme)
        github = QPushButton("Open OpenReef on GitHub")
        github.setIcon(bootstrap_icon("github", "#d1d1d6", 24))
        github.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/marine-ecologist/openreef/")
            )
        )
        card_layout.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(github, 0, Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(card)
        return page

    def _build_markertags_page(self) -> QWidget:
        """Placeholder catalogue for printable OpenReef field markers."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(14)
        title = QLabel("MarkerTags")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        subtitle = QLabel(
            "Choose a field marker design for scale and repeat-survey workflows. "
            "Downloadable STL packages will be added here."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        for name, description, availability in (
            (
                "MarkerTags",
                "Temporary metric-scale markers using tag36h11 AprilTags with a "
                "50 mm encoded-square edge.",
                "STL download · coming soon",
            ),
            (
                "Fixed reference markers",
                "Long-term site references for repeat surveys. Detection support "
                "will be added in a later release.",
                "STL download · planned",
            ),
            (
                "Scale and colour targets",
                "Combined reference targets for future scale and colour workflows.",
                "STL download · planned",
            ),
        ):
            card = QFrame()
            card.setObjectName("projectCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)
            heading = QLabel(name)
            heading.setObjectName("projectName")
            detail = QLabel(description)
            detail.setObjectName("pageSubtitle")
            detail.setWordWrap(True)
            download = QPushButton(availability)
            download.setEnabled(False)
            download.setToolTip(
                "This download will become available when the marker package is published."
            )
            card_layout.addWidget(heading)
            card_layout.addWidget(detail)
            card_layout.addStretch(1)
            card_layout.addWidget(download)
            cards.addWidget(card, 1)
        outer.addLayout(cards, 1)
        return page

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        QSettings().setValue("appearance/dark", self._dark_mode)
        self._apply_theme()

    def _apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(application_stylesheet(self._dark_mode))
        self.theme_button.setText(
            "Use light appearance" if self._dark_mode else "Use dark appearance"
        )
        theme_icon = "sun-fill" if self._dark_mode else "moon-stars-fill"
        self.theme_button.setIcon(bootstrap_icon(theme_icon, icon_color(self._dark_mode), 24))
        self._sync_navigation()
        if hasattr(self, "scene"):
            self.scene.set_theme(self._dark_mode)
        if hasattr(self, "points_page"):
            self.points_page.scene.set_theme(self._dark_mode)

    def _connect_controls(self) -> None:
        self.controls.fit_requested.connect(self.scene.fit_to_view)
        self.controls.set_view_requested.connect(self._set_preferred_view)
        self.controls.projection_changed.connect(self._set_parallel_projection)
        self.controls.display_mode_changed.connect(self.scene.set_display_mode)
        self.controls.point_size_changed.connect(self.scene.set_point_size)
        self.controls.standard_view_requested.connect(self.scene.set_standard_view)
        self.controls.open_requested.connect(self.open_model)
        self.controls.save_requested.connect(self._save_edited_model)
        self.controls.lasso_requested.connect(self._begin_lasso)
        self.controls.undo_requested.connect(self._undo_edit)
        self.controls.reset_requested.connect(self._reset_edits)
        self.controls.complexity_requested.connect(self._set_mesh_complexity)
        self.controls.content_mode_changed.connect(self._viewer_content_changed)
        self.controls.use_crop_requested.connect(self._use_crop_in_next_stage)
        self.controls.web_export_requested.connect(self._export_web)
        self.controls.compact_web_export_requested.connect(
            lambda: self._export_web(compact=True)
        )
        self.controls.open_web_requested.connect(self._open_web_export)
        self.controls.splat_cleanup_requested.connect(self._preview_splat_cleanup)
        self.controls.splat_cleanup_reset_requested.connect(self._reset_splat_cleanup)
        self.controls.splat_cleanup_save_requested.connect(self._save_cleaned_splat)
        self.controls.orthomosaic_angle_requested.connect(self._set_orthomosaic_angle)
        self.controls.orthomosaic_export_requested.connect(self._export_orthomosaic)
        self.input_page.dataset_path_changed.connect(self._sync_dataset_root)
        self.input_page.images_ready.connect(self._input_images_ready)
        self.render_page.dataset_path_changed.connect(self._sync_dataset_root)
        self.render_page.open_artifact_requested.connect(lambda path: self.load_path(Path(path)))
        self.render_page.crop_requested.connect(self._open_sparse_crop)
        self.render_page.tileset_requested.connect(self._export_tiled_web)
        self.points_page.roi_changed.connect(self._roi_changed)
        self.plotter.lasso_finished.connect(self._finish_lasso)
        self.plotter.lasso_cancelled.connect(self._lasso_cancelled)
        self.plotter.measurement_tool_selected.connect(self.measurements.begin)
        self.plotter.measurement_clear_requested.connect(self.measurements.clear_all)
        self.plotter.measurement_point_clicked.connect(
            self.measurements.add_display_point
        )
        self.plotter.measurement_close_requested.connect(
            self.measurements.close_polygon
        )
        self.plotter.measurement_backspace_requested.connect(
            self.measurements.remove_last_vertex
        )
        self.plotter.measurement_cancel_requested.connect(self.measurements.cancel)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.runner.artifact_ready.connect(self._dense_artifact_ready)
        self.runner.job_finished.connect(self._pipeline_finished)
        self.runner.running_changed.connect(self.input_page.set_pipeline_busy)
        self.input_runner.running_changed.connect(self.render_page.set_external_busy)

    @staticmethod
    def _load_orthographic_orientation() -> CameraOrientation | None:
        value = QSettings().value("viewer/orthographic_orientation", "", type=str)
        if not value:
            return None
        try:
            return CameraOrientation.from_json(value)
        except ValueError:
            QSettings().remove("viewer/orthographic_orientation")
            return None

    def _set_preferred_view(self) -> None:
        document = self.scene.document
        if (
            document is None
            or is_gaussian_splat(document)
            or self.viewer_stack.currentWidget() is not self.plotter.interactor
        ):
            QMessageBox.information(
                self,
                "Set view",
                "Open a mesh or point cloud in the native 3D viewer first.",
            )
            return
        try:
            orientation = CameraOrientation.capture(self.plotter)
        except ValueError as exc:
            QMessageBox.critical(self, "Could not set view", str(exc))
            return
        self._orthographic_orientation = orientation
        QSettings().setValue("viewer/orthographic_orientation", orientation.to_json())
        self.controls.set_preferred_view_ready(True)
        self.statusBar().showMessage(
            "View saved — future orthographic views will use this orientation"
        )

    def _set_parallel_projection(self, enabled: bool) -> None:
        if enabled and self._orthographic_orientation is not None:
            self._orthographic_orientation.apply(self.plotter)
        self.scene.set_parallel_projection(enabled)
        if enabled and self.scene.document is not None:
            self.scene.fit_to_view()

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

        self.set_view_action = QAction("&Set view", self)
        self.set_view_action.setToolTip(
            "Use the current camera orientation for future orthographic views"
        )
        self.set_view_action.triggered.connect(self._set_preferred_view)

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

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.set_view_action)

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
        self._sync_dataset_root(root)
        self.tabs.setCurrentWidget(self.input_scroll)
        self._sync_navigation()
        self.setWindowTitle(f"{root.name} — OpenReef 0.6.2")
        self.statusBar().showMessage(f"Dataset: {root}")

    def _sync_dataset_root(self, path: str | Path) -> None:
        if not str(path).strip():
            return
        root = Path(path).expanduser().resolve()
        project_changed = self._dataset_root is None or root != self._dataset_root
        self._dataset_root = root
        if root.is_dir():
            QSettings().setValue("workspace/last_dataset", str(root))
        self.input_page.set_dataset_root(root)
        self.render_page.set_dataset_root(root)
        self.points_page.set_dataset_root(root)
        try:
            sync_model_links(DatasetLayout(root))
        except OSError as exc:
            self.statusBar().showMessage(f"Dataset selected; mesh shortcuts unavailable: {exc}")
        sections = self._refresh_model_catalog()
        reloaded = self._reload_viewer_for_project(sections) if project_changed else None
        if hasattr(self, "project_name"):
            self.project_name.setText(root.name)
            self.project_path.setText(str(root))
        self.setWindowTitle(f"{root.name} — OpenReef 0.6.2")
        message = f"Dataset: {root}"
        if reloaded is not None:
            message += f" · Viewer reloaded: {reloaded.name}"
        self.statusBar().showMessage(message)

    def _input_images_ready(self, dataset: str) -> None:
        self._sync_dataset_root(dataset)
        count = self.render_page.dataset_summary.text()
        self.statusBar().showMessage(f"Input images ready — {count}")

    def open_model(self) -> None:
        start = str(self._dataset_root / "models") if self._dataset_root else ""
        filename, _ = QFileDialog.getOpenFileName(self, "Open reef model", start, MODEL_FILTER)
        if filename:
            self.load_path(Path(filename))

    def _refresh_model_catalog(
        self, selected: Path | None = None
    ) -> tuple[ModelCatalogSection, ...]:
        if self._dataset_root is None:
            self.controls.set_model_catalog(())
            return ()
        sections = discover_model_catalog(DatasetLayout(self._dataset_root))
        self.controls.set_model_catalog(sections, selected)
        return sections

    def _reload_viewer_for_project(
        self, sections: tuple[ModelCatalogSection, ...]
    ) -> Path | None:
        """Clear the old project scene and prepare the best result from the new project."""

        self._leave_embedded_renderers()
        self.scene.clear_document()
        self.viewer_stack.setCurrentWidget(self.plotter.interactor)
        self.controls.set_splat_mode(False)
        self.controls.set_tileset_mode(False)
        self.measurements.configure(None, (), available=False)
        self.controls.set_model_available(False)
        self.controls.set_mesh_available(False)
        self.controls.set_history_available(False)
        self.controls.set_stats("No model loaded for this project")
        self.controls.set_web_export_ready(None)
        self._last_web_export = None
        self._edit_full_resolution = None
        self._edit_history.clear()
        self._edit_operations.clear()

        preferred = preferred_model_path(sections)
        if preferred is not None:
            self.load_path(preferred, show_viewer=False)
            return preferred

        sparse = next(
            (section for section in sections if section.title == "Sparse cloud"),
            None,
        )
        if sparse and sparse.items and self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
            self.viewer_stack.setCurrentWidget(self.points_page)
            self.controls.select_sparse_view()
            self.controls.set_stats("Sparse points and registered cameras")
            return sparse.items[0].path
        return None

    def _viewer_markertag_metadata(self, source: Path) -> dict[str, object] | None:
        if self._dataset_root is None:
            return None
        try:
            source.resolve().relative_to(self._dataset_root.resolve())
        except (OSError, ValueError):
            return None
        return read_viewer_metadata(DatasetLayout(self._dataset_root).markertags_metadata)

    def _measurement_scale_is_valid(self, metadata: dict[str, object] | None) -> bool:
        if self._dataset_root is None or not has_metric_scale(metadata):
            return False
        return stage_output_exists(
            StageKey.MARKERTAGS, DatasetLayout(self._dataset_root)
        )

    def load_path(
        self,
        path: Path,
        *,
        select_in_catalog: bool = True,
        show_viewer: bool = True,
    ) -> None:
        self._leave_embedded_renderers()
        if path.name.casefold().endswith("_3d_tiles.json"):
            self._load_tiled_model(
                path,
                select_in_catalog=select_in_catalog,
                show_viewer=show_viewer,
            )
            return
        try:
            document = load_model(path)
        except ModelLoadError as exc:
            QMessageBox.critical(self, "Could not open model", str(exc))
            self.statusBar().showMessage("Model could not be opened")
            return
        splat = is_gaussian_splat(document)
        self.controls.set_tileset_mode(False)
        automatic_cleanup = None
        if splat:
            # Keep the document available to OpenReef actions, but avoid first
            # drawing the approximate VTK point representation underneath it.
            self.scene.set_document(document, render_splat=False)
            display_path = document.source
            try:
                automatic_cleanup = clean_gaussian_document(
                    document,
                    minimum_opacity=0.02,
                    maximum_scale_percentile=98.5,
                    maximum_aspect_ratio=50.0,
                    bounds=self._splat_roi_bounds(document.source),
                )
                display_path = Path(self._splat_preview_folder.name) / "openreef_splat_display.ply"
                write_gaussian_ply(automatic_cleanup.document, display_path)
            except (OSError, RuntimeError, ValueError):
                automatic_cleanup = None
            try:
                self.splat_page.load_path(display_path)
                self.viewer_stack.setCurrentWidget(self.splat_page)
            except (OSError, RuntimeError, ValueError) as exc:
                self.scene.set_document(document)
                self.viewer_stack.setCurrentWidget(self.plotter.interactor)
                self.statusBar().showMessage(f"Using Gaussian fallback renderer: {exc}")
        else:
            self.scene.set_document(document)
            self.viewer_stack.setCurrentWidget(self.plotter.interactor)
        metadata = self._viewer_markertag_metadata(document.source)
        stats = document.stats.as_text()
        if splat:
            stats += "\nRenderer: SuperSplat (WebGL)"
            if automatic_cleanup is not None:
                stats += f"\nDisplay-only halo filter: {automatic_cleanup.removed:,} removed"
        stats += f"\n\n{format_viewer_diagnostics(metadata)}"
        self.controls.set_stats(stats)
        self._edit_full_resolution = document
        self._edit_history.clear()
        self._edit_operations.clear()
        self._orthomosaic_view = None
        self.controls.reset_orthomosaic_angle()
        self._complexity_percent = 100
        self.controls.set_complexity(100)
        self.controls.set_model_available(
            True,
            (
                f"Gaussian splat — {document.stats.points:,} splats. "
                "Orbit and inspect it in the embedded true-splat renderer."
                if splat
                else f"Ready — {document.stats.points:,} points and "
                f"{document.stats.cells:,} cells."
            ),
            editable=not splat,
            exportable=not splat,
        )
        self.controls.set_splat_mode(splat)
        self.controls.set_splat_cleanup_available(
            splat,
            self._splat_roi_bounds(document.source) is not None,
        )
        if automatic_cleanup is not None:
            self.controls.set_splat_cleanup_status(
                f"Display filter active: {automatic_cleanup.retained:,} splats shown; "
                f"{automatic_cleanup.removed:,} halo outliers hidden. Source unchanged."
            )
        has_mesh = not splat and any(part.kind == "mesh" for part in document.parts)
        self.controls.set_mesh_available(has_mesh)
        self.measurements.configure(
            document,
            self.scene.mesh_actors,
            available=has_mesh and self._measurement_scale_is_valid(metadata),
        )
        self.controls.set_history_available(False)
        self.setWindowTitle(f"{document.source.name} — OpenReef Viewer 0.6.2")
        self.statusBar().showMessage(f"Loaded {document.source}")
        self.controls.set_workflow_crop_stage(self._workflow_stage(document))
        if select_in_catalog:
            self.controls.select_model(document.source)
        if show_viewer:
            self.tabs.setCurrentWidget(self.viewer_page)

    def _load_tiled_model(
        self,
        path: Path,
        *,
        select_in_catalog: bool,
        show_viewer: bool = True,
    ) -> None:
        try:
            manifest = read_tiled_model_manifest(path)
            self.tileset_page.load_path(manifest.viewer)
        except (OSError, RuntimeError, ValueError) as exc:
            self.controls.set_tileset_mode(False)
            QMessageBox.critical(self, "Could not open 3D Tiles", str(exc))
            self.statusBar().showMessage("3D Tiles model could not be opened")
            return
        self.viewer_stack.setCurrentWidget(self.tileset_page)
        self._edit_full_resolution = None
        self._edit_history.clear()
        self._edit_operations.clear()
        self.controls.set_splat_mode(False)
        self.controls.set_tileset_mode(True)
        self.controls.set_model_available(False)
        metadata = self._viewer_markertag_metadata(path)
        self.measurements.configure(None, (), available=False)
        self.controls.set_stats(
            f"Streaming 3D Tiles\nTileset: {manifest.tileset.name}\n"
            "Detail is fetched progressively for the current camera view.\n\n"
            f"{format_viewer_diagnostics(metadata)}"
        )
        self.setWindowTitle(f"{manifest.title} — OpenReef Viewer 0.6.2")
        self.statusBar().showMessage(f"Opened streaming 3D Tiles from {manifest.tileset}")
        if select_in_catalog:
            self.controls.select_model(path)
        if show_viewer:
            self.tabs.setCurrentWidget(self.viewer_page)

    def _leave_embedded_renderers(self) -> None:
        """Free embedded browser surfaces before switching viewer modes."""

        current = self.viewer_stack.currentWidget()
        if current not in {self.splat_page, self.tileset_page}:
            return
        self.viewer_stack.setCurrentWidget(self.plotter.interactor)
        if current is self.splat_page:
            self.splat_page.deactivate()
        else:
            self.tileset_page.deactivate()
        QApplication.processEvents()

    def _begin_lasso(self, mode: str) -> None:
        if self.scene.document is None:
            QMessageBox.information(self, "No model", "Open a model before drawing a lasso.")
            return
        self._lasso_mode = mode
        self.measurements.cancel()
        self.tabs.setCurrentWidget(self.viewer_page)
        self.plotter.begin_lasso()
        action = "keep what is inside" if mode == "keep" else "delete what is inside"
        message = f"Draw around the model area to {action}. Release to apply; Esc cancels."
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _tab_changed(self, index: int) -> None:
        self._sync_navigation()
        self._apply_theme()
        if (
            self.tabs.widget(index) is self.viewer_page
            and self.viewer_stack.currentWidget() is self.points_page
            and self._dataset_root is not None
        ):
            self.points_page.set_dataset_root(self._dataset_root)
        if self.tabs.widget(index) is not self.viewer_page:
            self.plotter.cancel_lasso()

    def _open_sparse_crop(self) -> None:
        self._leave_embedded_renderers()
        self.controls.set_tileset_mode(False)
        if self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
        self.viewer_stack.setCurrentWidget(self.points_page)
        self.controls.select_sparse_view()
        self.tabs.setCurrentWidget(self.viewer_page)
        self.points_page.begin_crop()

    def _viewer_content_changed(self, mode: str) -> None:
        if not mode:
            return
        sparse = mode == "view:sparse"
        if sparse and self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
        if sparse:
            self.measurements.configure(None, (), available=False)
            self._leave_embedded_renderers()
            self.controls.set_tileset_mode(False)
            self.viewer_stack.setCurrentWidget(self.points_page)
            self.plotter.cancel_lasso()
            self.controls.set_splat_mode(False)
            self.controls.set_model_available(False)
            self.controls.set_stats("Sparse points and registered cameras")
        elif mode.startswith("model:"):
            self.load_path(Path(mode.removeprefix("model:")), select_in_catalog=False)

    def _splat_roi_bounds(
        self,
        source: Path | None = None,
    ) -> tuple[float, float, float, float, float, float] | None:
        if self._dataset_root is None:
            return None
        if source is not None:
            try:
                source.resolve().relative_to(self._dataset_root.resolve())
            except (OSError, ValueError):
                return None
        roi_path = DatasetLayout(self._dataset_root).roi
        if not roi_path.is_file():
            return None
        try:
            return SparseROI.load(roi_path).bounds
        except (OSError, KeyError, TypeError, ValueError):
            return None

    def _build_splat_cleanup(self):
        document = self._edit_full_resolution
        if document is None or not is_gaussian_splat(document):
            raise ValueError("Open a Gaussian splat before using cleanup")
        minimum_opacity, scale_percentile, aspect_ratio, use_roi = (
            self.controls.splat_cleanup_options()
        )
        bounds = self._splat_roi_bounds(document.source) if use_roi else None
        return clean_gaussian_document(
            document,
            minimum_opacity=minimum_opacity,
            maximum_scale_percentile=scale_percentile,
            maximum_aspect_ratio=aspect_ratio,
            bounds=bounds,
        )

    def _preview_splat_cleanup(self) -> None:
        self.controls.set_splat_cleanup_status("Preparing cleanup preview…")
        QApplication.processEvents()
        try:
            result = self._build_splat_cleanup()
            preview = Path(self._splat_preview_folder.name) / "openreef_splat_preview.ply"
            write_gaussian_ply(result.document, preview)
            self.splat_page.load_path(preview)
            self.viewer_stack.setCurrentWidget(self.splat_page)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, "Could not preview Gaussian cleanup", str(exc))
            self.controls.set_splat_cleanup_status("Cleanup preview was not created.")
            return
        message = (
            f"Preview: {result.retained:,} splats kept; {result.removed:,} removed. "
            "The original file has not changed."
        )
        self.controls.set_splat_cleanup_status(message)
        self.statusBar().showMessage(message)

    def _reset_splat_cleanup(self) -> None:
        document = self._edit_full_resolution
        if document is None or not is_gaussian_splat(document):
            return
        try:
            self.splat_page.load_path(document.source)
            self.viewer_stack.setCurrentWidget(self.splat_page)
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "Could not restore Gaussian splat", str(exc))
            return
        self.controls.set_splat_cleanup_status(
            "Original restored. Cleanup settings remain available for another preview."
        )

    def _save_cleaned_splat(self) -> None:
        document = self._edit_full_resolution
        if document is None or not is_gaussian_splat(document):
            return
        if self._dataset_root is not None:
            layout = DatasetLayout(self._dataset_root)
            layout.models.mkdir(parents=True, exist_ok=True)
            suggested = layout.models / f"{dataset_label(layout)}_gaussian_cleaned.ply"
        else:
            suggested = document.source.with_name(f"{document.source.stem}_cleaned.ply")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save cleaned Gaussian splat",
            str(suggested),
            "Gaussian splat (*.ply)",
        )
        if not filename:
            return
        destination = Path(filename)
        if destination.suffix.lower() != ".ply":
            destination = destination.with_suffix(".ply")
        self.controls.set_splat_cleanup_status("Saving cleaned Gaussian splat…")
        QApplication.processEvents()
        try:
            result = self._build_splat_cleanup()
            write_gaussian_ply(result.document, destination)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not save cleaned Gaussian splat", str(exc))
            self.controls.set_splat_cleanup_status("Cleaned splat was not saved.")
            return
        if self._dataset_root is not None:
            self._refresh_model_catalog(destination)
        message = (
            f"Saved {destination.name}: {result.retained:,} splats kept; "
            f"{result.removed:,} removed."
        )
        self.controls.set_splat_cleanup_status(message)
        self.statusBar().showMessage(message)

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
        if document.material_source is not None:
            message = (
                "Textured-triangle trim applied — retained cells keep their original "
                f"image mapping; {before.cells:,} → {after.cells:,} cells."
            )
        else:
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
        metadata = self._viewer_markertag_metadata(document.source)
        self.controls.set_stats(
            f"{document.stats.as_text()}\n\n{format_viewer_diagnostics(metadata)}"
        )
        self.measurements.configure(
            document,
            self.scene.mesh_actors,
            available=self._measurement_scale_is_valid(metadata)
            and any(part.kind == "mesh" for part in document.parts),
        )
        self.setWindowTitle(f"{document.source.name} — OpenReef Viewer 0.6.2")

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
        is_textured_glb = document.material_source is not None
        if is_textured_glb and self._complexity_percent < 100:
            QMessageBox.information(
                self,
                "Return to 100% complexity",
                "Saving an edited textured GLB preserves complete source triangles. "
                "Return Mesh complexity to 100%, then save. Use the separately generated "
                "Medium or Low textured GLB when a smaller textured model is needed.",
            )
            return
        if self._dataset_root:
            layout = DatasetLayout(self._dataset_root)
            layout.models.mkdir(parents=True, exist_ok=True)
            if is_textured_glb:
                suggested = layout.models / f"{dataset_label(layout)}_textured_mesh_edited.glb"
            else:
                suffix = (
                    f"mesh_{self._complexity_percent}pct"
                    if self._complexity_percent < 100
                    else "mesh_edited"
                )
                suggested = layout.models / f"{dataset_label(layout)}_{suffix}.ply"
        else:
            extension = ".glb" if is_textured_glb else ".ply"
            suggested = document.source.with_name(f"{document.source.stem}_edited{extension}")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save edited model",
            str(suggested),
            EDITED_GLB_FILTER if is_textured_glb else EDITED_MODEL_FILTER,
        )
        if not filename:
            return
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(".glb" if is_textured_glb else ".ply")
        try:
            self.controls.set_edit_status("Preparing model at the selected complexity…")
            QApplication.processEvents()
            export_document = self._document_at_complexity(self._complexity_percent)
            destination = save_document(export_document, path)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not save edited model", str(exc))
            return
        message = f"Saved edited model to {destination}"
        if self._dataset_root is not None:
            self._refresh_model_catalog(self.scene.document.source)
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
                displayed = ModelDocument(
                    source=preview_path,
                    parts=displayed.parts,
                    material_source=displayed.material_source,
                )
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

    def _workflow_stage(self, document: ModelDocument) -> str | None:
        if document.material_source is not None:
            return "textured"
        return "dense" if self._dense_source_output(document.source) is not None else None

    def _dense_source_output(self, source: Path) -> Path | None:
        if self._dataset_root is None:
            return None
        layout = DatasetLayout(self._dataset_root)
        candidates = (
            layout.dense_cloud,
            layout.dense_cloud_original,
            layout.dense_cloud_medium,
            layout.dense_cloud_low,
        )
        resolved = source.expanduser().resolve()
        for candidate in candidates:
            cropped = dense_crop_for_output(candidate)
            if resolved in (candidate.resolve(), cropped.resolve()):
                return candidate
        return None

    def _use_crop_in_next_stage(self) -> None:
        source_document = self._edit_full_resolution
        if source_document is None:
            return
        stage = self._workflow_stage(source_document)
        if stage == "textured":
            self._save_edited_model()
            return
        dense_source = self._dense_source_output(source_document.source)
        if dense_source is None:
            QMessageBox.information(
                self,
                "No workflow handoff",
                "Open a dataset dense-cloud output before creating a Surface Mesh crop.",
            )
            return
        if not self._edit_operations:
            QMessageBox.information(
                self,
                "Draw a crop first",
                "Draw a retain or delete lasso before sending this dense cloud to Surface Mesh.",
            )
            return
        destination = dense_crop_for_output(dense_source)
        try:
            document = self._document_at_complexity(100)
            save_document(document, destination)
            if self._dataset_root is not None:
                sync_model_links(DatasetLayout(self._dataset_root))
                self.render_page.set_dataset_root(self._dataset_root)
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not save processing crop", str(exc))
            return
        message = (
            f"Dense crop saved to {destination.name}. Surface Mesh will use this crop "
            "instead of the complete cloud."
        )
        self.controls.set_edit_status(message)
        self.statusBar().showMessage(message)

    def _export_web(self, compact: bool = False) -> None:
        if self.scene.document is None or self._edit_full_resolution is None:
            return
        if self.scene.document.material_source is not None and self._complexity_percent < 100:
            QMessageBox.information(
                self,
                "Return to 100% complexity",
                "Return Viewer complexity to 100% before exporting a textured GLB. "
                "Open a generated Medium or Low GLB when a smaller web model is needed.",
            )
            return
        source_parent = self._edit_full_resolution.source.parent
        if self._dataset_root is not None:
            dataset_root = self._dataset_root
        elif source_parent.name in {"models", "openmvs"}:
            dataset_root = source_parent.parent
        else:
            dataset_root = source_parent
        output = DatasetLayout(dataset_root).web_export
        self.controls.set_web_export_ready(None)
        action = "Creating compact openreef-web…" if compact else "Creating openreef-web…"
        self.controls.web_status.setText(action)
        QApplication.processEvents()
        try:
            with TemporaryDirectory(prefix="openreef-web-") as temporary:
                source = self._edit_full_resolution.source
                if self._edit_operations or self._complexity_percent < 100:
                    suffix = ".glb" if self.scene.document.material_source else ".ply"
                    source = Path(temporary) / f"edited{suffix}"
                    save_document(
                        self._document_at_complexity(self._complexity_percent),
                        source,
                    )
                result = export_web_viewer(
                    source,
                    output,
                    title=dataset_root.name,
                    compact=compact,
                )
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not create openreef-web", str(exc))
            self.controls.web_status.setText("Web export failed.")
            return
        self._last_web_export = result.folder
        model_size = result.model.stat().st_size
        if model_size <= GITHUB_REGULAR_FILE_LIMIT:
            pages_status = "GitHub Pages-ready"
        else:
            size_mib = model_size / (1024 * 1024)
            pages_status = f"{size_mib:.1f} MiB model exceeds GitHub's 100 MiB limit"
        self.controls.set_web_export_ready(f"{result.folder}\n{pages_status}")
        self.statusBar().showMessage(f"Created {result.folder}")

    def _open_web_export(self) -> None:
        if self._last_web_export is None:
            return
        launcher = self._last_web_export / "Open OpenReef Web.command"
        if launcher.is_file():
            QProcess.startDetached("/usr/bin/open", [str(launcher)])

    def _export_tiled_web(self) -> None:
        if self._dataset_root is None:
            QMessageBox.information(
                self,
                "Choose a dataset",
                "Choose an OpenReef dataset before packaging a 3D Tiles model.",
            )
            return
        if self.runner.is_running or self.input_runner.is_running:
            QMessageBox.information(
                self,
                "Processing is running",
                "Wait for the current image or reconstruction process to finish first.",
            )
            return
        if self._tile_process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(
                self,
                "3D Tiles build is running",
                "The current spatial tileset is still being generated.",
            )
            return
        layout = DatasetLayout(self._dataset_root)
        layout.models.mkdir(parents=True, exist_ok=True)
        textured_models = sorted(
            (
                path
                for path in layout.models.glob("*.glb")
                if "textur" in path.name.casefold()
            ),
            key=lambda path: ("compact" in path.name.casefold(), path.name.casefold()),
        )
        chooser_start = textured_models[0] if textured_models else layout.models
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose the highest-detail textured GLB to tile",
            str(chooser_start),
            "Textured GLB models (*.glb)",
        )
        if not filename:
            return
        self._tile_build_layout = layout
        self._tile_build_buffer = ""
        self._tile_build_log.clear()
        self.render_page.set_external_busy(True)
        self.render_page.tileset_checkpoint.set_building(True, 0, "Starting spatial tiler")
        self.statusBar().showMessage(f"Building spatial 3D Tiles from {Path(filename).name}…")

        environment = QProcessEnvironment.systemEnvironment()
        source_root = str(Path(__file__).resolve().parents[2])
        python_path = environment.value("PYTHONPATH")
        environment.insert(
            "PYTHONPATH",
            source_root if not python_path else f"{source_root}:{python_path}",
        )
        environment.insert("PYTHONUNBUFFERED", "1")
        search_path = environment.value("PATH")
        for folder in ("/opt/homebrew/bin", "/usr/local/bin"):
            if Path(folder).is_dir() and folder not in search_path.split(":"):
                search_path = f"{folder}:{search_path}"
        environment.insert("PATH", search_path)
        self._tile_process.setProcessEnvironment(environment)
        self._tile_process.setWorkingDirectory(str(layout.root))
        self._tile_process.setProgram(sys.executable)
        self._tile_process.setArguments(
            [
                "-m",
                "openreef.tile_builder",
                "--model",
                filename,
                "--dataset",
                str(layout.root),
            ]
        )
        self._tile_process.start()

    def _tile_build_output_ready(self) -> None:
        chunk = bytes(self._tile_process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        self._tile_build_buffer += chunk
        lines = self._tile_build_buffer.split("\n")
        self._tile_build_buffer = lines.pop()
        for line in lines:
            clean = line.rstrip("\r")
            self._tile_build_log.append(clean)
            if len(self._tile_build_log) > 80:
                self._tile_build_log.pop(0)
            if clean.startswith("OPENREEF_TILE_PROGRESS\t"):
                parts = clean.split("\t", 2)
                if len(parts) == 3:
                    try:
                        percent = int(parts[1])
                    except ValueError:
                        continue
                    self.render_page.tileset_checkpoint.set_building(
                        True,
                        percent,
                        parts[2],
                    )
                    self.statusBar().showMessage(parts[2])
            elif clean.startswith("OPENREEF_PROGRESS\t"):
                parts = clean.split("\t", 3)
                if len(parts) == 4:
                    try:
                        copied, total = int(parts[1]), int(parts[2])
                    except ValueError:
                        continue
                    percent = 88 + round(10 * copied / max(total, 1))
                    self.render_page.tileset_checkpoint.set_building(
                        True,
                        percent,
                        parts[3],
                    )
                    self.statusBar().showMessage(parts[3])

    def _tile_build_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        self._tile_build_output_ready()
        layout = self._tile_build_layout
        self._tile_build_layout = None
        self.render_page.set_external_busy(False)
        self.render_page.tileset_checkpoint.set_building(False)
        success = (
            exit_status == QProcess.ExitStatus.NormalExit
            and exit_code == 0
            and layout is not None
            and layout.tiled_model_manifest.is_file()
        )
        if not success:
            details = "\n".join(line for line in self._tile_build_log[-16:] if line).strip()
            QMessageBox.critical(
                self,
                "Could not build 3D Tiles",
                details or "The spatial tiler stopped before producing a tileset.",
            )
            self.statusBar().showMessage("3D Tiles build failed")
            if layout is not None:
                self.render_page.set_dataset_root(layout.root)
            return
        self._last_web_export = layout.tiled_web_export
        self.render_page.set_dataset_root(layout.root)
        self._refresh_model_catalog(layout.tiled_model_manifest)
        self.statusBar().showMessage(
            f"3D Tiles built and added to Viewer: {layout.tiled_model_manifest.name}"
        )
        self.load_path(layout.tiled_model_manifest)

    def _tile_build_error(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.ProcessError.FailedToStart:
            return
        layout = self._tile_build_layout
        self._tile_build_layout = None
        self.render_page.set_external_busy(False)
        self.render_page.tileset_checkpoint.set_building(False)
        if layout is not None:
            self.render_page.set_dataset_root(layout.root)
        QMessageBox.critical(
            self,
            "Could not start 3D Tiles build",
            "OpenReef could not start its spatial tiling process.",
        )
        self.statusBar().showMessage("3D Tiles build could not start")

    def _roi_changed(self, path: str) -> None:
        if self._dataset_root is None:
            return
        self.render_page.set_dataset_root(self._dataset_root)
        message = (
            "Processing ROI saved. OpenMVS import and every later stage will use "
            "the crop instead of the complete reconstruction."
            if path
            else "Processing ROI cleared; rerun OpenMVS import for the complete model."
        )
        self.statusBar().showMessage(message)

    def _dense_artifact_ready(self, path: str) -> None:
        if self._dataset_root is not None:
            try:
                sync_model_links(DatasetLayout(self._dataset_root))
            except OSError:
                pass
            self._refresh_model_catalog()
        self.statusBar().showMessage(f"Model ready for 3D Viewer: {path}")

    def _pipeline_finished(self, success: bool, message: str) -> None:
        if success and self._dataset_root is not None:
            self.points_page.set_dataset_root(self._dataset_root)
            self.render_page.set_dataset_root(self._dataset_root)
            self._refresh_model_catalog()
        self.statusBar().showMessage(message)

    def save_screenshot(self) -> None:
        embedded = self.viewer_stack.currentWidget() in {
            self.splat_page,
            self.tileset_page,
        }
        if self.scene.document is None and not embedded:
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
            if self.viewer_stack.currentWidget() is self.splat_page:
                self.splat_page.save_screenshot(path)
            elif self.viewer_stack.currentWidget() is self.tileset_page:
                self.tileset_page.save_screenshot(path)
            else:
                self.plotter.screenshot(str(path))
        except Exception as exc:
            QMessageBox.critical(self, "Could not save screenshot", str(exc))
            return
        self.statusBar().showMessage(f"Saved screenshot to {path}")

    def _set_orthomosaic_angle(self) -> None:
        document = self.scene.document
        if (
            document is None
            or is_gaussian_splat(document)
            or self.viewer_stack.currentWidget() is not self.plotter.interactor
        ):
            QMessageBox.information(
                self,
                "Orthomosaic angle",
                "Open a mesh or point cloud in the native 3D viewer first.",
            )
            return
        self._orthomosaic_view = CameraView.capture(self.plotter)
        self.controls.set_orthomosaic_angle_ready()
        self.statusBar().showMessage("Orthomosaic viewing angle saved")

    def _export_orthomosaic(self) -> None:
        document = self.scene.document
        if document is None or self._orthomosaic_view is None:
            QMessageBox.information(
                self,
                "Set an angle first",
                "Rotate the model, then choose Set current viewing angle.",
            )
            return
        default_name = f"{document.source.stem}_orthomosaic.png"
        default_path = (
            self._dataset_root / "models" / default_name
            if self._dataset_root is not None
            else Path(default_name)
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export visual orthomosaic",
            str(default_path),
            "PNG image (*.png)",
        )
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")

        longest_edge, transparent = self.controls.orthomosaic_options()
        dimensions = orthomosaic_image_size(
            longest_edge,
            max(1, self.plotter.width()),
            max(1, self.plotter.height()),
        )
        original_view = CameraView.capture(self.plotter)
        original_mode = self.controls.display_mode.currentText()
        has_mesh = any(part.kind == "mesh" for part in document.parts)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._orthomosaic_view.apply(self.plotter)
            self.plotter.camera.parallel_projection = True
            if has_mesh:
                self.scene.set_display_mode("Solid")
            self.scene.fit_to_view()
            self.plotter.screenshot(
                str(path),
                transparent_background=transparent,
                window_size=dimensions,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.critical(self, "Could not export orthomosaic", str(exc))
            return
        finally:
            if has_mesh:
                self.scene.set_display_mode(original_mode)
            original_view.apply(self.plotter)
            QApplication.restoreOverrideCursor()

        self.statusBar().showMessage(
            f"Exported {dimensions[0]:,} × {dimensions[1]:,} visual orthomosaic to {path}"
        )

    def save_viewpoint(self) -> None:
        if self.viewer_stack.currentWidget() in {self.splat_page, self.tileset_page}:
            QMessageBox.information(
                self,
                "Embedded viewer viewpoint",
                "Embedded viewer cameras are not yet interchangeable with OpenReef's "
                "mesh viewpoint format. Use the embedded viewer's Frame and Reset "
                "controls instead.",
            )
            return
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
        if self.viewer_stack.currentWidget() in {self.splat_page, self.tileset_page}:
            QMessageBox.information(
                self,
                "Embedded viewer viewpoint",
                "Saved mesh viewpoints cannot yet be applied to an embedded viewer.",
            )
            return
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
        tile_building = self._tile_process.state() != QProcess.ProcessState.NotRunning
        busy = self.runner.is_running or self.input_runner.is_running or tile_building
        if busy:
            answer = QMessageBox.question(
                self,
                "Processing is still running",
                "Stop the active processing or export and close OpenReef?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.runner.cancel()
            self.input_runner.stop()
            if tile_building:
                self._tile_process.terminate()
        self.plotter.close()
        self.points_page.plotter.close()
        self.splat_page.shutdown()
        self.tileset_page.shutdown()
        self._splat_preview_folder.cleanup()
        event.accept()

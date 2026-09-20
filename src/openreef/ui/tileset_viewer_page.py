"""Embedded browser page for viewing a packaged OpenReef 3D Tiles model."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        """Keep local tile requests out of the processing terminal."""


class TilesetAssetServer:
    """Serve one generated OpenReef Web folder on a loopback-only address."""

    def __init__(self) -> None:
        self._http: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None
        self._folder: Path | None = None

    def load_viewer(self, index: str | Path) -> str:
        viewer = Path(index).expanduser().resolve()
        if not viewer.is_file():
            raise FileNotFoundError(viewer)
        folder = viewer.parent
        if self._http is None or folder != self._folder:
            self.close()
            handler = partial(_QuietStaticHandler, directory=str(folder))
            self._http = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            self._http.daemon_threads = True
            self._thread = Thread(target=self._http.serve_forever, daemon=True)
            self._thread.start()
            self._folder = folder
        port = self._http.server_address[1]
        relative = viewer.relative_to(folder).as_posix()
        return f"http://127.0.0.1:{port}/{relative}"

    def close(self) -> None:
        if self._http is None:
            return
        self._http.shutdown()
        self._http.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._http = None
        self._thread = None
        self._folder = None


class TilesetViewerPage(QWidget):
    """Host the generated streaming viewer inside OpenReef."""

    load_status = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._server = TilesetAssetServer()
        self._current_url = ""
        self._view = None
        self._web_view_type = None
        self._web_settings_type = None

        layout = QVBoxLayout(self)
        self._layout = layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("splatViewerToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 6, 10, 6)
        self.status_label = QLabel("Streaming 3D Tiles viewer")
        self.status_label.setObjectName("mutedLabel")
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addStretch(1)
        self.reload_button = QPushButton("Reload")
        self.reload_button.setToolTip("Reload the current streaming 3D Tiles view.")
        self.reload_button.clicked.connect(self.reload)
        toolbar_layout.addWidget(self.reload_button)
        self.browser_button = QPushButton("Open in browser")
        self.browser_button.setToolTip(
            "Open the local streaming 3D Tiles viewer in your default browser."
        )
        self.browser_button.clicked.connect(self.open_in_browser)
        toolbar_layout.addWidget(self.browser_button)
        layout.addWidget(toolbar)

        try:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

            self._web_view_type = QWebEngineView
            self._web_settings_type = QWebEngineSettings
            self._create_view()
        except ImportError:
            message = QLabel(
                "The embedded 3D Tiles viewer is unavailable. "
                "Use Open in browser to view this model."
            )
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setWordWrap(True)
            layout.addWidget(message, 1)

    def _create_view(self) -> None:
        if self._view is not None or self._web_view_type is None:
            return
        self._view = self._web_view_type(self)
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        settings = self._view.settings()
        settings.setAttribute(self._web_settings_type.WebGLEnabled, True)
        settings.setAttribute(self._web_settings_type.Accelerated2dCanvasEnabled, True)
        self._view.loadStarted.connect(self._load_started)
        self._view.loadProgress.connect(self._load_progress)
        self._view.loadFinished.connect(self._load_finished)
        self._layout.addWidget(self._view, 1)

    def load_path(self, viewer: str | Path) -> None:
        viewer_path = Path(viewer)
        self._current_url = self._server.load_viewer(viewer_path)
        self.status_label.setText(f"Loading {viewer_path.parent.name}…")
        self._create_view()
        if self._view is not None:
            nonce = str(viewer_path.stat().st_mtime_ns)
            self._view.setUrl(QUrl(f"{self._current_url}?v={nonce}"))

    def reload(self) -> None:
        if self._view is not None and self._current_url:
            self._view.reload()

    def open_in_browser(self) -> None:
        if self._current_url:
            QDesktopServices.openUrl(QUrl(self._current_url))

    def save_screenshot(self, path: str | Path) -> None:
        if self._view is None:
            raise RuntimeError("The embedded 3D Tiles viewer is unavailable")
        if not self._view.grab().save(str(path)):
            raise OSError(f"Could not write screenshot to {path}")

    def deactivate(self) -> None:
        if self._view is None:
            return
        view = self._view
        self._view = None
        view.stop()
        view.setUrl(QUrl("about:blank"))
        self._layout.removeWidget(view)
        view.hide()
        view.setParent(None)
        view.deleteLater()
        self.status_label.setText("Streaming 3D Tiles viewer paused")

    def shutdown(self) -> None:
        self.deactivate()
        self._server.close()

    def _load_started(self) -> None:
        self.status_label.setText("Loading 3D Tiles viewer…")

    def _load_progress(self, percent: int) -> None:
        self.status_label.setText(f"Loading 3D Tiles viewer… {percent}%")

    def _load_finished(self, success: bool) -> None:
        message = "3D Tiles viewer ready" if success else "3D Tiles viewer could not load"
        self.status_label.setText(message)
        self.load_status.emit(message)

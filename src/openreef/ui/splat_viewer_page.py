"""Embedded browser page for viewing true Gaussian splats."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

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

from openreef.ui.theme import ASSET_FOLDER


class _SplatRequestHandler(BaseHTTPRequestHandler):
    """Serve the bundled viewer and the currently selected model."""

    server: _SplatHTTPServer

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        route = urlparse(self.path).path
        if route in {"/", "/index.html"}:
            self._send_file(self.server.asset_folder / "index.html", "text/html; charset=utf-8")
            return
        if route == "/index.css":
            self._send_file(self.server.asset_folder / "index.css", "text/css; charset=utf-8")
            return
        if route == "/index.js":
            self._send_file(self.server.asset_folder / "index.js", "text/javascript; charset=utf-8")
            return
        if route == "/settings.json":
            self._send_file(
                self.server.asset_folder / "settings.json",
                "application/json; charset=utf-8",
                no_cache=True,
            )
            return
        if route == "/model.ply" and self.server.model_path is not None:
            self._send_file(self.server.model_path, "application/octet-stream", no_cache=True)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _send_file(self, path: Path, content_type: str, *, no_cache: bool = False) -> None:
        try:
            size = path.stat().st_size
            handle = path.open("rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        with handle:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Access-Control-Allow-Origin", "*")
            if no_cache:
                self.send_header("Cache-Control", "no-store, max-age=0")
            self.end_headers()
            while chunk := handle.read(1024 * 1024):
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep local model requests out of the processing terminal."""


class _SplatHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, asset_folder: Path) -> None:
        self.asset_folder = asset_folder
        self.model_path: Path | None = None
        super().__init__(("127.0.0.1", 0), _SplatRequestHandler)


class SplatAssetServer:
    """Small loopback-only server needed by the browser renderer."""

    def __init__(self) -> None:
        self._http: _SplatHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def running(self) -> bool:
        return self._http is not None

    def load_model(self, path: Path) -> str:
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if self._http is None:
            asset_folder = ASSET_FOLDER / "supersplat"
            if not (asset_folder / "index.html").is_file():
                raise FileNotFoundError("Bundled SuperSplat viewer assets are missing")
            self._http = _SplatHTTPServer(asset_folder)
            self._thread = Thread(target=self._http.serve_forever, daemon=True)
            self._thread.start()
        self._http.model_path = path
        port = self._http.server_address[1]
        # WebGL is used inside Qt for broad Mac compatibility. The same official
        # bundle can choose WebGPU when opened in a current external browser.
        return (
            f"http://127.0.0.1:{port}/index.html"
            "?content=/model.ply&settings=/settings.json&webgl&aa&noanim"
        )

    def close(self) -> None:
        if self._http is None:
            return
        self._http.shutdown()
        self._http.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._http = None
        self._thread = None


class SplatViewerPage(QWidget):
    """Host the official SuperSplat runtime inside OpenReef."""

    load_status = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._server = SplatAssetServer()
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
        self.status_label = QLabel("Gaussian splat renderer")
        self.status_label.setObjectName("mutedLabel")
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addStretch(1)
        self.reload_button = QPushButton("Reload")
        self.reload_button.setToolTip("Reload the current Gaussian splat in the viewer.")
        self.reload_button.clicked.connect(self.reload)
        toolbar_layout.addWidget(self.reload_button)
        self.browser_button = QPushButton("Open in browser")
        self.browser_button.setToolTip(
            "Open the local Gaussian viewer in your default browser for WebGPU support."
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
                "The embedded Gaussian renderer is unavailable. "
                "Use Open in browser to view this model."
            )
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setWordWrap(True)
            layout.addWidget(message, 1)

    @property
    def available(self) -> bool:
        return self._web_view_type is not None

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

    def load_path(self, path: str | Path) -> None:
        model_path = Path(path)
        self._current_url = self._server.load_model(model_path)
        self.status_label.setText(f"Loading {model_path.name}…")
        self.load_status.emit(self.status_label.text())
        self._create_view()
        if self._view is not None:
            # A query nonce prevents Chromium from reusing the previous PLY.
            nonce = str(model_path.stat().st_mtime_ns)
            self._view.setUrl(QUrl(f"{self._current_url}&v={nonce}"))

    def reload(self) -> None:
        if self._view is not None and self._current_url:
            self._view.reload()

    def open_in_browser(self) -> None:
        if self._current_url:
            # Let a current standalone browser choose WebGPU. The embedded view
            # keeps the explicit WebGL flag for compatibility with Qt Chromium.
            QDesktopServices.openUrl(QUrl(self._current_url.replace("&webgl", "")))

    def save_screenshot(self, path: str | Path) -> None:
        if self._view is None:
            raise RuntimeError("The embedded Gaussian renderer is unavailable")
        if not self._view.grab().save(str(path)):
            raise OSError(f"Could not write screenshot to {path}")

    def deactivate(self) -> None:
        """Release Chromium's surface before a native VTK model is displayed."""

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
        self.status_label.setText("Gaussian splat renderer paused")

    def shutdown(self) -> None:
        self.deactivate()
        self._server.close()

    def _load_started(self) -> None:
        self.status_label.setText("Loading Gaussian splat…")

    def _load_progress(self, percent: int) -> None:
        self.status_label.setText(f"Loading Gaussian splat… {percent}%")

    def _load_finished(self, success: bool) -> None:
        message = "Gaussian splat ready" if success else "Gaussian renderer could not load"
        self.status_label.setText(message)
        self.load_status.emit(message)

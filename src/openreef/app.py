"""Application entry point."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

os.environ.setdefault("QT_API", "pyside6")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenReef reconstruction workspace and 3D viewer")
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="dataset folder or PLY, OBJ, or GLB model to open",
    )
    parser.add_argument("--version", action="version", version="OpenReef 0.5.0")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from openreef.ui.main_window import MainWindow

    application_args = sys.argv if argv is None else [sys.argv[0], *argv]
    app = QApplication.instance() or QApplication(application_args)
    app.setApplicationName("OpenReef")
    app.setOrganizationName("OpenReef")
    icon_path = Path(__file__).with_name("assets") / "openreef-icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow(restore_last_dataset=args.path is None)
    window.show()

    if args.path is not None:
        initial_path = args.path.expanduser()

        def open_initial_path() -> None:
            if initial_path.is_dir():
                window.set_dataset_root(initial_path)
            else:
                window.load_path(initial_path)

        # Let macOS paint the application window before image thumbnails or a
        # large 3D model are loaded from the initial path.
        QTimer.singleShot(100, open_initial_path)
    return app.exec()

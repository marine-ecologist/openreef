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

STYLE = """
QMainWindow, QWidget { background: #101a20; color: #dce9ec; }
QMenuBar, QMenu, QStatusBar { background: #17252d; color: #dce9ec; }
QMenuBar::item:selected, QMenu::item:selected { background: #276575; }
QTabWidget::pane { border: 0; border-top: 1px solid #314650; }
QTabBar::tab {
    background: #17252d;
    border: 0;
    border-right: 1px solid #283b44;
    padding: 11px 28px;
    font-weight: 600;
}
QTabBar::tab:selected { background: #21414c; color: #72d0d9; }
QTabBar::tab:hover:!selected { background: #1c3039; }
QGroupBox {
    border: 1px solid #314650;
    border-radius: 5px;
    margin-top: 9px;
    padding-top: 9px;
    font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background: #1c3039;
    border: 1px solid #3a5661;
    border-radius: 4px;
    padding: 6px 8px;
}
QPushButton:hover { background: #24505d; border-color: #58aebe; }
QPushButton:pressed { background: #173b45; }
QTextEdit, QPlainTextEdit {
    background: #071015;
    border: 1px solid #314650;
    border-radius: 4px;
    font-family: monospace;
}
QScrollArea { border: 0; }
QSlider::groove:horizontal { height: 4px; background: #314650; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: #63c2cf; }
QLabel#heading { font-size: 22px; font-weight: 700; color: #69cad5; }
QLabel#subtitle { color: #90aab2; margin-bottom: 4px; }
QLabel#pageTitle { font-size: 24px; font-weight: 700; color: #69cad5; }
QLabel#pageSubtitle, QLabel#datasetSummary, QLabel#terminalHint, QLabel#stageOutput {
    color: #90aab2;
}
QLabel#fieldLabel, QLabel#stageNumber { color: #62c8cf; font-size: 11px; font-weight: 700; }
QLabel#flowArrow { color: #4f8995; font-size: 25px; }
QFrame#stageCard {
    background: #14242c;
    border: 1px solid #314650;
    border-radius: 7px;
}
QFrame#stageCard[state="running"] { border: 2px solid #63c2cf; }
QFrame#stageCard[state="complete"], QFrame#stageCard[state="ready"] { border-color: #55a97a; }
QFrame#stageCard[state="failed"] { border-color: #d06868; }
QPushButton#primaryButton { background: #266777; border-color: #62c8cf; font-weight: 700; }
QProgressBar {
    background: #101a20;
    border: 1px solid #314650;
    border-radius: 3px;
    text-align: center;
}
QProgressBar::chunk { background: #54b9c6; }
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenReef reconstruction workspace and 3D viewer")
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="dataset folder or PLY, OBJ, or GLB model to open",
    )
    parser.add_argument("--version", action="version", version="OpenReef 0.2.0")
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
    app.setStyleSheet(STYLE)

    window = MainWindow()
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

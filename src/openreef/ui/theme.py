"""OpenReef Carbon styling and Bootstrap icon helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ASSET_FOLDER = Path(__file__).resolve().parent.parent / "assets"
PRIMARY_ACCENT = "#5B8CFF"
RUNNING_ACCENT = "#38A9FF"
WARNING_ACCENT = "#F05A5A"


@lru_cache(maxsize=32)
def bootstrap_icon(name: str, color: str = "#ffffff", size: int = 32) -> QIcon:
    """Render a bundled Bootstrap SVG using the requested theme color."""
    source = ASSET_FOLDER / f"bi-{name}.svg"
    try:
        svg = source.read_text(encoding="utf-8").replace("currentColor", color)
    except OSError:
        return QIcon()
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def application_stylesheet(dark: bool) -> str:
    """Return OpenReef's quiet Carbon theme and its retained light counterpart."""
    if dark:
        body = "#212121"
        surface = "#2f2f2f"
        raised = "#333333"
        step_surface = "#292929"
        selected_step = "#303645"
        text = "#ececec"
        muted = "#afafaf"
        border = "#424242"
        input_bg = "#262626"
        input_text = "#ececec"
        terminal = "#171717"
        tab_selected = "#212121"
        scroll_handle = "#505050"
        button_bg = "#303030"
        button_hover = "#383838"
        button_pressed = "#282828"
        button_text = "#ececec"
        disabled_text = "#777777"
        status_bg = "#242424"
    else:
        body = "#f2f5f5"
        surface = "#fbfcfc"
        raised = "#edf1f2"
        step_surface = "#f5f7f7"
        text = "#29363c"
        muted = "#708087"
        border = "#d7e0e2"
        input_bg = "#ffffff"
        input_text = "#29363c"
        terminal = "#f8fafa"
        tab_selected = "#f2f5f5"
        scroll_handle = "#aebbc0"
        button_bg = "#e5eaec"
        button_hover = "#dce4e6"
        button_pressed = "#d3dcdf"
        button_text = "#29363c"
        disabled_text = "#89979c"
        selected_step = "#e7efff"
        status_bg = "#edf1f2"

    return f"""
* {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow, QWidget {{ background: {body}; color: {text}; }}
QLabel {{ background: transparent; }}
QStackedWidget, QStackedWidget > QWidget {{ background: transparent; }}
QWidget#appHeader {{
    background: #171717;
    color: #ffffff;
    border-bottom: 1px solid #2b2b2b;
}}
QLabel#appTitle {{
    background: transparent;
    color: #ffffff;
    font-size: 23px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}
QLabel#appCaption {{
    background: transparent;
    color: #9b9b9b;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
}}
QLabel#headerLogo {{ background: transparent; border: 0; }}
QMenuBar, QMenu, QStatusBar {{ background: #171717; color: #ececec; }}
QMenuBar {{ border-bottom: 1px solid #2b2b2b; }}
QMenuBar::item {{ background: transparent; padding: 5px 9px; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: #303030; }}
QStatusBar {{ border-top: 1px solid #2b2b2b; }}

QTabWidget#workspaceTabs::pane {{ border: 0; background: {body}; }}
QTabWidget#workspaceTabs QTabBar {{ background: #171717; }}
QTabWidget#workspaceTabs QTabBar::tab {{
    background: #171717;
    color: #afafaf;
    border: 0;
    border-right: 1px solid #2b2b2b;
    border-bottom: 2px solid #171717;
    padding: 13px 18px 12px 18px;
    min-width: 128px;
    font-weight: 600;
}}
QTabWidget#workspaceTabs QTabBar::tab:hover:!selected {{
    background: #252525;
    color: #ececec;
}}
QTabWidget#workspaceTabs QTabBar::tab:selected {{
    background: {tab_selected};
    color: {text};
    border-bottom: 2px solid {PRIMARY_ACCENT};
}}

QGroupBox {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px 12px 12px 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: {text};
}}
QFrame#stageCard {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
}}
QFrame#stageCard[state="running"] {{ border: 1px solid {RUNNING_ACCENT}; }}
QFrame#stageCard[state="complete"], QFrame#stageCard[state="ready"] {{
    border: 1px solid {PRIMARY_ACCENT};
}}
QFrame#stageCard[state="failed"] {{ border: 1px solid {WARNING_ACCENT}; }}
QFrame#workflowGroup, QFrame#cropCheckpoint, QFrame#tilesetCheckpoint {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 10px;
}}
QFrame#workflowGroup[selected="true"] {{
    background: {raised};
    border-left: 1px solid #505050;
    border-right: 1px solid #505050;
    border-bottom: 1px solid #505050;
}}
QFrame#workflowStep {{
    background: {step_surface};
    border: 1px solid {border};
    border-radius: 6px;
}}
QFrame#workflowStep[selected="true"] {{
    background: {selected_step};
    border: 1px solid {PRIMARY_ACCENT};
}}
QGroupBox#globalOptions {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
}}
QGroupBox#sourcePanel {{ border-top: 2px solid {PRIMARY_ACCENT}; }}
QGroupBox#preparationPanel {{ border-top: 2px solid {PRIMARY_ACCENT}; }}
QFrame#optionsDivider {{ color: {border}; }}
QLabel#globalOptionsTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#compactTarget {{
    color: #ffffff;
    background: #3d63b8;
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#workflowGroupSubtitle {{ color: {muted}; font-size: 11px; }}
QLabel#settingsExplanation {{
    color: {muted};
    font-size: 14px;
    line-height: 1.35;
    padding: 12px;
}}
QLabel#statusBadge {{
    color: {muted};
    background: {status_bg};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#statusBadge[state="complete"] {{ color: #9bb7ff; border-color: #4f70bd; }}
QLabel#statusBadge[state="running"] {{
    color: #ffffff;
    background: #245f89;
    border-color: {RUNNING_ACCENT};
}}
QLabel#statusBadge[state="queued"] {{ color: {muted}; border-color: #505050; }}
QLabel#statusBadge[state="failed"] {{ color: #ff8a8a; border-color: {WARNING_ACCENT}; }}
QPushButton#workflowSettingsButton {{
    background: transparent;
    color: {muted};
    border-color: {border};
}}
QPushButton#workflowSettingsButton:hover {{ color: {text}; border-color: {PRIMARY_ACCENT}; }}

QPushButton, QToolButton {{
    background: {button_bg};
    color: {button_text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 7px 11px;
    min-height: 18px;
}}
QPushButton:hover, QToolButton:hover {{ background: {button_hover}; border-color: #5a5a5a; }}
QPushButton:pressed, QToolButton:pressed {{ background: {button_pressed}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {disabled_text}; background: {surface}; }}
QPushButton#primaryButton {{
    background: {PRIMARY_ACCENT};
    border-color: {PRIMARY_ACCENT};
    color: #ffffff;
    font-weight: 700;
}}
QPushButton#primaryButton:hover {{ background: #739eff; border-color: #739eff; }}
QPushButton#primaryButton:pressed {{ background: #4776df; border-color: #4776df; }}
QPushButton#navbarButton {{
    background: transparent;
    border: 1px solid #424242;
    color: #ffffff;
    padding: 7px 11px;
}}
QPushButton#navbarButton:hover {{ background: #303030; border-color: #5a5a5a; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {input_bg};
    color: {input_text};
    selection-background-color: #436fd1;
    selection-color: #ffffff;
    border: 1px solid {border};
    border-radius: 6px;
    padding: 7px 9px;
    min-height: 18px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {PRIMARY_ACCENT};
}}
QComboBox QAbstractItemView {{
    background: {surface};
    color: {text};
    border: 1px solid {border};
    selection-background-color: #436fd1;
    selection-color: #ffffff;
    outline: 0;
}}
QCheckBox {{ spacing: 7px; background: transparent; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    background: {input_bg};
    border: 1px solid #5a5a5a;
    border-radius: 3px;
}}
QCheckBox::indicator:checked {{ background: {PRIMARY_ACCENT}; border-color: #739eff; }}
QCheckBox::indicator:disabled {{ background: {raised}; border-color: {border}; }}

QTextEdit, QPlainTextEdit {{
    background: {terminal};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 8px;
    font-family: Menlo, Monaco, Consolas, monospace;
}}
QPlainTextEdit#processingTerminal {{ font-size: 11px; }}
QScrollArea {{ border: 0; background: transparent; }}
QScrollArea#workspacePageScroll {{ background: {body}; }}
QScrollArea#viewerControlsScroll {{ background: {body}; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: {raised}; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {scroll_handle}; border-radius: 5px; min-height: 28px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QSlider::groove:horizontal {{ height: 5px; background: {border}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
    background: {PRIMARY_ACCENT};
    border: 1px solid #739eff;
}}
QProgressBar {{
    background: {raised};
    color: {text};
    border: 0;
    border-radius: 4px;
    text-align: center;
    min-height: 7px;
}}
QProgressBar::chunk {{ background: {PRIMARY_ACCENT}; border-radius: 4px; }}
QProgressBar[state="running"]::chunk {{ background: {RUNNING_ACCENT}; }}

QLabel#heading {{ font-size: 21px; font-weight: 700; color: {text}; }}
QLabel#subtitle {{ color: {muted}; margin-bottom: 4px; }}
QLabel#pageTitle {{ font-size: 25px; font-weight: 700; color: {text}; }}
QLabel#pageSubtitle, QLabel#datasetSummary, QLabel#terminalHint, QLabel#stageOutput {{
    color: {muted};
}}
QLabel#fieldLabel, QLabel#stageNumber {{
    color: {PRIMARY_ACCENT};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
}}
QLabel#flowArrow {{ color: {muted}; font-size: 24px; }}
QLabel#currentStage {{ color: {muted}; font-weight: 600; }}
QLabel#mediaPreview {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; }}
QToolTip {{
    background: #303030;
    color: #ececec;
    border: 1px solid #505050;
    padding: 5px;
}}
"""


def icon_color(dark: bool, selected: bool = False) -> str:
    if selected:
        return PRIMARY_ACCENT
    return "#afafaf" if dark else "#708087"


def viewport_background(dark: bool) -> tuple[str, str]:
    return ("#2f2f2f", "#171717") if dark else ("#f2f5f5", "#dce5e7")


def transparent_color() -> QColor:
    """Small convenience for callers creating transparent branded pixmaps."""
    return QColor(0, 0, 0, 0)

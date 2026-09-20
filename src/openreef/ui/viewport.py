"""3D viewport interaction tailored for mouse and trackpad use."""

from __future__ import annotations

import math
from typing import cast

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QInputDevice,
    QKeyEvent,
    QMouseEvent,
    QNativeGestureEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPolygon,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from openreef.core.camera import pan_camera
from openreef.ui.theme import WARNING_ACCENT

ORBIT_MOTION_FACTOR = 4.0
TRACKPAD_PAN_FACTOR = 0.35
PINCH_SENSITIVITY = 1.40
WHEEL_ZOOM_STEP = 1.08
TRACKPAD_ORBIT_DEGREES_PER_PIXEL = 0.08


def tinkercad_navigation_button(
    button: Qt.MouseButton,
    modifiers: Qt.KeyboardModifier,
) -> Qt.MouseButton | None:
    """Map a physical mouse press to VTK's orbit/pan buttons."""

    shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
    control = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
    if button == Qt.MouseButton.LeftButton:
        if not control:
            return None
        return Qt.MouseButton.MiddleButton if shift else Qt.MouseButton.LeftButton
    if button == Qt.MouseButton.RightButton:
        return Qt.MouseButton.MiddleButton if shift else Qt.MouseButton.LeftButton
    if button == Qt.MouseButton.MiddleButton:
        return Qt.MouseButton.MiddleButton
    return None


class LassoOverlay(QWidget):
    """Transparent drawing surface placed over the VTK viewport."""

    finished = Signal(object)
    cancelled = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._points: list[QPoint] = []
        self._drawing = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def begin(self) -> None:
        self._points.clear()
        self._drawing = False
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        self.setFocus()
        self.update()

    def cancel(self) -> None:
        self._points.clear()
        self._drawing = False
        self.hide()
        self.cancelled.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if event.button() == Qt.MouseButton.RightButton:
            self.cancel()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._points = [event.position().toPoint()]
        self._drawing = True
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if not self._drawing:
            return
        point = event.position().toPoint()
        previous = self._points[-1]
        if (point - previous).manhattanLength() >= 3:
            self._points.append(point)
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if event.button() != Qt.MouseButton.LeftButton or not self._drawing:
            return
        self._drawing = False
        points = [(float(point.x()), float(point.y())) for point in self._points]
        self.hide()
        if len(points) >= 3:
            self.finished.emit(points)
        else:
            self.cancelled.emit()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API name
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt API name
        del event
        if len(self._points) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(WARNING_ACCENT), 2.5))
        polygon = QPolygon(self._points)
        if len(self._points) >= 3:
            fill = QColor(WARNING_ACCENT)
            fill.setAlpha(42)
            painter.setBrush(fill)
            painter.drawPolygon(polygon)
        else:
            painter.drawPolyline(polygon)


class MeasurementToolbar(QFrame):
    """Compact floating controls shown only for a confirmed metric mesh."""

    tool_selected = Signal(str)
    clear_requested = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("measurementToolbar")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 9, 10, 9)
        outer.setSpacing(6)

        self.scale_status = QLabel("MarkerTags detected · scaled")
        self.scale_status.setObjectName("measurementScaleStatus")
        outer.addWidget(self.scale_status)

        row = QHBoxLayout()
        row.setSpacing(5)
        self.length_button = QPushButton("↔  Length")
        self.polygon_button = QPushButton("◇  Surface polygon")
        self.clear_button = QPushButton("Clear")
        for button in (self.length_button, self.polygon_button):
            button.setObjectName("measurementToolButton")
            button.setCheckable(True)
        self.clear_button.setObjectName("measurementClearButton")
        self.length_button.clicked.connect(lambda: self.tool_selected.emit("length"))
        self.polygon_button.clicked.connect(lambda: self.tool_selected.emit("polygon"))
        self.clear_button.clicked.connect(self.clear_requested)
        row.addWidget(self.length_button)
        row.addWidget(self.polygon_button)
        row.addWidget(self.clear_button)
        outer.addLayout(row)

        self.hint = QLabel()
        self.hint.setObjectName("measurementHint")
        self.hint.setWordWrap(True)
        self.hint.hide()
        outer.addWidget(self.hint)
        self.hide()

    def set_mode(self, mode: str | None) -> None:
        self.length_button.setChecked(mode == "length")
        self.polygon_button.setChecked(mode == "polygon")

    def set_hint(self, text: str) -> None:
        self.hint.setText(text)
        self.hint.setVisible(bool(text))
        self.adjustSize()


class ReefInteractor(QtInteractor):
    """Qt/VTK viewport with Tinkercad-style mouse and trackpad navigation."""

    lasso_finished = Signal(object)
    lasso_cancelled = Signal()
    measurement_tool_selected = Signal(str)
    measurement_clear_requested = Signal()
    measurement_point_clicked = Signal(float, float)
    measurement_close_requested = Signal()
    measurement_backspace_requested = Signal()
    measurement_cancel_requested = Signal()

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        style = self.iren.interactor.GetInteractorStyle()
        if hasattr(style, "SetMotionFactor"):
            style.SetMotionFactor(ORBIT_MOTION_FACTOR)
        self._navigation_press_active = False
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)
        self.lasso_overlay = LassoOverlay(self)
        self.lasso_overlay.finished.connect(self.lasso_finished)
        self.lasso_overlay.cancelled.connect(self.lasso_cancelled)
        self.measurement_toolbar = MeasurementToolbar(self)
        self.measurement_toolbar.tool_selected.connect(self.measurement_tool_selected)
        self.measurement_toolbar.clear_requested.connect(self.measurement_clear_requested)
        self._measurement_mode: str | None = None

    def begin_lasso(self) -> None:
        self.set_measurement_mode(None)
        self.lasso_overlay.begin()

    def cancel_lasso(self) -> None:
        if not self.lasso_overlay.isHidden():
            self.lasso_overlay.cancel()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        self.lasso_overlay.setGeometry(self.rect())
        self._position_measurement_toolbar()

    def set_measurement_available(self, available: bool, status: str = "") -> None:
        self.measurement_toolbar.scale_status.setText(status)
        self.measurement_toolbar.setVisible(available)
        if not available:
            self.set_measurement_mode(None)
        self._position_measurement_toolbar()
        if available:
            self.measurement_toolbar.raise_()

    def set_measurement_mode(self, mode: str | None) -> None:
        self._measurement_mode = mode
        self.measurement_toolbar.set_mode(mode)
        if mode is not None:
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setFocus()
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()

    def set_measurement_hint(self, text: str) -> None:
        self.measurement_toolbar.set_hint(text)
        self._position_measurement_toolbar()

    def _position_measurement_toolbar(self) -> None:
        toolbar = self.measurement_toolbar
        toolbar.adjustSize()
        toolbar.move(18, max(18, self.height() - toolbar.height() - 18))

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture:
            gesture = cast(QNativeGestureEvent, event)
            if gesture.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                self._zoom(math.exp(float(gesture.value()) * PINCH_SENSITIVITY))
                gesture.accept()
                return True
        return super().event(event)

    def _zoom(self, factor: float) -> None:
        self.camera.Zoom(max(0.05, min(factor, 20.0)))
        self.reset_camera_clipping_range()
        self.render()

    @staticmethod
    def _as_navigation_event(
        event: QMouseEvent,
        target: Qt.MouseButton,
    ) -> QMouseEvent:
        """Translate a physical press to the plain VTK button for its action."""

        buttons = event.buttons()
        physical = event.button()
        if buttons & physical:
            buttons &= ~physical
            buttons |= target
        return QMouseEvent(
            event.type(),
            event.position(),
            event.scenePosition(),
            event.globalPosition(),
            target,
            buttons,
            Qt.KeyboardModifier.NoModifier,
            event.pointingDevice(),
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if (
            self._measurement_mode is not None
            and event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        ):
            self.measurement_point_clicked.emit(
                float(event.position().x()), float(event.position().y())
            )
            event.accept()
            return
        target = tinkercad_navigation_button(event.button(), event.modifiers())
        if target is None:
            self._navigation_press_active = False
            event.accept()
            return
        self._navigation_press_active = True
        super().mousePressEvent(self._as_navigation_event(event, target))
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if self._measurement_mode == "polygon" and event.button() == Qt.MouseButton.LeftButton:
            self.measurement_close_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API name
        if self._measurement_mode is not None:
            if event.key() == Qt.Key.Key_Escape:
                self.measurement_cancel_requested.emit()
                event.accept()
                return
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.measurement_close_requested.emit()
                event.accept()
                return
            if event.key() == Qt.Key.Key_Backspace:
                self.measurement_backspace_requested.emit()
                event.accept()
                return
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API name
        if self._navigation_press_active:
            super().mouseReleaseEvent(event)
            self._navigation_press_active = False
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 - Qt API name
        pixel_delta = event.pixelDelta()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            amount = pixel_delta.y() if not pixel_delta.isNull() else event.angleDelta().y() / 4.0
            self._zoom(math.exp(float(amount) / 360.0))
            event.accept()
            return
        phased_scroll = event.phase() != Qt.ScrollPhase.NoScrollPhase
        touchpad = event.device().type() == QInputDevice.DeviceType.TouchPad
        if pixel_delta.isNull() and not phased_scroll and not touchpad:
            steps = float(event.angleDelta().y()) / 120.0
            if steps:
                self._zoom(WHEEL_ZOOM_STEP**steps)
            event.accept()
            return

        if pixel_delta.isNull():
            # Qt occasionally omits pixelDelta for macOS trackpad scrolls. One
            # wheel angle step is 120 units; dividing by eight gives a similar
            # pan distance to the native pixel stream without a sudden jump.
            angle_delta = event.angleDelta()
            dx = float(angle_delta.x()) / 8.0
            dy = float(angle_delta.y()) / 8.0
        else:
            dx = float(pixel_delta.x())
            dy = float(pixel_delta.y())

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.camera.Azimuth(-dx * TRACKPAD_ORBIT_DEGREES_PER_PIXEL)
            self.camera.Elevation(dy * TRACKPAD_ORBIT_DEGREES_PER_PIXEL)
            self.camera.OrthogonalizeViewUp()
            self.reset_camera_clipping_range()
            self.render()
            event.accept()
            return

        pan_camera(
            self.camera,
            dx=dx * TRACKPAD_PAN_FACTOR,
            dy=dy * TRACKPAD_PAN_FACTOR,
            viewport_height=self.height(),
        )
        self.reset_camera_clipping_range()
        self.render()
        event.accept()

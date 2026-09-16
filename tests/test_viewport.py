import pytest
from PySide6.QtCore import Qt

from openreef.ui.viewport import tinkercad_navigation_button


@pytest.mark.parametrize(
    ("button", "modifiers", "expected"),
    [
        (Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, None),
        (
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.MouseButton.LeftButton,
        ),
        (
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.MouseButton.MiddleButton,
        ),
        (
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.ShiftModifier,
            Qt.MouseButton.MiddleButton,
        ),
        (
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.MouseButton.LeftButton,
        ),
        (
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier,
            Qt.MouseButton.MiddleButton,
        ),
    ],
)
def test_tinkercad_navigation_button(
    button: Qt.MouseButton,
    modifiers: Qt.KeyboardModifier,
    expected: Qt.MouseButton | None,
) -> None:
    assert tinkercad_navigation_button(button, modifiers) == expected

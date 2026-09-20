from openreef.ui.theme import (
    PRIMARY_ACCENT,
    RUNNING_ACCENT,
    WARNING_ACCENT,
    WORKFLOW_LEVEL_COLORS,
    application_stylesheet,
    icon_color,
)


def test_dark_theme_uses_neutral_macos_surfaces() -> None:
    stylesheet = application_stylesheet(True)

    assert "#111315" in stylesheet
    assert "#1c1f22" in stylesheet
    assert PRIMARY_ACCENT in stylesheet
    assert RUNNING_ACCENT in stylesheet
    assert WARNING_ACCENT in stylesheet
    assert "QFrame#tilesetCheckpoint" in stylesheet
    assert "#5b8cff" not in stylesheet.lower()
    assert "#38a9ff" not in stylesheet.lower()
    assert "QFrame#appSidebar" in stylesheet
    assert all(color in stylesheet for color in WORKFLOW_LEVEL_COLORS)
    assert 'QFrame#workflowGroup[level="1"]' in stylesheet
    assert 'QFrame#tilesetCheckpoint[level="6"]' in stylesheet
    assert icon_color(True, selected=True) == PRIMARY_ACCENT


def test_light_theme_remains_available() -> None:
    stylesheet = application_stylesheet(False)

    assert "#f2f2f7" in stylesheet
    assert PRIMARY_ACCENT in stylesheet

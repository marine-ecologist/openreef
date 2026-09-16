from openreef.ui.theme import (
    PRIMARY_ACCENT,
    RUNNING_ACCENT,
    WARNING_ACCENT,
    application_stylesheet,
    icon_color,
)


def test_dark_theme_uses_carbon_surfaces_and_blue_semantic_palette() -> None:
    stylesheet = application_stylesheet(True)

    assert "#212121" in stylesheet
    assert "#171717" in stylesheet
    assert PRIMARY_ACCENT in stylesheet
    assert RUNNING_ACCENT in stylesheet
    assert WARNING_ACCENT in stylesheet
    assert "QFrame#tilesetCheckpoint" in stylesheet
    assert "#67a99b" not in stylesheet.lower()
    assert icon_color(True, selected=True) == PRIMARY_ACCENT


def test_light_theme_remains_available() -> None:
    stylesheet = application_stylesheet(False)

    assert "#f2f5f5" in stylesheet
    assert PRIMARY_ACCENT in stylesheet

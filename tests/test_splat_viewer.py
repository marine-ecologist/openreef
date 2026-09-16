from pathlib import Path
from urllib.request import urlopen

from openreef.ui.splat_viewer_page import SplatAssetServer

ASSET_JAVASCRIPT = (
    Path(__file__).parents[1] / "src" / "openreef" / "assets" / "supersplat" / "index.js"
)


def test_splat_asset_server_serves_selected_model(tmp_path: Path) -> None:
    source = tmp_path / "reef.ply"
    source.write_bytes(b"ply\nend_header\n")
    server = SplatAssetServer()
    try:
        url = server.load_model(source)
        assert "noanim" in url
        root = url.split("/index.html", 1)[0]
        with urlopen(f"{root}/model.ply", timeout=2) as response:  # noqa: S310
            assert response.read() == source.read_bytes()
        with urlopen(f"{root}/settings.json", timeout=2) as response:  # noqa: S310
            assert response.headers["Content-Type"].startswith("application/json")
    finally:
        server.close()


def test_splat_viewer_uses_tinkercad_navigation_map() -> None:
    javascript = ASSET_JAVASCRIPT.read_text()

    assert "cameraButton = event.shiftKey ? 2 : 0" in javascript
    assert "event.button === 1" in javascript
    assert "cameraButton = 2" in javascript
    assert "event.button === 2" in javascript
    assert "const trackpadPan" in javascript
    assert "const isShiftOrbit = event.shiftKey" in javascript
    assert "trackpadZoomSensitivity = 1.75" in javascript

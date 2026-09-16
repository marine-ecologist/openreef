from pathlib import Path

import pytest

from openreef.web_export import (
    discover_web_models,
    export_tiled_web_viewer,
    export_web_viewer,
    read_tiled_model_manifest,
    write_tiled_model_manifest,
)


def test_discover_web_models_prefers_textured_outputs_and_deduplicates_links(
    tmp_path: Path,
) -> None:
    models = tmp_path / "models"
    openmvs = tmp_path / "openmvs"
    models.mkdir()
    openmvs.mkdir()
    original = openmvs / "scene_mesh_textured.glb"
    original.write_bytes(b"glb")
    (models / "reef_textured_mesh.glb").symlink_to(original)
    (models / "reef_textured_mesh_medium.glb").write_bytes(b"medium")
    (models / "reef_mesh.ply").write_bytes(b"ply")
    (models / "notes.txt").write_text("not a model")

    discovered = discover_web_models(tmp_path)

    assert [path.name for path in discovered] == [
        "reef_textured_mesh.glb",
        "reef_textured_mesh_medium.glb",
        "reef_mesh.ply",
    ]


def test_export_web_viewer_creates_runnable_folder(tmp_path: Path) -> None:
    source = tmp_path / "models" / "reef.ply"
    source.parent.mkdir()
    source.write_bytes(b"portable ply")
    output = tmp_path / "openreef-web"

    result = export_web_viewer(source, output, title="Reef survey")

    assert result.model.read_bytes() == b"portable ply"
    assert "Reef survey" in result.index.read_text()
    assert "PLYLoader" in (output / "viewer.js").read_text()
    assert '<option value="points">Points</option>' in result.index.read_text()
    assert 'value="1"' in result.index.read_text()
    assert "model.ply" in (output / "openreef-web.json").read_text()
    assert '"compact": false' in (output / "openreef-web.json").read_text()
    assert (output / "serve.py").is_file()
    assert (output / ".nojekyll").is_file()
    pages_guide = (output / "GITHUB-PAGES.md").read_text()
    assert "Deploy from a branch" in pages_guide
    assert "below GitHub's 100 MiB" in pages_guide
    viewer_javascript = (output / "viewer.js").read_text()
    assert "distance *= 1.005" in viewer_javascript
    assert "controls.mouseButtons.LEFT = null" in viewer_javascript
    assert "controls.mouseButtons.MIDDLE = THREE.MOUSE.PAN" in viewer_javascript
    assert "controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE" in viewer_javascript
    assert "event.shiftKey ? 1 : 2" in viewer_javascript
    assert "panFromTrackpad" in viewer_javascript
    assert "orbitFromTrackpad" in viewer_javascript
    assert "event.key.toLowerCase() !== 'f'" in viewer_javascript
    assert result.launcher.stat().st_mode & 0o111


def test_export_rejects_source_folder_as_output(tmp_path: Path) -> None:
    source = tmp_path / "reef.ply"
    source.write_bytes(b"ply")

    with pytest.raises(ValueError, match="output folder"):
        export_web_viewer(source, tmp_path)


def test_export_tiled_web_viewer_copies_hierarchy_and_streaming_viewer(
    tmp_path: Path,
) -> None:
    source = tmp_path / "converted-tiles"
    content = source / "level-0"
    content.mkdir(parents=True)
    tileset = source / "tileset.json"
    tileset.write_text(
        '{"asset":{"version":"1.1"},"geometricError":100,'
        '"root":{"boundingVolume":{"sphere":[0,0,0,10]},"geometricError":0}}'
    )
    (content / "reef.glb").write_bytes(b"tile payload")

    output = tmp_path / "openreef-web-tiles"
    stale = output / "tiles" / "textures" / "obsolete.png"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old shared atlas")
    result = export_tiled_web_viewer(tileset, output, title="Large reef")

    assert result.model == output / "tiles" / "tileset.json"
    assert (output / "tiles" / "level-0" / "reef.glb").read_bytes() == b"tile payload"
    assert "Large reef" in result.index.read_text()
    viewer = (output / "viewer.js").read_text()
    assert "new TilesRenderer(config.tileset)" in viewer
    assert "tiles.loadProgress" in viewer
    assert "tiles.update()" in viewer
    assert '"format": "3dtiles"' in (output / "openreef-web.json").read_text()
    assert "coarse tiles" in (output / "GITHUB-PAGES.md").read_text()
    assert not stale.exists()


def test_export_tiled_web_viewer_rejects_non_tileset_json(tmp_path: Path) -> None:
    source = tmp_path / "tileset.json"
    source.write_text('{"not": "3D Tiles"}')

    with pytest.raises(ValueError, match="asset metadata"):
        export_tiled_web_viewer(source, tmp_path / "output")


def test_tiled_model_manifest_is_portable_from_models_folder(tmp_path: Path) -> None:
    source = tmp_path / "converted-tiles"
    source.mkdir()
    tileset = source / "tileset.json"
    tileset.write_text(
        '{"asset":{"version":"1.1"},'
        '"root":{"boundingVolume":{"sphere":[0,0,0,1]},"geometricError":0}}'
    )
    result = export_tiled_web_viewer(
        tileset,
        tmp_path / "reef" / "openreef-web-tiles",
        title="Patch reef",
    )
    entry = write_tiled_model_manifest(
        result,
        tmp_path / "reef" / "models" / "reef_3d_tiles.json",
        title="Patch reef",
    )

    manifest = read_tiled_model_manifest(entry)

    assert manifest.title == "Patch reef"
    assert manifest.viewer == result.index
    assert manifest.tileset == result.model
    assert '"viewer": "../openreef-web-tiles/index.html"' in entry.read_text()


def test_export_tiled_web_viewer_rejects_output_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "converted-tiles" / "tileset.json"
    source.parent.mkdir()
    source.write_text(
        '{"asset":{"version":"1.1"},'
        '"root":{"boundingVolume":{"sphere":[0,0,0,1]},"geometricError":0}}'
    )

    with pytest.raises(ValueError, match="outside the source tileset"):
        export_tiled_web_viewer(source, source.parent / "viewer")

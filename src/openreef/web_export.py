"""Create a portable browser-viewer folder for an OpenReef model."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from openreef.core.glb_edit import (
    WEB_COMPACT_TARGET,
    make_compact_glb,
    make_glb_self_contained,
)

SUPPORTED_WEB_FORMATS = frozenset({".glb", ".ply"})
THREE_VERSION = "0.186.0"
TILES_RENDERER_VERSION = "0.6.2"
GITHUB_REGULAR_FILE_LIMIT = 100 * 1024 * 1024


@dataclass(frozen=True)
class WebExportResult:
    folder: Path
    model: Path
    index: Path
    launcher: Path


@dataclass(frozen=True)
class TiledModelManifest:
    title: str
    viewer: Path
    tileset: Path


def discover_web_models(dataset: str | Path) -> tuple[Path, ...]:
    """Find browser-compatible models, preferring friendly files in models/."""
    root = Path(dataset).expanduser().resolve()
    discovered: list[Path] = []
    seen: set[Path] = set()
    for folder in (root / "models", root / "openmvs"):
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_WEB_FORMATS:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            discovered.append(path)
    return tuple(sorted(discovered, key=_model_sort_key))


def _model_sort_key(path: Path) -> tuple[int, str]:
    name = path.name.lower()
    if "textured_mesh" in name and "medium" not in name and "low" not in name:
        rank = 0
    elif "textured" in name and "medium" in name:
        rank = 1
    elif "textured" in name and "low" in name:
        rank = 2
    elif path.suffix.lower() == ".glb":
        rank = 3
    elif "mesh" in name:
        rank = 4
    elif "densecloud" in name or "dense" in name:
        rank = 5
    else:
        rank = 6
    return rank, name


def export_web_viewer(
    model: str | Path,
    output_folder: str | Path,
    *,
    title: str | None = None,
    compact: bool = False,
    max_model_bytes: int = WEB_COMPACT_TARGET,
) -> WebExportResult:
    """Copy one model and write the HTML viewer and local-server launcher."""
    source = Path(model).expanduser().resolve()
    output = Path(output_folder).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Model does not exist: {source}")
    if source.suffix.lower() not in SUPPORTED_WEB_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_WEB_FORMATS))
        raise ValueError(f"Web Export supports: {supported}")
    if output == source.parent or source.is_relative_to(output):
        raise ValueError("Choose an output folder that does not contain the source model.")

    output.mkdir(parents=True, exist_ok=True)
    model_name = f"model{source.suffix.lower()}"
    destination = output / model_name
    if source.suffix.lower() == ".glb":
        if compact:
            print("OPENREEF_PHASE\tCompacting GLB for GitHub Pages", flush=True)
            make_compact_glb(source, destination, max_bytes=max_model_bytes)
        else:
            print("OPENREEF_PHASE\tEmbedding GLB textures", flush=True)
            make_glb_self_contained(source, destination)
    else:
        if compact and source.stat().st_size > max_model_bytes:
            raise ValueError(
                "Compact export currently requires a GLB for automatic compression. "
                "Reduce this PLY with the Viewer complexity slider, save it, and retry."
            )
        _copy_with_progress(source, destination)

    display_title = title.strip() if title and title.strip() else source.stem.replace("_", " ")
    settings = {
        "model": model_name,
        "format": source.suffix.lower().removeprefix("."),
        "title": display_title,
        "source": source.name,
        "threeVersion": THREE_VERSION,
        "compact": compact,
    }
    (output / "index.html").write_text(_index_html(display_title), encoding="utf-8")
    (output / "styles.css").write_text(STYLES, encoding="utf-8")
    (output / "viewer.js").write_text(_viewer_javascript(settings), encoding="utf-8")
    (output / "serve.py").write_text(SERVER_PYTHON, encoding="utf-8")
    launcher = output / "Open OpenReef Web.command"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(0o755)
    (output / "Open OpenReef Web.bat").write_text(WINDOWS_LAUNCHER, encoding="utf-8")
    (output / "README.txt").write_text(_readme(display_title, model_name), encoding="utf-8")
    (output / ".nojekyll").touch()
    (output / "GITHUB-PAGES.md").write_text(
        _github_pages_guide(display_title, model_name, destination.stat().st_size),
        encoding="utf-8",
    )
    (output / "openreef-web.json").write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("OPENREEF_PHASE\tWeb viewer ready", flush=True)
    return WebExportResult(output, destination, output / "index.html", launcher)


def export_tiled_web_viewer(
    tileset_json: str | Path,
    output_folder: str | Path,
    *,
    title: str | None = None,
) -> WebExportResult:
    """Package an existing spatial 3D Tiles hierarchy as an OpenReef Web site."""
    source = Path(tileset_json).expanduser().resolve()
    output = Path(output_folder).expanduser().resolve()
    settings = _validate_tileset(source)
    source_folder = source.parent
    if output == source_folder or output.is_relative_to(source_folder):
        raise ValueError("Choose an output folder outside the source tileset folder.")

    output.mkdir(parents=True, exist_ok=True)
    tiles_folder = output / "tiles"
    _copy_tree_with_progress(source_folder, tiles_folder)
    copied_tileset = tiles_folder / source.relative_to(source_folder)
    display_title = title.strip() if title and title.strip() else source_folder.name
    web_settings = {
        "tileset": copied_tileset.relative_to(output).as_posix(),
        "format": "3dtiles",
        "title": display_title,
        "source": source.name,
        "tilesVersion": str(settings.get("asset", {}).get("version", "unknown")),
        "threeVersion": THREE_VERSION,
        "tilesRendererVersion": TILES_RENDERER_VERSION,
    }
    (output / "index.html").write_text(_tiled_index_html(display_title), encoding="utf-8")
    (output / "styles.css").write_text(STYLES, encoding="utf-8")
    (output / "viewer.js").write_text(
        _tiled_viewer_javascript(web_settings), encoding="utf-8"
    )
    (output / "serve.py").write_text(SERVER_PYTHON, encoding="utf-8")
    launcher = output / "Open OpenReef Web.command"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(0o755)
    (output / "Open OpenReef Web.bat").write_text(WINDOWS_LAUNCHER, encoding="utf-8")
    (output / "README.txt").write_text(_tiled_readme(display_title), encoding="utf-8")
    (output / ".nojekyll").touch()
    (output / "GITHUB-PAGES.md").write_text(
        _tiled_github_pages_guide(display_title, tiles_folder), encoding="utf-8"
    )
    (output / "openreef-web.json").write_text(
        json.dumps(web_settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("OPENREEF_PHASE\t3D Tiles viewer ready", flush=True)
    return WebExportResult(output, copied_tileset, output / "index.html", launcher)


def write_tiled_model_manifest(
    result: WebExportResult,
    destination: str | Path,
    *,
    title: str,
) -> Path:
    """Add a portable 3D Tiles viewer entry to a dataset's models folder."""
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "openreef-3d-tiles",
        "title": title,
        "viewer": os.path.relpath(result.index, path.parent),
        "tileset": os.path.relpath(result.model, path.parent),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_tiled_model_manifest(path: str | Path) -> TiledModelManifest:
    """Resolve and validate a models-folder entry for the embedded tiled viewer."""
    source = Path(path).expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid OpenReef 3D Tiles model entry: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("format") != "openreef-3d-tiles":
        raise ValueError("This JSON is not an OpenReef 3D Tiles model entry.")
    title = str(payload.get("title") or source.stem)
    viewer_value = payload.get("viewer")
    tileset_value = payload.get("tileset")
    if not isinstance(viewer_value, str) or not isinstance(tileset_value, str):
        raise ValueError("The 3D Tiles model entry is missing its viewer or tileset path.")
    viewer = (source.parent / viewer_value).resolve()
    tileset = (source.parent / tileset_value).resolve()
    if not viewer.is_file():
        raise ValueError(f"The packaged 3D Tiles viewer is missing: {viewer}")
    if not tileset.is_file():
        raise ValueError(f"The packaged tileset.json is missing: {tileset}")
    return TiledModelManifest(title, viewer, tileset)


def _validate_tileset(source: Path) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(f"3D Tiles tileset does not exist: {source}")
    if source.name.lower() != "tileset.json":
        raise ValueError("Choose the tileset.json produced by a spatial 3D tiler.")
    try:
        parsed = json.loads(source.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid 3D Tiles JSON: {exc}") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("asset"), dict):
        raise ValueError("This JSON is missing the 3D Tiles asset metadata.")
    if not isinstance(parsed.get("root"), dict):
        raise ValueError("This JSON is missing the 3D Tiles root hierarchy.")
    return parsed


def _copy_tree_with_progress(source: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.openreef-tmp")
    previous = destination.with_name(f".{destination.name}.openreef-previous")
    for disposable in (temporary, previous):
        if disposable.is_dir():
            shutil.rmtree(disposable)
        elif disposable.exists():
            disposable.unlink()

    files = tuple(path for path in source.rglob("*") if path.is_file())
    total = sum(path.stat().st_size for path in files)
    copied = 0
    try:
        for path in files:
            relative = path.relative_to(source)
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with path.open("rb") as input_stream, target.open("wb") as output_stream:
                while block := input_stream.read(8 * 1024 * 1024):
                    output_stream.write(block)
                    copied += len(block)
                    print(
                        f"OPENREEF_PROGRESS\t{copied}\t{total}\tCopying 3D Tiles",
                        flush=True,
                    )
            shutil.copystat(path, target)
        if destination.exists():
            destination.replace(previous)
        temporary.replace(destination)
    except Exception:
        if not destination.exists() and previous.exists():
            previous.replace(destination)
        if temporary.is_dir():
            shutil.rmtree(temporary)
        raise
    if previous.is_dir():
        shutil.rmtree(previous)


def _copy_with_progress(source: Path, destination: Path) -> None:
    total = source.stat().st_size
    copied = 0
    temporary = destination.with_name(f".{destination.name}.openreef-tmp")
    try:
        with source.open("rb") as input_stream, temporary.open("wb") as output_stream:
            while block := input_stream.read(8 * 1024 * 1024):
                output_stream.write(block)
                copied += len(block)
                print(
                    f"OPENREEF_PROGRESS\t{copied}\t{total}\tCopying {source.name}",
                    flush=True,
                )
        shutil.copystat(source, temporary)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _index_html(title: str) -> str:
    safe_title = (
        title.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} — OpenReef Web</title>
  <link rel="stylesheet" href="styles.css">
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.min.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/"
      }}
    }}
  </script>
</head>
<body>
  <header>
    <div>
      <div class="brand">OPENREEF WEB</div>
      <h1 id="model-title">{safe_title}</h1>
    </div>
    <div id="status">Loading model…</div>
  </header>
  <main id="viewport"></main>
  <aside id="controls">
    <button id="fit" type="button">Fit to view</button>
    <label>Display
      <select id="display-mode">
        <option value="solid">Textured / solid</option>
        <option value="wireframe">Wire mesh</option>
        <option value="solid-wire">Solid + wireframe</option>
        <option value="points">Points</option>
      </select>
    </label>
    <label id="point-size-row">Point size
      <input id="point-size" type="range" min="1" max="12" value="1">
    <button id="screenshot" type="button">Screenshot</button>
    <button id="fullscreen" type="button">Full screen</button>
  </aside>
  <div id="progress"><div id="progress-bar"></div></div>
  <footer>
    Right-drag orbit · middle-drag or two fingers pan · Shift + right-drag pan ·
    Shift + two fingers orbit · wheel or pinch zoom · F fit
  </footer>
  <script type="module" src="viewer.js"></script>
</body>
</html>
"""


def _tiled_index_html(title: str) -> str:
    safe_title = (
        title.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} — OpenReef 3D Tiles</title>
  <link rel="stylesheet" href="styles.css">
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.min.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/",
        "three/examples/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/",
        "3d-tiles-renderer": "https://cdn.jsdelivr.net/npm/3d-tiles-renderer@{TILES_RENDERER_VERSION}/build/index.js",
        "3d-tiles-renderer/three/plugins": "https://cdn.jsdelivr.net/npm/3d-tiles-renderer@{TILES_RENDERER_VERSION}/build/index.three-plugins.js"
      }}
    }}
  </script>
</head>
<body>
  <header>
    <div>
      <div class="brand">OPENREEF · STREAMING 3D TILES</div>
      <h1 id="model-title">{safe_title}</h1>
    </div>
    <div id="status">Loading tileset…</div>
  </header>
  <main id="viewport"></main>
  <aside id="controls">
    <button id="fit" type="button">Fit to view</button>
    <label>Streaming detail
      <select id="detail">
        <option value="16">Fast preview</option>
        <option value="8" selected>Balanced</option>
        <option value="3">Fine</option>
      </select>
    </label>
    <button id="screenshot" type="button">Screenshot</button>
    <button id="fullscreen" type="button">Full screen</button>
  </aside>
  <div id="progress"><div id="progress-bar"></div></div>
  <footer>
    Right-drag orbit · middle-drag or two fingers pan · Shift + right-drag pan ·
    Shift + two fingers orbit · wheel or pinch zoom · F fit
  </footer>
  <script type="module" src="viewer.js"></script>
</body>
</html>
"""


def _viewer_javascript(settings: dict[str, object]) -> str:
    configuration = json.dumps(settings, ensure_ascii=False)
    return f"""import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
import {{ PLYLoader }} from 'three/addons/loaders/PLYLoader.js';

const config = {configuration};
const viewport = document.querySelector('#viewport');
const status = document.querySelector('#status');
const progress = document.querySelector('#progress');
const progressBar = document.querySelector('#progress-bar');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x071015);

const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 1000000);
const renderer = new THREE.WebGLRenderer({{ antialias: true, preserveDrawingBuffer: true }});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.mouseButtons.LEFT = null;
controls.mouseButtons.MIDDLE = THREE.MOUSE.PAN;
controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE;

// Keep the same Tinkercad-style navigation in the browser export as the
// desktop mesh, cloud, and Gaussian viewers. Plain left-click remains free for
// selecting a model; the modifier variants are translated into OrbitControls'
// established middle/right-button actions.
const remappedPointerEvents = new WeakSet();
renderer.domElement.addEventListener('pointerdown', (event) => {{
  if (remappedPointerEvents.has(event)) return;
  if (event.button !== 0) return;
  if (!event.ctrlKey) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const mappedButton = event.shiftKey ? 1 : 2;
  const mappedEvent = new PointerEvent('pointerdown', {{
    bubbles: true,
    cancelable: true,
    composed: true,
    pointerId: event.pointerId,
    pointerType: event.pointerType,
    isPrimary: event.isPrimary,
    clientX: event.clientX,
    clientY: event.clientY,
    screenX: event.screenX,
    screenY: event.screenY,
    button: mappedButton,
    buttons: mappedButton === 1 ? 4 : 2
  }});
  remappedPointerEvents.add(mappedEvent);
  renderer.domElement.dispatchEvent(mappedEvent);
}}, true);
renderer.domElement.addEventListener('contextmenu', (event) => event.preventDefault());

function panFromTrackpad(deltaX, deltaY) {{
  camera.updateMatrix();
  const offset = camera.position.clone().sub(controls.target);
  const visibleHeight = 2 * offset.length()
    * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
  const worldUnitsPerPixel = visibleHeight
    / Math.max(renderer.domElement.clientHeight, 1);
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1);
  const movement = right.multiplyScalar(-deltaX * worldUnitsPerPixel * 0.45)
    .add(up.multiplyScalar(deltaY * worldUnitsPerPixel * 0.45));
  camera.position.add(movement);
  controls.target.add(movement);
  controls.update();
}}

function orbitFromTrackpad(deltaX, deltaY) {{
  const offset = camera.position.clone().sub(controls.target);
  const spherical = new THREE.Spherical().setFromVector3(offset);
  spherical.theta -= deltaX * 0.003;
  spherical.phi -= deltaY * 0.003;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi, 0.01, Math.PI - 0.01);
  offset.setFromSpherical(spherical);
  camera.position.copy(controls.target).add(offset);
  camera.lookAt(controls.target);
  controls.update();
}}

renderer.domElement.addEventListener('wheel', (event) => {{
  // Browsers report trackpad pinches as Ctrl+wheel; leave those, along with
  // stepped mouse-wheel events, to OrbitControls for zooming.
  if (event.ctrlKey) return;
  const isTrackpadMovement = event.deltaMode === WheelEvent.DOM_DELTA_PIXEL
    && (Math.abs(event.deltaX) > 0 || Math.abs(event.deltaY) < 50);
  if (!isTrackpadMovement) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  if (event.shiftKey) orbitFromTrackpad(event.deltaX, event.deltaY);
  else panFromTrackpad(event.deltaX, event.deltaY);
}}, {{ capture: true, passive: false }});
scene.add(new THREE.HemisphereLight(0xc9eff5, 0x16262d, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 2.5);
sun.position.set(4, -3, 8);
scene.add(sun);

let modelRoot = null;
let pointObjects = [];
let meshObjects = [];
let generatedPointObjects = [];
let edgeObjects = [];

function resize() {{
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / Math.max(height, 1);
  camera.updateProjectionMatrix();
}}

function fitToView() {{
  if (!modelRoot) return;
  const box = new THREE.Box3().setFromObject(modelRoot);
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3());
  const direction = new THREE.Vector3(0.8, -1.2, 0.65).normalize();
  const forward = direction.clone().multiplyScalar(-1);
  const upReference = Math.abs(direction.z) > 0.95
    ? new THREE.Vector3(0, 1, 0)
    : new THREE.Vector3(0, 0, 1);
  const right = new THREE.Vector3().crossVectors(forward, upReference).normalize();
  const up = new THREE.Vector3().crossVectors(right, forward).normalize();
  const verticalTangent = Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
  const horizontalTangent = verticalTangent * camera.aspect;
  const corners = [];
  for (const x of [box.min.x, box.max.x]) {{
    for (const y of [box.min.y, box.max.y]) {{
      for (const z of [box.min.z, box.max.z]) {{
        corners.push(new THREE.Vector3(x, y, z));
      }}
    }}
  }}
  let distance = 0.001;
  let depthExtent = 0.001;
  corners.forEach((corner) => {{
    const relative = corner.sub(center);
    const depth = relative.dot(direction);
    depthExtent = Math.max(depthExtent, Math.abs(depth));
    distance = Math.max(
      distance,
      depth + Math.abs(relative.dot(right)) / horizontalTangent,
      depth + Math.abs(relative.dot(up)) / verticalTangent
    );
  }});
  distance *= 1.005;
  camera.position.copy(center).add(direction.multiplyScalar(distance));
  camera.up.copy(up);
  camera.near = Math.max((distance - depthExtent) / 100, 0.0001);
  camera.far = Math.max((distance + depthExtent) * 100, 1000);
  camera.updateProjectionMatrix();
  controls.target.copy(center);
  controls.update();
}}

function collectObjects() {{
  pointObjects = [];
  meshObjects = [];
  generatedPointObjects = [];
  modelRoot.traverse((object) => {{
    if (object.isPoints) pointObjects.push(object);
    if (object.isMesh) meshObjects.push(object);
  }});
  meshObjects.forEach((mesh) => {{
    const points = new THREE.Points(mesh.geometry, new THREE.PointsMaterial({{
      color: 0x78dbe4,
      size: 1,
      sizeAttenuation: false
    }}));
    points.position.copy(mesh.position);
    points.quaternion.copy(mesh.quaternion);
    points.scale.copy(mesh.scale);
    points.userData.openreefGeneratedPoints = true;
    mesh.parent.add(points);
    generatedPointObjects.push(points);
  }});
  pointObjects.push(...generatedPointObjects);
  pointObjects.forEach((object) => {{
    object.material.size = 1;
    object.material.sizeAttenuation = false;
  }});
}}

function setDisplayMode(mode) {{
  edgeObjects.forEach((edge) => {{
    edge.parent?.remove(edge);
    edge.geometry.dispose();
    edge.material.dispose();
  }});
  edgeObjects = [];
  meshObjects.forEach((object) => {{
    object.visible = mode !== 'points';
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach((material) => {{ material.wireframe = mode === 'wireframe'; }});
    if (mode === 'solid-wire') {{
      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(object.geometry, 22),
        new THREE.LineBasicMaterial({{ color: 0x10252d, transparent: true, opacity: 0.62 }})
      );
      object.add(edges);
      edgeObjects.push(edges);
    }}
  }});
  pointObjects.forEach((object) => {{ object.visible = mode === 'points'; }});
  document.querySelector('#point-size-row').hidden = mode !== 'points';
}}

function modelReady(root) {{
  modelRoot = root;
  scene.add(root);
  collectObjects();
  if (meshObjects.length === 0) {{
    document.querySelector('#display-mode').value = 'points';
  }}
  fitToView();
  setDisplayMode(document.querySelector('#display-mode').value);
  progress.hidden = true;
  status.textContent = `${{config.source}} · ${{formatCount(countVertices(root))}} vertices`;
}}

function countVertices(root) {{
  let count = 0;
  root.traverse((object) => {{
    if (!object.userData.openreefGeneratedPoints) {{
      count += object.geometry?.attributes?.position?.count || 0;
    }}
  }});
  return count;
}}

function formatCount(value) {{ return new Intl.NumberFormat().format(value); }}

function onProgress(event) {{
  if (!event.total) return;
  progressBar.style.width = `${{Math.round(event.loaded / event.total * 100)}}%`;
}}

function onError(error) {{
  console.error(error);
  progress.hidden = true;
  status.textContent = 'Could not load model — see README.txt';
}}

if (config.format === 'glb') {{
  new GLTFLoader().load(config.model, (result) => modelReady(result.scene), onProgress, onError);
}} else {{
  new PLYLoader().load(config.model, (geometry) => {{
    geometry.computeBoundingSphere();
    const hasFaces = geometry.index !== null;
    const hasColors = geometry.hasAttribute('color');
    if (hasFaces) {{
      if (!geometry.hasAttribute('normal')) geometry.computeVertexNormals();
      modelReady(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({{
        color: hasColors ? 0xffffff : 0x61b8c8,
        vertexColors: hasColors,
        roughness: 0.85,
        metalness: 0,
        side: THREE.DoubleSide
      }})));
    }} else {{
      modelReady(new THREE.Points(geometry, new THREE.PointsMaterial({{
        color: hasColors ? 0xffffff : 0x62c8cf,
        vertexColors: hasColors,
        size: 0.01,
        sizeAttenuation: true
      }})));
    }}
  }}, onProgress, onError);
}}

document.querySelector('#fit').addEventListener('click', fitToView);
window.addEventListener('keydown', (event) => {{
  if (event.key.toLowerCase() !== 'f' || event.ctrlKey || event.metaKey || event.altKey) return;
  event.preventDefault();
  fitToView();
}});
document.querySelector('#display-mode').addEventListener('change', (event) => {{
  setDisplayMode(event.target.value);
}});
document.querySelector('#point-size').addEventListener('input', (event) => {{
  pointObjects.forEach((object) => {{
    object.material.size = Number(event.target.value);
  }});
}});
document.querySelector('#fullscreen').addEventListener('click', () => {{
  document.documentElement.requestFullscreen();
}});
document.querySelector('#screenshot').addEventListener('click', () => {{
  renderer.render(scene, camera);
  const link = document.createElement('a');
  link.download = 'openreef-web.png';
  link.href = renderer.domElement.toDataURL('image/png');
  link.click();
}});
window.addEventListener('resize', resize);
resize();

renderer.setAnimationLoop(() => {{
  controls.update();
  renderer.render(scene, camera);
}});
"""


def _tiled_viewer_javascript(settings: dict[str, object]) -> str:
    configuration = json.dumps(settings, ensure_ascii=False)
    return f"""import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ DRACOLoader }} from 'three/addons/loaders/DRACOLoader.js';
import {{ KTX2Loader }} from 'three/addons/loaders/KTX2Loader.js';
import {{ TilesRenderer }} from '3d-tiles-renderer';
import {{ GLTFExtensionsPlugin }} from '3d-tiles-renderer/three/plugins';

const config = {configuration};
const viewport = document.querySelector('#viewport');
const status = document.querySelector('#status');
const progress = document.querySelector('#progress');
const progressBar = document.querySelector('#progress-bar');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x071015);

const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 1000000000);
const renderer = new THREE.WebGLRenderer({{ antialias: true, preserveDrawingBuffer: true }});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.mouseButtons.LEFT = null;
controls.mouseButtons.MIDDLE = THREE.MOUSE.PAN;
controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE;
renderer.domElement.addEventListener('contextmenu', (event) => event.preventDefault());

const remappedPointerEvents = new WeakSet();
renderer.domElement.addEventListener('pointerdown', (event) => {{
  if (remappedPointerEvents.has(event) || event.button !== 0 || !event.ctrlKey) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const mappedButton = event.shiftKey ? 1 : 2;
  const mappedEvent = new PointerEvent('pointerdown', {{
    bubbles: true,
    cancelable: true,
    composed: true,
    pointerId: event.pointerId,
    pointerType: event.pointerType,
    isPrimary: event.isPrimary,
    clientX: event.clientX,
    clientY: event.clientY,
    screenX: event.screenX,
    screenY: event.screenY,
    button: mappedButton,
    buttons: mappedButton === 1 ? 4 : 2
  }});
  remappedPointerEvents.add(mappedEvent);
  renderer.domElement.dispatchEvent(mappedEvent);
}}, true);

function panFromTrackpad(deltaX, deltaY) {{
  camera.updateMatrix();
  const offset = camera.position.clone().sub(controls.target);
  const visibleHeight = 2 * offset.length()
    * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
  const worldUnitsPerPixel = visibleHeight / Math.max(renderer.domElement.clientHeight, 1);
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1);
  const movement = right.multiplyScalar(-deltaX * worldUnitsPerPixel * 0.45)
    .add(up.multiplyScalar(deltaY * worldUnitsPerPixel * 0.45));
  camera.position.add(movement);
  controls.target.add(movement);
  controls.update();
}}

function orbitFromTrackpad(deltaX, deltaY) {{
  const offset = camera.position.clone().sub(controls.target);
  const spherical = new THREE.Spherical().setFromVector3(offset);
  spherical.theta -= deltaX * 0.003;
  spherical.phi -= deltaY * 0.003;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi, 0.01, Math.PI - 0.01);
  offset.setFromSpherical(spherical);
  camera.position.copy(controls.target).add(offset);
  camera.lookAt(controls.target);
  controls.update();
}}

renderer.domElement.addEventListener('wheel', (event) => {{
  if (event.ctrlKey) return;
  const isTrackpadMovement = event.deltaMode === WheelEvent.DOM_DELTA_PIXEL
    && (Math.abs(event.deltaX) > 0 || Math.abs(event.deltaY) < 50);
  if (!isTrackpadMovement) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  if (event.shiftKey) orbitFromTrackpad(event.deltaX, event.deltaY);
  else panFromTrackpad(event.deltaX, event.deltaY);
}}, {{ capture: true, passive: false }});

scene.add(new THREE.HemisphereLight(0xc9eff5, 0x16262d, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 2.5);
sun.position.set(4, -3, 8);
scene.add(sun);

const tiles = new TilesRenderer(config.tileset);
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.7/');
const ktx2Loader = new KTX2Loader()
  .setTranscoderPath(
    'https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/libs/basis/'
  )
  .detectSupport(renderer);
tiles.registerPlugin(new GLTFExtensionsPlugin({{ dracoLoader, ktx2Loader }}));
tiles.setCamera(camera);
tiles.setResolutionFromRenderer(camera, renderer);
tiles.errorTarget = 8;
scene.add(tiles.group);

let rootReady = false;
let loadedTiles = 0;

function resize() {{
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / Math.max(height, 1);
  camera.updateProjectionMatrix();
  tiles.setResolutionFromRenderer(camera, renderer);
}}

function fitToView() {{
  const sphere = new THREE.Sphere();
  if (!rootReady || !tiles.getBoundingSphere(sphere) || sphere.radius <= 0) return;
  tiles.group.updateMatrixWorld(true);
  sphere.applyMatrix4(tiles.group.matrixWorld);
  const direction = new THREE.Vector3(0.8, -1.2, 0.65).normalize();
  const distance = sphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov * 0.5));
  camera.position.copy(sphere.center).add(direction.multiplyScalar(distance * 1.08));
  camera.up.set(0, 0, 1);
  camera.near = Math.max(distance / 1000, 0.0001);
  camera.far = Math.max(distance * 1000, 1000);
  camera.updateProjectionMatrix();
  controls.target.copy(sphere.center);
  controls.update();
}}

tiles.addEventListener('load-root-tileset', () => {{
  rootReady = true;
  fitToView();
  status.textContent = '3D Tiles ready · detail streams as you move';
}});
tiles.addEventListener('load-model', () => {{ loadedTiles += 1; }});
tiles.addEventListener('dispose-model', () => {{ loadedTiles = Math.max(0, loadedTiles - 1); }});
tiles.addEventListener('tiles-load-start', () => {{
  progress.hidden = false;
  status.textContent = 'Streaming visible detail…';
}});
tiles.addEventListener('tiles-load-end', () => {{
  progress.hidden = true;
  status.textContent = `${{loadedTiles}} tiles loaded · move closer for more detail`;
}});
tiles.addEventListener('load-error', (event) => {{
  console.error(event.error || event);
  status.textContent = 'Could not load 3D Tiles — see README.txt';
}});

document.querySelector('#fit').addEventListener('click', fitToView);
window.addEventListener('keydown', (event) => {{
  if (event.key.toLowerCase() !== 'f' || event.ctrlKey || event.metaKey || event.altKey) return;
  event.preventDefault();
  fitToView();
}});
document.querySelector('#detail').addEventListener('change', (event) => {{
  tiles.errorTarget = Number(event.target.value);
}});
document.querySelector('#fullscreen').addEventListener('click', () => {{
  document.documentElement.requestFullscreen();
}});
document.querySelector('#screenshot').addEventListener('click', () => {{
  renderer.render(scene, camera);
  const link = document.createElement('a');
  link.download = 'openreef-3d-tiles.png';
  link.href = renderer.domElement.toDataURL('image/png');
  link.click();
}});
window.addEventListener('resize', resize);
resize();

renderer.setAnimationLoop(() => {{
  controls.update();
  camera.updateMatrixWorld();
  tiles.update();
  if (!progress.hidden) {{
    progressBar.style.width = `${{Math.round(tiles.loadProgress * 100)}}%`;
  }}
  renderer.render(scene, camera);
}});
"""


STYLES = """* { box-sizing: border-box; }
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
body { background: #071015; color: #dce9ec; font: 14px system-ui, sans-serif; }
header { position: fixed; z-index: 3; inset: 0 0 auto 0; display: flex; align-items: center;
  justify-content: space-between; padding: 16px 20px; pointer-events: none;
  background: linear-gradient(#071015dd, transparent); }
.brand { color: #62c8cf; font-size: 11px; font-weight: 800; letter-spacing: .16em; }
h1 { margin: 2px 0 0; font-size: 20px; font-weight: 650; }
#status { color: #9bb3ba; }
#viewport { position: absolute; inset: 0; }
#viewport canvas { width: 100%; height: 100%; display: block; touch-action: none; }
#controls { position: fixed; z-index: 4; top: 86px; right: 16px; width: 190px; padding: 12px;
  border: 1px solid #34505b; border-radius: 8px; background: #14242cee;
  box-shadow: 0 8px 30px #0007; }
button, select, input { width: 100%; }
button, select { margin: 0 0 9px; padding: 8px; border: 1px solid #3a5661; border-radius: 5px;
  background: #1c3039; color: #e6f1f3; cursor: pointer; }
button:hover { background: #24505d; border-color: #58aebe; }
label { display: block; margin: 2px 0 9px; color: #a9bec4; font-size: 12px; }
label select, label input { margin-top: 5px; }
#progress { position: fixed; z-index: 5; left: 20%; right: 20%; bottom: 54px; height: 5px;
  border-radius: 4px; overflow: hidden; background: #243940; }
#progress-bar { width: 0; height: 100%; background: #62c8cf; transition: width .15s; }
footer { position: fixed; z-index: 3; bottom: 0; left: 0; right: 0; padding: 12px 20px;
  color: #78949c; pointer-events: none; background: linear-gradient(transparent, #071015dd); }
@media (max-width: 650px) {
  #controls { top: auto; bottom: 48px; width: 165px; }
  #status { display: none; }
}
"""

SERVER_PYTHON = """#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import webbrowser

folder = Path(__file__).resolve().parent
os.chdir(folder)
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
url = f"http://127.0.0.1:{server.server_port}/"
print(f"OpenReef Web is available at {url}")
print("Keep this window open while viewing. Press Control-C to stop.")
webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
"""

LAUNCHER = """#!/bin/zsh
set -eu
cd "${0:A:h}"
exec /usr/bin/python3 serve.py
"""

WINDOWS_LAUNCHER = """@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 serve.py
) else (
  python serve.py
)
pause
"""


def _readme(title: str, model_name: str) -> str:
    return f"""OpenReef Web export: {title}

Double-click “Open OpenReef Web.command” on macOS. A small local web server will
start and the viewer will open in your browser. Keep its Terminal window open
while viewing; press Control-C there to stop it.

On Windows or Linux, open a terminal in this folder and run:

    python3 serve.py

On Windows, you can instead double-click “Open OpenReef Web.bat”. When the
folder comes from Microsoft Teams, first choose “Always keep on this device”
or otherwise wait for model.glb to finish downloading. Do not open index.html
directly: browsers prevent a file:// page from loading the model.

The model is stored as {model_name}. The viewer downloads Three.js {THREE_VERSION}
from jsDelivr, so an internet connection is required when opening the export.
The model itself stays in this folder and is served only from your computer.
"""


def _tiled_readme(title: str) -> str:
    return f"""OpenReef 3D Tiles export: {title}

This viewer uses tiles/tileset.json and fetches only the spatial levels of detail
needed for the current camera view. The complete tiles/ hierarchy must stay
together; tileset.json alone is not the model.

Double-click “Open OpenReef Web.command” on macOS. On Windows, double-click
“Open OpenReef Web.bat”. On Linux, open a terminal in this folder and run:

    python3 serve.py

Do not open index.html directly: browsers prevent a file:// page from fetching
the tile hierarchy. The viewer downloads Three.js {THREE_VERSION} and
3d-tiles-renderer {TILES_RENDERER_VERSION} from jsDelivr, so it needs an internet
connection. The 3D Tiles data stays in this folder and is served only from your
computer.

Important: OpenReef packages an already converted spatial tileset. A single GLB
renamed or wrapped by a tileset.json is still one large download and does not
provide progressive detail. Convert the textured GLB with a photogrammetry-aware
spatial tiler first, then package the resulting complete tileset folder.
"""


def _github_pages_guide(title: str, model_name: str, model_size: int) -> str:
    size_mib = model_size / (1024 * 1024)
    if model_size < GITHUB_REGULAR_FILE_LIMIT:
        size_note = (
            f"This export's `{model_name}` is {size_mib:.1f} MiB, so it is below "
            "GitHub's 100 MiB hard per-file limit."
        )
    else:
        size_note = (
            f"This export's `{model_name}` is {size_mib:.1f} MiB, which exceeds "
            "GitHub's 100 MiB hard per-file limit. Export a lower-complexity GLB "
            "or host the model on object storage; Git LFS does not work with "
            "GitHub Pages."
        )
    return f"""# Publish {title} with GitHub Pages

This `openreef-web` folder is a complete static website. Keep `index.html`,
`viewer.js`, `styles.css`, and `{model_name}` together at the repository root.

{size_note}

1. Create a repository for this exported viewer (for example `openreef-web`).
2. Add every file from this folder, including the empty `.nojekyll` file.
3. Push the files to the repository's `main` branch.
4. In GitHub, open **Settings → Pages**.
5. Under **Build and deployment**, select **Deploy from a branch**.
6. Choose **main**, **/(root)**, then **Save**.
7. Use the published URL shown by GitHub after deployment completes.

The page loads `{model_name}` through a relative URL, so it works both at a
repository Pages address such as `https://USER.github.io/openreef-web/` and at a
custom domain. The viewer code comes from jsDelivr; an internet connection is
required. GitHub Pages is public, so do not publish a sensitive survey model.
"""


def _tiled_github_pages_guide(title: str, tiles_folder: Path) -> str:
    files = tuple(path for path in tiles_folder.rglob("*") if path.is_file())
    largest = max(files, key=lambda path: path.stat().st_size, default=None)
    if largest is None:
        size_note = "The tiles folder is empty; re-export the complete source tileset."
    else:
        largest_size = largest.stat().st_size
        relative = largest.relative_to(tiles_folder).as_posix()
        size_mib = largest_size / (1024 * 1024)
        if largest_size < GITHUB_REGULAR_FILE_LIMIT:
            size_note = (
                f"The largest tile is `tiles/{relative}` at {size_mib:.1f} MiB, below "
                "GitHub's 100 MiB hard per-file limit."
            )
        else:
            size_note = (
                f"`tiles/{relative}` is {size_mib:.1f} MiB and exceeds GitHub's "
                "100 MiB hard per-file limit. Retile with a smaller maximum tile payload "
                "before publishing; Git LFS does not work with GitHub Pages."
            )
    return f"""# Publish {title} 3D Tiles with GitHub Pages

This folder is a complete static streaming viewer. Keep `index.html`, `viewer.js`,
`styles.css`, and the complete `tiles/` hierarchy together at the repository root.

{size_note}

1. Create a repository for this exported viewer.
2. Add every file from this folder, including `.nojekyll` and every file in `tiles/`.
3. Push the files to the repository's `main` branch.
4. In GitHub, open **Settings → Pages**.
5. Under **Build and deployment**, select **Deploy from a branch**.
6. Choose **main**, **/(root)**, then **Save**.

The browser begins with coarse tiles and replaces them with detailed tiles as the
camera moves closer. GitHub Pages is public, so do not publish a sensitive survey.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an OpenReef browser-viewer folder")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--model", type=Path)
    source.add_argument(
        "--tileset",
        type=Path,
        help="package an existing spatial 3D Tiles tileset.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="compress a GLB to a GitHub Pages-safe size below 100 MiB",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.tileset is not None:
            if args.compact:
                raise ValueError("--compact applies to a GLB model, not an existing tileset")
            result = export_tiled_web_viewer(args.tileset, args.output, title=args.title)
        else:
            result = export_web_viewer(
                args.model,
                args.output,
                title=args.title,
                compact=args.compact,
            )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1
    print(f"Exported OpenReef Web to {result.folder}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

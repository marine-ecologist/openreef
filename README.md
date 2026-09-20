## OpenReef: open-source 3D reconstruction workflow imaging coral reefs

<img src="src/openreef/assets/openreef-icon.png" alt="OpenReef icon" width="250" align="right">

OpenReef is an open-source desktop workspace for reconstructing 3D coral and reef-scale 3D models without requiring a US$3,499 Metashape Pro licence. It is designed around underwater photogrammetry and large-area imaging workflows in which overlapping photographs are converted into georeferenced or locally scaled 3D reconstructions that can be revisited through time.

OpenReef adopts the same underlying standardised workflow as [ReefShape](https://github.com/Perry-Institute/ReefShape): standardised acquisition, repeatable reconstruction, explicit quality control, and analysis-ready outputs, but replaces the proprietary Metashape processing dependency with an open-source reconstruction stack. COLMAP performs feature extraction, image matching, camera calibration, and sparse structure-from-motion; OpenMVS then generates dense point clouds, surface meshes, and image-derived textures. An optional OpenSplat/Metal stage trains a Gaussian appearance model from the same registered cameras and undistorted photographs. PyVista/VTK provides local inspection of sparse and dense geometry and camera positions, while the bundled SuperSplat viewer handles full Gaussian appearance rendering.

OpenReef now supports temporary MarkerTags for metric scale. For repeat monitoring, v1.0
will extend this with permanent, stable non-collinear site markers so models can also be
placed in a consistent coordinate frame through time. The end goal is quantitative analysis
of colony dimensions, surface area, volume, structural complexity, and change between surveys.


## Version 0.6.2

See [CHANGELOG.md](CHANGELOG.md) for the recorded 0.2.0–0.6.2 version history.

The desktop workflow is organized as:

```text
Data → Process [Sparse → MarkerTags → Crop → Dense → Texture → Splat → 3D Tiles] → Viewer
```

The left sidebar keeps Data preparation, Process reconstruction, Viewer inspection,
and Projects distinct while leaving the central workspace wide. **Process**
automatically marks existing stages as
Complete, checks unfinished stages, and lets a completed stage be checked again
when it needs recomputing. Each workflow group and individual step reports
Pending, Queued, Running, Complete, or Needs attention while the shared live
terminal continues to stream detailed output.

- Preview photo collections as thumbnails or play a selected source video.
- Sample videos into still frames at a configurable interval using FFmpeg.
- Preserve untouched photos and extracted frames in `original/`, then build
  the pipeline-ready `images/` folder with or without color correction.
- Select a dataset and run individual or contiguous pipeline stages.
- Generate COLMAP features, sequential matches, sparse geometry, automatically
  detect temporary MarkerTags, solve metric scale, and create PINHOLE undistorted images.
- Inspect every disconnected COLMAP sparse model together with its registered
  cameras. OpenReef recommends the model registering the most photographs and
  passes the selected numbered model folder into downstream processing.
- Switch 3D Viewer to **Sparse points + cameras**, inspect every disconnected
  COLMAP model, and save a non-destructive crop before dense reconstruction.
  OpenReef filters the sparse model and OpenMVS reconstruction volume so dense
  compute is not spent on excluded surroundings.
- Import COLMAP output into OpenMVS and generate a dense colored point cloud.
- Select global Original, Medium, Low, and Compact output profiles. Retained
  points default to 100%, 20%, and 5%; Compact derives the smallest cloud and
  mesh needed for a textured GLB below 100 MB.
- Pass every selected dense cloud—including its OpenMVS camera-view metadata—
  into surface reconstruction to create a matching mesh at each level.
- Crop a dense cloud in 3D Viewer and hand it to Surface Mesh without replacing
  the complete cloud. The meshing stage automatically prefers the current
  `scene_dense*_cropped.ply` input.
- Continue through Texture mesh in the same **Process** workflow to
  project registered photographs onto every selected output level and export
  portable, self-contained GLBs.
- Train an optional Gaussian splat from the undistorted COLMAP project using
  OpenSplat. Apple Silicon uses Metal automatically when OpenSplat was built
  with the full Xcode Metal toolchain; checkpoint/resume and live iteration
  progress are integrated into the tab.
- Browse `models/` from a grouped one-column Viewer menu: Sparse cloud, Dense
  cloud, Surface mesh, Texture mesh, Gaussian splat, and Custom saves, with
  High, Medium, Low, and Compact levels shown where available.
- Selecting a Gaussian PLY activates the bundled SuperSplat WebGL renderer,
  including anisotropic splat rotation, opacity, scale, and spherical-harmonic
  appearance. Gaussian output is never opened automatically.
- Preview and save a conservative Gaussian cleanup that removes very faint or
  unusually large splats and, when available, keeps only the saved survey crop.
  Cleanup always writes a new PLY and leaves the trained source unchanged.
- Export the current Viewer model from the right sidebar into an
  `openreef-web/` browser-viewer folder. GLB texture sidecars are embedded into
  `model.glb`, with textured, wire-mesh, solid-plus-wire, and 1 px point views.
- Keep the Viewer responsive while processing continues in the background.
- Follow every stage through per-stage and overall progress bars, elapsed time,
  current-stage status, and streaming terminal output.
- Control CPU threads, an optional process RAM ceiling, camera model, GPU use,
  image size, sequence overlap, dense resolution, neighbor views, fusion
  agreement, colors, normals, texture image scale, atlas size, sharpness, and
  seam blending.
- Open PLY, OBJ, and GLB files (GLB depends on the bundled VTK reader).
- Display meshes and point clouds, including per-vertex RGB/RGBA colors.
- Orbit, pan, zoom, fit to view, switch projection, and use six standard views.
- Use the same Tinkercad-style mouse and trackpad controls for sparse points,
  dense clouds, meshes, textured models, Gaussian splats, and web exports.
- Use solid, wireframe, or solid-with-wireframe mesh display.
- Adjust point size and inspect basic model statistics.
- Capture any current viewing angle and export a fitted 2K, 4K, or 8K
  orthographic PNG with an optional transparent background. This is a render-only
  visual orthomosaic, not a georeferenced measurement product.
- Trim meshes or point clouds with a camera-aligned freehand lasso: retain the
  circled colony or delete the circled material, then undo, reset, or save a
  new file without overwriting the source model.
- Crop textured GLBs by retaining or removing complete original triangles, so
  retained faces keep their existing UV coordinates and image-atlas mapping.
- Save edited textured models as new self-contained GLBs. OpenReef embeds any
  external OpenMVS texture images into the saved GLB; untextured meshes and
  point clouds continue to save as PLY or VTP. Textured GLB saving requires
  100% Viewer complexity so the retained triangles still match the source
  texture atlas; use the generated Medium or Low GLB for a smaller source.
- Adjust mesh complexity continuously from 5–100%. Lasso cuts are replayed
  against the source mesh before the selected output complexity is saved.
- Export screenshots and save or restore JSON camera viewpoints.

OpenReef 0.6.2 includes OpenMVS surface reconstruction and texturing,
sparse-camera QA, a downstream processing ROI, and an initial non-destructive
lasso-trimming workflow, plus optional OpenSplat training and MarkerTag metric scaling. It
does **not** yet perform hole filling, mesh repair, permanent-site alignment, or scientific
analysis.

### MarkerTags: temporary scale markers

MarkerTags are non-permanent AprilTag field markers placed in a survey to give the
reconstruction metric scale. After sparse reconstruction, OpenReef scans the source images,
matches detections to registered COLMAP cameras, triangulates each tag's four canonical
corners and centre across views, and robustly combines the reconstructed edge lengths. The
default family is `tag36h11` and the known encoded-square edge is `0.050 m` (50 mm).

The tag edge is the only scale reference. The current physical carrier is a 90 mm diameter,
8 mm high disc with the tag face raised by 0.6 mm; none of those carrier dimensions enters
the scale solve. A scale is accepted only when a tag is detected across registered images,
at least two edges reconstruct, and the edge estimates agree within the validation limits.
Otherwise the workflow continues explicitly unscaled and records the reason.

The complete audit record is written to `models/<dataset>_markertags.json`: family and IDs,
source images, pixel corners/centres, registered image and camera IDs, reconstructed 3D
corners/centres where available, observation counts, scale factor, and residual. A validated
metric copy of the COLMAP model is created under `colmap/metric/sparse/` before undistortion,
so dense clouds, meshes, textures, tiles, and Gaussian outputs inherit metre coordinates.
The raw sparse reconstruction under `colmap/sparse/` is retained unchanged.

Command-line configuration uses `--marker-tag-family` and `--marker-tag-size-m`; the desktop
Render workflow exposes the same family and edge-size settings. Permanent site markers are a
separate future marker class: unlike temporary MarkerTags, they may later establish a stable
coordinate frame and cross-survey alignment, not just scale.

### Setup and run

OpenReef is tested on macOS and requires Python 3.10 or newer, COLMAP, OpenMVS,
and a working OpenGL environment.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e .
openreef                              # empty workspace
openreef path/to/dataset              # select a dataset immediately
openreef path/to/model.ply            # open a model in Viewer
```

OpenReef can also be run as a module:

```bash
python -m openreef path/to/dataset
```

### Dense and textured mesh workflow

The **Process** view presents Sparse cloud, the optional crop checkpoint,
Dense cloud, Texture mesh, and Gaussian splat as one left-to-right workflow.
Dense Cloud creates the selected point clouds and surface meshes. Texture Mesh
then uses OpenMVS to project the registered source photographs onto any matching
Original, Medium, Low, or Compact mesh:

```text
Dense point cloud → Surface mesh → Texture mesh
```

In the Texture mesh settings, select the global output levels, leave **Texture image
scale** at `0` for the best available image resolution, and run the selected
stage. Level `1` uses half-size images and level `2` uses quarter-size images,
reducing memory use and runtime. The default 8192 px atlas size, 0.5 sharpness,
patch balancing, and seam blending are suitable starting values.

OpenReef exports GLB because it stores mesh geometry, materials, and texture
images together in one portable file. Finished files are linked into `models/`
with dataset-based names. In 3D Viewer, open the GLB and select **Solid** or
**Solid + wireframe** to display its embedded texture.

### Gaussian Splat workflow

**Gaussian splat** is an optional appearance-reconstruction path within Render
images. It uses
the registered cameras, sparse points, and PINHOLE images already produced in
`colmap/dense/`; it does not derive splats from the textured mesh. OpenReef
creates a managed `gaussian/input/` bridge in the COLMAP layout expected by
[OpenSplat](https://github.com/WebODM/OpenSplat), then writes
`gaussian/<dataset>_gaussian.ply`, its camera JSON, and a friendly link in
`models/`.

The defaults deliberately suit machines no faster than the current 64 GB M2
Max reference system:

- **Preview:** 7,000 iterations, 4× image downscale, maximum 2 million splats.
- **Balanced:** 15,000 iterations, 2× image downscale, maximum 3.5 million splats.
- **High:** 30,000 iterations, full images, maximum 5 million splats.

Start with Preview even on the M2 Max. Training speed is usually the constraint;
64 GB unified memory gives useful headroom, so the RAM ceiling remains Unlimited
by default. The low-memory cache option trades speed for a smaller working set.
OpenReef saves a checkpoint every 1,000 steps and resumes the current PLY when
possible. The stage card switches from an activity indicator to real iteration
percentage as soon as OpenSplat prints its first training step.

OpenSplat is a separate AGPL-3.0 program and is not installed by the Python
package. On macOS, install its prerequisites and build it once:

```bash
brew install cmake opencv pytorch libomp assimp
git clone https://github.com/WebODM/OpenSplat.git ~/OpenSplat
cmake -S ~/OpenSplat -B ~/OpenSplat/build \
  -DCMAKE_PREFIX_PATH="$(brew --prefix pytorch)" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build ~/OpenSplat/build --parallel 12
```

A Metal build requires the full Xcode application and Metal toolchain, not only
Apple's Command Line Tools. Confirm that `xcrun -sdk macosx metal --version`
works before building. Then select `~/OpenSplat/build/opensplat` in the tab.
If macOS blocks PyTorch libraries on first launch, allow each reported library
under **System Settings → Privacy & Security**. CPU fallback is exposed for
compatibility but is roughly 100× slower according to OpenSplat and is not a
practical default.

The 3D Viewer lists Gaussian outputs under **Gaussian splat** in its model menu.
Selecting one opens a bundled build of
[PlayCanvas SuperSplat Viewer](https://github.com/playcanvas/supersplat-viewer)
rather than
drawing the PLY as ordinary glowing points. The renderer uses each splat's full
ellipsoid rotation, scale, opacity, and spherical-harmonic appearance. It uses
WebGL inside the desktop app for Mac compatibility; **Open in browser** lets the
same viewer choose WebGPU in a current browser when available. It uses the same
navigation as the mesh and cloud viewer: right-drag, Ctrl + left-drag, or
Shift + two-finger movement orbits; middle-drag, Shift + right-drag,
Ctrl + Shift + left-drag, or ordinary two-finger movement pans; pinch or the
mouse wheel zooms; and `F` frames the scene. A plain left-click is reserved for
selection. When a crop tool is active, left-drag draws the selection instead.

The Viewer sidebar also provides non-destructive Gaussian cleanup. **Preview**
filters splats below the chosen opacity, removes the largest or most stretched
outliers, and can apply the sparse-stage crop bounds. OpenReef applies a
conservative display-only version when a splat first opens to suppress the long
rays produced by malformed ellipsoids. **Original** returns to the trained
file, while **Save cleaned splat…** writes a complete Gaussian PLY under Custom
saves without changing the source. This helps with obvious floaters, but it
cannot repair weak camera registration or moving-water artefacts in training.
CF-3DGS remains a future remote NVIDIA/CUDA backend, and Splat Labs is a possible
later publishing destination rather than the reconstruction engine.

### Web Export

In **Viewer**, open or crop a GLB/PLY model, then choose **Export current
model…** under OpenReef Web in the right sidebar. OpenReef automatically creates
or updates `openreef-web/` in the dataset root, beside `models/`, `colmap/`, and
`openmvs/`. It contains the current model, `index.html`, its viewer files, local
launchers for macOS and Windows, and a GitHub Pages guide. For OpenMVS GLBs,
external texture PNGs are embedded into `model.glb` so the web export does not
depend on sidecar image paths.

Choose **Export compact (<100 MB)** for GitHub Pages. This leaves the source GLB
unchanged, embeds its textures, then progressively resizes and JPEG-compresses
opaque texture atlases until the complete GLB is below a conservative 95 MiB
target. Transparent textures remain PNG. If geometry alone prevents that target,
OpenReef stops without writing an oversized result and asks for a lower-resolution
textured mesh. The command-line equivalent adds `--compact` to
`python -m openreef.web_export`.

After **Gaussian splat** in **Process**, use the narrow **3D tiles**
checkpoint and choose the highest-detail textured GLB in `models/`. OpenReef now
builds the hierarchy itself: Assimp converts the textured mesh, OpenReef divides
its triangles spatially, reuses the smallest Compact/Low textured GLB as a
coarse root when it can be kept below 12 MiB, and writes detailed glTF leaf
tiles. Each leaf receives a compressed, maximum 1024 px local atlas containing
only the texture islands used by that tile. It then creates
`openreef-web-tiles/` and adds a portable
`*_3d_tiles.json` entry to `models/`.

Select **3D tiles → Streaming viewer** in the 3D Viewer model menu to open the
result inside OpenReef. The viewer initially transfers the optional coarse root
and loads visible spatial leaves as the camera moves closer. If a useful coarse
root cannot fit within the 12 MiB ceiling it is omitted, avoiding a large startup
download. This is a real 3D Tiles 1.1 `REPLACE` hierarchy rather than a single
GLB wrapped in `tileset.json`. Assimp is required (`brew install assimp` on
macOS). Existing externally generated hierarchies can still be packaged with
`python -m openreef.web_export --tileset path/to/tileset.json --output ...`.

On macOS, double-click that command file to open the model in the default web
browser. Keep the accompanying Terminal window open while viewing. The model is
served only from the exported folder on the local computer; an internet
connection is currently required to load the Three.js viewer library.

The same `openreef-web/` folder is ready for **GitHub Pages**. Put its contents at
the root of a repository, then in **Settings → Pages** select **Deploy from a
branch**, `main`, and `/(root)`. The generated `GITHUB-PAGES.md` records these
steps and checks whether the exported model is below GitHub's 100 MiB per-file
limit. Git LFS cannot be used by GitHub Pages, so larger models need a lower
complexity export or separate web/object storage.

For a **Microsoft Teams** folder, keep the whole `openreef-web/` directory
together and mark it **Always keep on this device** before opening it. Teams and
SharePoint store the files but do not serve them as a website, so `index.html`
cannot load the GLB directly from a `file://` address. Double-click the generated
`.command` launcher on macOS or `.bat` launcher on Windows; it starts a local
web address and opens the viewer. Use GitHub Pages when the model should open
from one shareable HTTPS link without downloading the folder first.

### Command-line pipeline (no GUI)

Run the complete reconstruction directly in Terminal with the included script:

```bash
./scripts/openreef-pipeline.sh /path/to/dataset
```

The default pipeline runs feature extraction, sequential matching, sparse
reconstruction, image undistortion/PINHOLE conversion, OpenMVS import, dense
point-cloud generation, surface-mesh reconstruction, and GLB texturing. Output
already on disk is skipped, so the same command can resume an interrupted
dataset. Live COLMAP and OpenMVS output is printed in Terminal; press
`Control-C` to stop.

Useful examples:

```bash
# Limit the run to 8 cores and 24 GB of RAM
./scripts/openreef-pipeline.sh /path/to/dataset --cores 8 --memory-gb 24

# Run without COLMAP GPU acceleration
./scripts/openreef-pipeline.sh /path/to/dataset --no-gpu

# Run only the OpenMVS stages
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages openmvs_import,dense,mesh,texture

# Create Medium and Low clouds, meshes, and textured GLBs
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages dense,mesh,texture --dense-medium --dense-low

# Override the default retained-point percentages
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages dense,mesh,texture --dense-medium --dense-low \
  --dense-medium-percent 30 --dense-low-percent 10

# Texture existing selected meshes using half-resolution source images
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages texture --texture-resolution-level 1

# Rebuild the surface mesh even when it already exists
./scripts/openreef-pipeline.sh /path/to/dataset --stages mesh --force

# Train the optional safe local Gaussian preview after Sparse Cloud completes
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages gaussian \
  --opensplat-executable ~/OpenSplat/build/opensplat
```

Use `./scripts/openreef-pipeline.sh --help` for all camera, matching, image-size,
dense-resolution, neighboring-view, CPU, RAM, and stage-selection options. The
finished friendly filenames are collected in `models/`, including
`dataset_sparsecloud.ply`, `dataset_densecloud_high.ply`, optional
`dataset_densecloud_medium.ply` and `dataset_densecloud_low.ply`, and
matching `dataset_mesh_medium.ply` and `dataset_mesh_low.ply` files.
Textured outputs use `dataset_textured_mesh.glb`, with optional
`dataset_textured_mesh_medium.glb` and `dataset_textured_mesh_low.glb` files.
`dataset_densecloud.ply` remains as a compatibility name for the High cloud.

After an editable installation, the same runner is also available as:

```bash
openreef-pipeline /path/to/dataset
```

### Dataset folder structure

Each dataset must contain an `images/` directory at its root.

```text
dataset/
├── images/
│   ├── frame_000001.jpg
│   ├── frame_000002.jpg
│   └── ...
│
├── models/
│   ├── dataset_sparsecloud.ply
│   ├── dataset_cameras.json
│   ├── dataset_roi.json
│   ├── dataset_densecloud.ply
│   ├── dataset_densecloud_high.ply
│   ├── dataset_densecloud_medium.ply
│   ├── dataset_densecloud_low.ply
│   ├── dataset_dense_cropped.ply
│   ├── dataset_mesh.ply
│   ├── dataset_mesh_medium.ply
│   ├── dataset_mesh_low.ply
│   ├── dataset_textured_mesh.glb
│   ├── dataset_textured_mesh_medium.glb
│   ├── dataset_textured_mesh_low.glb
│   ├── dataset_gaussian.ply
│   └── dataset_mesh_lores.ply
│
├── openreef-web/
│   ├── model.glb or model.ply
│   ├── index.html
│   ├── viewer.js
│   ├── GITHUB-PAGES.md
│   ├── Open OpenReef Web.command
│   └── Open OpenReef Web.bat
│
├── gaussian/
│   ├── input/
│   │   ├── images -> ../../colmap/dense/images
│   │   └── sparse/0 -> ../../../colmap/dense/sparse
│   ├── dataset_gaussian.ply
│   └── dataset_cameras.json
│
├── colmap/
│   ├── database.db
│   ├── sparse/
│   │   ├── selected -> 0/
│   │   ├── 0/
│   │   │   ├── cameras.bin
│   │   │   ├── images.bin
│   │   │   ├── points3D.bin
│   │   │   └── points3D.ply
│   │   └── 1/ ...
│   └── dense/
│       ├── images/
│       └── sparse/
│           ├── cameras.bin
│           ├── images.bin
│           └── points3D.bin
│
└── openmvs/
    ├── images/
    ├── scene.mvs
    ├── scene_dense.mvs
    ├── scene_dense.ply
    ├── scene_dense_cropped.ply
    ├── scene_dense_medium.ply
    ├── scene_dense_low.ply
    ├── scene_mesh.mvs
    ├── scene_mesh.ply
    ├── scene_mesh_medium.mvs
    ├── scene_mesh_medium.ply
    ├── scene_mesh_low.mvs
    ├── scene_mesh_low.ply
    ├── scene_mesh_textured.glb
    ├── scene_mesh_medium_textured.glb
    └── scene_mesh_low_textured.glb
```

If a pre-existing dataset contains only `images/`, OpenReef adopts those files
into `original/` before rebuilding `images/`. Preparation is atomic: the
current `images/` folder is not replaced until the new set is complete. Files
are linked instead of duplicated where the filesystem permits.

OpenReef keeps COLMAP and OpenMVS working filenames in place and exposes
readable dataset-based outputs in the root-level `models/` folder. For example,
a dataset named `natans` uses `natans_sparsecloud.ply`, `natans_mesh.ply`, and
`natans_densecloud.ply`; its current editing proxy is saved as
`natans_mesh_lores.ply`. Existing v0.1 `images/meshes/` content is migrated and
that old path becomes a compatibility link to `models/`. Rebuilding unchanged
inputs preserves the models folder; changing the image source archives it with
the invalidated reconstruction.

Changing the input source or enabling color correction invalidates previously
computed features and geometry. OpenReef moves existing `colmap/`, `openmvs/`,
and `models/` directories into a timestamped `.openreef/history/` directory
before installing the new `images/` set. This is a recoverable archive, not a
deletion. Adopting unchanged existing images without correction leaves current
results in place.

The optional correction matches the earlier `colorprocess.py`: mild red-channel
compensation, gray-world balance, CLAHE on luminance, a slight gamma adjustment,
and very mild sharpening. It is intentionally conservative for photogrammetry
and disabled by default.

Reconstruction outputs retain the shell-pipeline layout:
`colmap/database.db`, `colmap/sparse`, `colmap/dense`, and
`openmvs/scene*.mvs`. When OpenMVS writes `scene_dense.ply`, Process offers
it directly to 3D Viewer.

The RAM control is an optional hard ceiling for the active child process. It is
unlimited by default because an undersized ceiling can cause COLMAP or OpenMVS
to exit. Stop first requests a graceful process shutdown; if the tool does not
respond within five seconds, OpenReef terminates it.

In 3D Viewer, select **Sparse points + cameras**, choose among the numbered
sparse-model folders, inspect its points and camera frustums, then draw a crop
when only part of that reconstruction should continue into OpenMVS. The model
registering the most images is recommended automatically. The choice is stored
as the folder link `colmap/sparse/selected`; the numbered COLMAP folders are
never merged or removed. Changing the selected model requires undistortion and
downstream stages to be rerun. Changing or clearing the ROI marks OpenMVS
outputs as needing a rerun.

COLMAP creates multiple numbered sparse models when its image-match graph has
disconnected components: there are enough trustworthy matches to reconstruct
each component internally, but not enough shared geometry to place the
components in one coordinate system. OpenReef keeps that uncertainty visible
instead of guessing a transformation between unrelated components.

In 3D Viewer, use **Open model…** and **Save as…** at the top of the right panel.
Open a textured GLB and switch from the default Wireframe mode to Solid to see
its embedded image texture. GLB keeps the geometry, materials, and texture
atlases together in one file. Right-drag, Ctrl + left-drag, or Shift +
two-finger movement orbits. Middle-drag, Shift + right-drag, Ctrl + Shift +
left-drag, or ordinary two-finger movement pans. Pinch or the mouse wheel zooms,
and `F` fits the whole model into view. A plain left-click is reserved for
selection; when a crop tool is active, left-drag draws the selection. Meshes
open in wireframe mode by default. Mesh trimming and
complexity controls live in this Viewer rather than a separate editing tab. The
application menu exposes dataset/model selection, Screenshot, Save Viewpoint,
and Load Viewpoint commands.

For an orthomosaic-style image, rotate the mesh or cloud to the required angle,
choose **Set current viewing angle**, select the output resolution, then choose
**Export orthomosaic PNG**. OpenReef temporarily uses orthographic projection,
fits the complete model, renders meshes as a solid textured surface, and then
restores the interactive camera. MarkerTags can provide metric scale in version
0.6, but the PNG has no geospatial coordinate reference and remains intended for
visual comparison and QA rather than mapped distance or area measurements.


For development:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```


### architecture

```text
src/openreef/
├── app.py                 startup and command-line entry point
├── web_export.py          portable HTML viewer-folder generator
├── core/
│   ├── camera.py          serializable camera viewpoint state
│   ├── glb_edit.py        texture-preserving triangle-subset GLB writer
│   ├── mesh_edit.py       screen-projected lasso clipping and edited-file export
│   ├── model.py           model parts, color discovery, and statistics
│   └── scene.py           PyVista scene and rendering controls
├── pipeline/
│   ├── cli.py             complete terminal pipeline without the GUI
│   ├── stages.py          dataset contract, validation, and stage commands
│   ├── runner.py          asynchronous queue, live progress, logs, and cancellation
│   ├── limited_exec.py    optional per-process RAM ceiling
│   └── tasks.py           OpenMVS preparation and multi-level dense/mesh/texture tasks
├── io/
│   ├── colmap_model.py    camera-pose reader, sparse ROI, and model filtering
│   ├── gaussian_ply.py    Gaussian detection, cleanup, and attribute-safe PLY I/O
│   └── model_loader.py    PLY/OBJ/GLB loading and multiblock normalization
└── ui/
    ├── controls.py        view, mesh editing, complexity, open/save, and statistics
    ├── pipeline_page.py   stage cards, compute options, and live terminal
    ├── points_viewer_page.py sparse-point, camera, and processing-ROI viewer
    ├── splat_viewer_page.py local server and embedded SuperSplat browser view
    ├── viewport.py        mouse, trackpad, and freehand lasso interaction
    └── main_window.py     tabbed Qt application shell and user actions
```

The GUI launches one selected stage at a time through `QProcess`, so tool output
streams into the interface without blocking the Qt event loop or Viewer. The
terminal pipeline shares the same stage definitions and validation, but runs
synchronously and streams tool output directly to the shell. Every command is
constructed as an argument list rather than shell text. The loader returns a
format-neutral `ModelDocument`, keeping rendering independent from reconstruction.


## Roadmap

- **0.6:** MarkerTag metric scaling, spatial 3D Tiles, and the neutral sidebar
  workspace design.
- **Next:** richer material controls, mesh repair, measurement, and annotations.
- **Later:** alignment, batch/timelapse orchestration, and scientific change
  analysis. Processing will remain separate from the viewer core so OpenReef
  can still be used as a lightweight QA application.

## License

OpenReef is released under the MIT License. The bundled SuperSplat Viewer is
also MIT-licensed; its notice is retained in
`src/openreef/assets/supersplat/LICENSE`. COLMAP, OpenMVS, and OpenSplat remain
separate tools under their respective licences.

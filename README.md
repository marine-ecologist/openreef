## OpenReef: open-source 3D reconstruction workflow imaging coral reefs

<img src="src/openreef/assets/openreef-icon.png" alt="OpenReef icon" width="250" align="right">

OpenReef is an open-source desktop workspace for reconstructing 3D coral and reef-scale 3D models without requiring a US$3,499 Metashape Pro licence. It is designed around underwater photogrammetry and large-area imaging workflows in which overlapping photographs are converted into georeferenced or locally scaled 3D reconstructions that can be revisited through time.

OpenReef adopts the same underlying standardised workflow as [ReefShape](https://github.com/Perry-Institute/ReefShape): standardised acquisition, repeatable reconstruction, explicit quality control, and analysis-ready outputs, but replaces the proprietary Metashape processing dependency with an open-source reconstruction stack. COLMAP performs feature extraction, image matching, camera calibration, and sparse structure-from-motion; OpenMVS then generates dense point clouds, surface meshes, and image-derived textures. A PyVista/VTK-based viewer provides local inspection of the sparse and dense reconstruction, camera geometry, and model quality.

For repeat monitoring, v1.0 of OpenReef will  support fixed or temporary scale bars, coded targets, and stable non-collinear reference markers so that models can be placed in a consistent scale and coordinate frame through time, allowing reconstructions to become a quantitative monitoring product rather than simply a 3D visualisation. The end goal of OpenReef will be to support measurements such as colony dimensions, surface area, volume, structural complexity, and change between surveys.


## Version 0.2

- Preview photo collections as thumbnails or play a selected source video.
- Sample videos into still frames at a configurable interval using FFmpeg.
- Preserve untouched photos and extracted frames in `original/`, then build
  the pipeline-ready `images/` folder with or without color correction.
- Select a dataset and run individual or contiguous pipeline stages.
- Generate COLMAP features, sequential matches, sparse geometry, and PINHOLE
  undistorted images.
- Inspect every disconnected COLMAP sparse model together with its registered
  cameras. OpenReef recommends the model registering the most photographs and
  passes the selected numbered model folder into downstream processing.
- Draw and save a non-destructive 3D processing ROI in Points Viewer. OpenReef
  filters the sparse model to that region before OpenMVS estimates and crops
  its dense reconstruction volume.
- Import COLMAP output into OpenMVS and generate a dense colored point cloud.
- Select Original, Medium, and Low output levels, with editable retained-point
  percentages defaulting to 100%, 20%, and 5%.
- Pass every selected dense cloud—including its OpenMVS camera-view metadata—
  into surface reconstruction to create a matching mesh at each level.
- Continue from **Dense Cloud** into the separate **Texture Mesh** tab to project
  registered photographs onto any selected Original, Medium, or Low mesh and
  export a portable, self-contained GLB.
- Create an `openreef-web/` browser-viewer folder from a GLB or PLY model, with
  a double-click macOS launcher, display controls, fit-to-view, and screenshots.
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
- Use Tinkercad-style trackpad controls: two-finger movement pans and pinch
  gestures zoom.
- Use solid, wireframe, or solid-with-wireframe mesh display.
- Adjust point size and inspect basic model statistics.
- Trim meshes or point clouds with a camera-aligned freehand lasso: retain the
  circled colony or delete the circled material, then undo, reset, or save a
  new PLY/VTP file without overwriting the source model.
- Adjust mesh complexity continuously from 5–100%. Lasso cuts are replayed
  against the source mesh before the selected output complexity is saved.
- Export screenshots and save or restore JSON camera viewpoints.

OpenReef 0.2 includes OpenMVS surface reconstruction and texturing,
sparse-camera QA, a downstream processing ROI, and an initial non-destructive
lasso-trimming workflow. It does **not** yet perform hole filling or mesh
repair, alignment, scaling, or scientific analysis.

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

The reconstruction workflow is split into top-level **Sparse Cloud**, **Dense
Cloud**, and **Texture Mesh** tabs. Dense Cloud creates the selected point
clouds and surface meshes. Texture Mesh then uses OpenMVS to project the
registered source photographs onto any matching Original, Medium, or Low mesh:

```text
Dense point cloud → Surface mesh → Texture mesh
```

In Texture Mesh, select the mesh levels to texture, leave **Texture image
scale** at `0` for the best available image resolution, and run the selected
stage. Level `1` uses half-size images and level `2` uses quarter-size images,
reducing memory use and runtime.
The default 8192 px atlas size, 0.5 sharpness, patch balancing, and seam blending
are suitable starting values.

OpenReef exports GLB because it stores mesh geometry, materials, and texture
images together in one portable file. Finished files are linked into `models/`
with dataset-based names. In 3D Viewer, open the GLB and select **Solid** or
**Solid + wireframe** to display its embedded texture.

### Web Export

Open **Web Export**, choose a dataset and one of its GLB or PLY models, then
choose an output folder. The default is `dataset/openreef-web/`. OpenReef copies
the model and creates `index.html`, its viewer files, a small local server, and
`Open OpenReef Web.command`.

On macOS, double-click that command file to open the model in the default web
browser. Keep the accompanying Terminal window open while viewing. The model is
served only from the exported folder on the local computer; an internet
connection is currently required to load the Three.js viewer library.

### Command-line pipeline (no GUI)

Run the complete reconstruction directly in Terminal with the included script:

```bash
/Users/rof011/openreef/scripts/openreef-pipeline.sh \
  /Users/rof011/Desktop/LC_timelapse/cervicornis
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

On this workstation, double-click `OpenReef.command` on the Desktop to open the
`cervicornis` dataset. A different dataset folder can be dragged onto the same
launcher.

Each dataset must contain an `images/` directory. 

### Dataset folder structure

Each dataset must contain an `images/` directory at its root.

```text
dataset/
└── images/
    ├── frame_000001.jpg
    ├── frame_000002.jpg
    ├── frame_000003.jpg
    └── ...
```
openreef creates the following folder structure:

```text
dataset/
├── images/
│   ├── frame_000001.jpg
│   ├── frame_000002.jpg
│   ├── frame_000003.jpg
│   └── ...
│
├── models/
│   ├── dataset_sparsecloud.ply  -> COLMAP sparse cloud
│   ├── dataset_cameras.json     registered COLMAP camera poses
│   ├── dataset_roi.json         optional downstream processing ROI
│   ├── dataset_densecloud.ply   -> compatibility link to High
│   ├── dataset_densecloud_high.ply    -> complete OpenMVS dense cloud
│   ├── dataset_densecloud_medium.ply  -> optional 20% viewing cloud
│   ├── dataset_densecloud_low.ply     -> optional 5% viewing cloud
│   ├── dataset_mesh.ply         -> OpenMVS full mesh
│   ├── dataset_mesh_medium.ply  -> optional Medium surface mesh
│   ├── dataset_mesh_low.ply     -> optional Low surface mesh
│   ├── dataset_textured_mesh.glb         -> complete textured mesh
│   ├── dataset_textured_mesh_medium.glb  -> optional Medium textured mesh
│   ├── dataset_textured_mesh_low.glb     -> optional Low textured mesh
│   └── dataset_mesh_lores.ply   current Viewer complexity preview
│
├── colmap/
│   ├── database.db
│   │
│   ├── sparse/
│   │   ├── selected -> 0/       current downstream model selection
│   │   ├── 0/
│   │   │   ├── cameras.bin
│   │   │   ├── images.bin
│   │   │   ├── points3D.bin
│   │   │   └── points3D.ply
│   │   └── 1/ ...              additional disconnected models, when present
│   │
│   └── dense/
│       ├── images/
│       │   └── undistorted input images
│       │
│       └── sparse/
│           ├── cameras.bin
│           ├── images.bin
│           └── points3D.bin
│
└── openmvs/
    ├── images/
    │   └── undistorted images used by OpenMVS
    │
    ├── scene.mvs
    ├── scene_dense.mvs
    ├── scene_dense.ply
    ├── scene_dense_medium.ply   optional 20% viewing cloud
    ├── scene_dense_low.ply      optional 5% viewing cloud
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
before installing the new `images/` set. This is a recoverable archive, not a deletion.
Adopting unchanged existing images without correction leaves current results in
place.

The optional correction matches the earlier `colorprocess.py`: mild red-channel
compensation, gray-world balance, CLAHE on luminance, a slight gamma adjustment,
and very mild sharpening. It is intentionally conservative for photogrammetry
and disabled by default.

Reconstruction outputs retain the shell-pipeline layout:
`colmap/database.db`, `colmap/sparse`, `colmap/dense`, and
`openmvs/scene*.mvs`. When OpenMVS writes `scene_dense.ply`, the Dense Cloud tab
offers it directly to 3D Viewer.

The RAM control is an optional hard ceiling for the active child process. It is
unlimited by default because an undersized ceiling can cause COLMAP or OpenMVS
to exit. Stop first requests a graceful process shutdown; if the tool does not
respond within five seconds, OpenReef terminates it.

In Points Viewer, choose among the numbered sparse-model folders, inspect its
points and camera frustums, then draw a processing ROI when only part of that
reconstruction should continue into OpenMVS. The model registering the most
images is recommended automatically. The choice is stored as the folder link
`colmap/sparse/selected`; the numbered COLMAP folders are never merged or
removed. Changing the selected model requires undistortion and downstream
stages to be rerun. Changing or clearing the ROI marks OpenMVS outputs as
needing a rerun.

COLMAP creates multiple numbered sparse models when its image-match graph has
disconnected components: there are enough trustworthy matches to reconstruct
each component internally, but not enough shared geometry to place the
components in one coordinate system. OpenReef keeps that uncertainty visible
instead of guessing a transformation between unrelated components.

In 3D Viewer, use **Open model…** and **Save as…** at the top of the right panel.
Open a textured GLB and switch from the default Wireframe mode to Solid to see
its embedded image texture. GLB keeps the geometry, materials, and texture
atlases together in one file.
Orbit with the left mouse button, pan with the middle button or a
two-finger trackpad move, and zoom with pinch, a mouse wheel, or the right button. Meshes
open in wireframe mode by default. Mesh trimming and complexity controls live
in this Viewer rather than a separate editing tab. The application menu exposes
dataset/model selection, Screenshot, Save Viewpoint, and Load Viewpoint commands.


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
│   ├── mesh_edit.py       screen-projected lasso clipping and edited-file export
│   ├── model.py           model parts, color discovery, and statistics
│   └── scene.py           PyVista scene and rendering controls
├── pipeline/
│   ├── cli.py             complete terminal pipeline without the GUI
│   ├── stages.py          dataset contract, validation, and stage commands
│   ├── runner.py          asynchronous queue, progress, logs, and cancellation
│   ├── limited_exec.py    optional per-process RAM ceiling
│   └── tasks.py           OpenMVS preparation and multi-level dense/mesh/texture tasks
├── io/
│   ├── colmap_model.py    camera-pose reader, sparse ROI, and model filtering
│   └── model_loader.py    PLY/OBJ/GLB loading and multiblock normalization
└── ui/
    ├── controls.py        view, mesh editing, complexity, open/save, and statistics
    ├── pipeline_page.py   stage cards, compute options, and live terminal
    ├── points_viewer_page.py sparse-point, camera, and processing-ROI viewer
    ├── viewport.py        mouse, trackpad, and freehand lasso interaction
    ├── web_export_page.py model selection, copy progress, and browser export
    └── main_window.py     tabbed Qt application shell and user actions
```

The GUI launches one selected stage at a time through `QProcess`, so tool output
streams into the interface without blocking the Qt event loop or Viewer. The
terminal pipeline shares the same stage definitions and validation, but runs
synchronously and streams tool output directly to the shell. Every command is
constructed as an argument list rather than shell text. The loader returns a
format-neutral `ModelDocument`, keeping rendering independent from reconstruction.


## Roadmap

- **0.3:** multi-model history, richer material controls, mesh repair,
  measurement, scale metadata, and annotations.
- **Later:** alignment, batch/timelapse orchestration, and scientific change
  analysis. Processing will remain separate from the viewer core so OpenReef
  can still be used as a lightweight QA application.

## License

OpenReef is released under the MIT License.

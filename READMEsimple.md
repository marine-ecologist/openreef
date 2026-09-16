## OpenReef: a beginner's guide for ecologists

<img src="src/openreef/assets/openreef-icon.png" alt="OpenReef icon" width="250" align="right">

OpenReef turns overlapping photographs or video frames into 3D records of coral
colonies and reef areas. It brings the main processing steps into one desktop
application and uses free, open-source reconstruction software.

The project is intended for ecologists who want to inspect, compare, and
eventually measure reefs through time without depending on proprietary
photogrammetry software. OpenReef follows the same broad idea as
[ReefShape](https://github.com/Perry-Institute/ReefShape): consistent image
collection, visible quality checks, repeatable processing, and clearly stored
outputs.

OpenReef is under active development. Version 0.5 can build and inspect 3D
models, but it does not yet provide scaling, alignment between surveys, or
ecological measurements. Until those tools are added, an OpenReef model should
be treated as a visual and quality-control product rather than a fully
measurement-ready monitoring product.

## Quick start

1. Double-click **OpenReef.app** or **OpenReef.command**.
2. Choose or create a dataset folder for one survey or colony.
3. Use **Input images** to add photographs or extract frames from video.
4. Use **Render images** to work from the sparse cloud through to a textured
   mesh or optional Gaussian splat, checking results in **3D viewer**.

If OpenReef has not been installed on the computer, see **Python setup and
launch** in the Advanced notes at the bottom of this page.

## The workflow in plain language

```text
Input images → Render images [Sparse → Crop → Dense → Texture → Splat] → 3D viewer
```

A typical project moves from left to right. Render images detects work already
on disk, marks those steps **Complete**, and checks the remaining steps. Check a
completed step again whenever you want to recompute it. Each main box and each
step shows when it is Pending, Queued, Running, Complete, or needs attention.
You can keep using the 3D Viewer while processing runs.

### Input images

Choose the main folder for one survey, colony, or model. OpenReef calls this the
**dataset folder**.

You can start with:

- a folder of photographs; or
- a video, from which OpenReef can extract a frame at a chosen time interval.

The original photographs or video frames are kept in `original/`. The images
used for reconstruction are placed in `images/`.

Color correction is optional. If it is enabled, OpenReef creates corrected
copies in `images/` and leaves the originals unchanged. The correction is
deliberately mild because strong or inconsistent editing can make photographs
harder to match. For a first reconstruction, it is reasonable to try the
uncorrected images first.

### Render images: Sparse cloud

The sparse stage works out which photographs overlap and where the camera was
for each photograph. It produces a relatively small set of recognizable 3D
points and a set of camera positions.

Run the four stages in order:

1. **Feature extraction** finds recognizable details in each photograph.
2. **Sequential matching** finds the same details in nearby photographs.
3. **Sparse reconstruction** estimates camera positions and creates the first
   rough point cloud.
4. **Undistort / PINHOLE** prepares the registered photographs for later stages.

Use **Sparse points + cameras** in the 3D Viewer to check the result before
starting the slower dense processing. A good result should broadly resemble the
survey area, and most of the useful photographs should appear as registered
cameras.

COLMAP may create several numbered sparse models. This happens when it can join
some groups of photographs internally but cannot confidently connect those
groups to one another. OpenReef lists every model and recommends the one with
the most registered photographs. The models are kept separate because guessing
how disconnected groups fit together could produce misleading geometry.

If only a small fraction of the photographs appears in the best model, inspect
the image overlap, blur, exposure changes, moving objects, and camera settings
before committing time to Dense Cloud.

### Render images: Dense cloud and surface mesh

The sparse cloud contains only enough points to solve the camera positions. The
**dense cloud** estimates many more points across the visible reef surface. It
is slower and uses substantially more memory, but it contains the detail needed
for a useful model.

The global output row can produce four sizes through the later workflow:

| Level | Default amount | Suggested use |
| --- | ---: | --- |
| Original | 100% | Full output and long-term archive |
| Medium | 20% | Routine viewing and sharing |
| Low | 5% | Quick checking on slower computers |
| Compact | Adaptive | A textured sharing copy kept below 100 MB |

The percentages can be changed. They describe how many points are retained from
the completed dense cloud; they are not separate reconstructions.

The optional **Surface mesh** stage joins the dense points into triangles. A
mesh gives the reef a continuous surface and is required before photographs can
be projected onto it as a texture.

### Render images: Texture mesh

A textured mesh combines the surface triangles with color and detail from the
registered photographs. This is normally the most natural-looking model for
presentation, interpretation, and web sharing.

Select the Original, Medium, Low, or Compact output globally. The default
texture settings are a sensible starting point. OpenReef saves textured models
as GLB files because one GLB can contain the geometry, material information, and
image textures together.

If you need a smaller textured model, generate and texture the Medium or Low
mesh rather than reducing the complexity of a full textured GLB in the Viewer.
This better preserves the connection between triangles and their source imagery.

### Render images: Gaussian splat

A Gaussian splat is an alternative way of representing the photographed scene.
Instead of a conventional triangle surface, it uses many small, soft 3D marks
that blend together when viewed. Splats can reproduce photographic appearance
well and can be pleasant to navigate, but they are not a replacement for a
surface mesh when surface area, volume, or geometric measurements are needed.

This stage uses the camera solution, sparse points, and prepared photographs
from Sparse Cloud. It does not use the textured mesh, so Dense Cloud and Texture
Mesh do not need to finish first.

Start with **Preview**, even on the 64 GB M2 Max reference computer:

| Preset | Training steps | Image size during training | Maximum splats |
| --- | ---: | --- | ---: |
| Preview | 7,000 | Quarter width and height | 2 million |
| Balanced | 15,000 | Half width and height | 3.5 million |
| High | 30,000 | Full size | 5 million |

Preview answers the important first question: “Does this dataset train
successfully?” Increase quality only after inspecting that result. OpenReef
saves regular checkpoints and can continue from the newest usable checkpoint
after an interrupted run.

Gaussian training requires OpenSplat, which is installed separately. On Apple
Silicon, it should be built with Metal support. In 3D Viewer, choose the result
under **Gaussian splat** in the model menu. OpenReef then switches to its
embedded SuperSplat display, using the saved colour, transparency, shape,
rotation, and view-dependent detail instead of showing ordinary point markers.
Use **Gaussian cleanup** to preview removal of very faint, unusually large,
highly stretched, or out-of-crop splats. A conservative display-only cleanup is
applied when a splat opens to reduce long halo rays. Saving creates a new PLY
under Custom saves and never changes the trained original. Installation details
are in the Advanced notes below.

### 3D viewer

The Viewer can open PLY point clouds, PLY or OBJ meshes, and textured GLB files.
It starts meshes in Wireframe mode so their structure is visible.

Main controls (the same for every model type):

- left-click to select;
- right-drag, Ctrl + left-drag, or Shift + two-finger movement to orbit;
- middle-drag, Shift + right-drag, Ctrl + Shift + left-drag, or ordinary
  two-finger movement to pan;
- pinch or use the mouse wheel to zoom;
- press `F` to fit the complete model into view;
- when a crop tool is active, use left-drag to draw the selection;
- use **Fit to view** to fill the window with the complete model;
- switch between perspective and orthographic views;
- use Top, Bottom, Front, Back, Left, or Right for repeatable viewpoints;
- change between Solid, Wireframe, and Solid + wireframe;
- change point size for point clouds; and
- save screenshots and camera viewpoints.

To make an orthomosaic-style image, first rotate the mesh or point cloud to the
angle you want. Choose **Set current viewing angle**, select 2K, 4K, or 8K, then
choose **Export orthomosaic PNG**. OpenReef fits the whole model and exports it
with orthographic projection. The optional transparent background makes the
image easier to place in figures. This is currently an unscaled visual image;
it is not yet a georeferenced map or a measurement-ready orthomosaic.

For a textured GLB, select **Solid** or **Solid + wireframe** to see the
photographic texture.

## Cropping and editing

The lasso tool can either retain the circled area or remove it. Edits do not
overwrite the source model unless you deliberately choose the same filename.
Undo and Reset are available before saving.

Cropping earlier can avoid unnecessary later processing:

- **After Sparse Cloud:** keep the useful reconstruction area before Dense
  Cloud. This can save the most processing time.
- **After Dense Cloud:** crop the dense points before creating a surface mesh.
- **After Texture Mesh:** crop the finished GLB for viewing or sharing. This
  reduces the exported model but cannot recover compute already spent.

When cropping a textured GLB, OpenReef retains complete source triangles so the
remaining triangles keep their original photograph mapping. Save the edited
model as GLB. Untextured meshes and point clouds are normally saved as PLY.

The **Mesh complexity** slider creates a lighter viewing copy. For textured
models, return the slider to 100% before saving an edited GLB; use a separately
generated Medium or Low textured mesh when a smaller textured model is needed.

## Where results are saved

The most useful outputs are collected in the dataset's `models/` folder and are
named after the dataset. For a dataset named `natans`, the main files would be:

| File | Meaning |
| --- | --- |
| `natans_sparsecloud.ply` | Early points used to check image registration |
| `natans_densecloud_high.ply` | Complete dense point cloud |
| `natans_densecloud_medium.ply` | Optional 20% dense point cloud |
| `natans_densecloud_low.ply` | Optional 5% dense point cloud |
| `natans_mesh.ply` | Triangle surface mesh |
| `natans_textured_mesh.glb` | Mesh with photographic texture |
| `natans_gaussian.ply` | Gaussian scene produced by OpenSplat |
| `natans_cameras.json` | Registered camera positions |
| `natans_roi.json` | Saved processing crop, when present |

OpenReef also keeps working files in `colmap/`, `openmvs/`, and `gaussian/`.
Most users should work from `models/` and leave those processing folders in
place so an interrupted job can be continued.

The 3D Viewer menu reads this folder and groups the files as Sparse cloud,
Dense cloud, Surface mesh, Texture mesh, and Gaussian splat. High, Medium, Low,
and Compact versions appear underneath each heading. Cropped and manually saved
models appear under **Custom saves**. Choosing the dataset does not
automatically open a Gaussian model; its splat display starts only when you
select that file.

If the input images or color-correction choice changes, earlier reconstruction
results are no longer valid. OpenReef moves them into a dated
`.openreef/history/` folder rather than deleting them.

## Sharing a model on the web

Open a GLB or PLY in 3D Viewer, then use **OpenReef Web** in the right sidebar.
OpenReef creates `openreef-web/` in the dataset folder. Keep the complete folder
together.

- Use the included macOS or Windows launcher to view the model locally.
- Use **Export compact (<100 MB)** when preparing a GLB for GitHub Pages.
- After **Gaussian splat** in Render images, use the narrow **3D tiles** box and
  select the highest-detail textured GLB in `models/`. OpenReef uses Assimp to
  generate a coarse root and spatial detail tiles, packages the web viewer, and
  adds the result to `models/`. Choose **3D tiles → Streaming viewer** in the 3D
  Viewer to open it. It fetches a small coarse model first when one can be made,
  then visible detail as you move closer.
- The export includes a short `GITHUB-PAGES.md` guide.

Assimp must be installed (`brew install assimp` on macOS). OpenReef spatially
divides the GLB and repacks only each tile's used texture islands into a local
atlas no larger than 1024 px; it does not merely wrap the complete GLB in
`tileset.json`.

Microsoft Teams and SharePoint can store the folder, but they do not serve an
HTML file as a website. Download or sync the complete folder and use its local
launcher, or publish it through GitHub Pages to create a shareable web address.

## A sensible first run

1. Create one dataset folder for the survey or colony.
2. Add photographs or select a source video in Input Images.
3. Leave color correction off for the first attempt.
4. Run all four Sparse Cloud stages.
5. Inspect the sparse points and cameras. Confirm that the best numbered model
   includes a useful proportion of the photographs.
6. If needed, crop the sparse model to the biological area of interest.
7. Run Dense Cloud with Original selected. Add Low if you want a quick viewing
   copy.
8. Run Surface Mesh, then Texture Mesh.
9. Inspect the textured GLB in Solid mode and save useful viewpoints or
   screenshots.
10. Try Gaussian Preview as an optional visual product once OpenSplat is set up.

## Current limitations

Version 0.5 does not yet provide:

- automatic mesh repair or hole filling;
- real-world scale from scale bars or targets;
- alignment of repeat surveys;
- ecological measurements or change analysis;
- automatic per-image masks for moving water and survey backgrounds; or
- automatic online/GPU-server processing.

These are planned areas of development. The aim for version 1.0 is to support
scale bars, coded targets, repeat-survey reference markers, colony dimensions,
surface area, volume, structural complexity, and change through time.

## Advanced and technical notes

The remainder of this README is for installation, troubleshooting, automation,
or software development. It is not required for routine use once OpenReef and
its processing tools are installed.

### Software used

- **COLMAP** finds image matches, solves camera positions, and creates the sparse
  reconstruction.
- **OpenMVS** creates dense clouds, triangle meshes, and photographic textures.
- **OpenSplat** optionally trains Gaussian splats.
- **SuperSplat Viewer** displays Gaussian splats with their full rendering data.
- **PySide6** provides the desktop interface.
- **PyVista/VTK** displays point clouds and triangle models; SuperSplat Viewer
  displays Gaussian models.

OpenReef requires Python 3.10 or newer, COLMAP, OpenMVS, and a working OpenGL
environment. Gaussian training is optional and requires OpenSplat.

### Camera and matching settings

Most users should begin with the defaults and change one setting at a time only
when Sparse Cloud performs poorly.

- Keep **Treat all images as one camera** selected when one unchanged camera and
  lens produced the complete survey.
- `SIMPLE_RADIAL` is a stable general starting model. For original GoPro Wide
  imagery with obvious lens distortion, `OPENCV` is worth testing because it can
  describe more complex distortion.
- Use `PINHOLE` only for imagery that has already been corrected to a normal
  straight-line projection. A GoPro Wide image is not automatically fisheye;
  use a fisheye model only for a true fisheye projection.
- **Sequence overlap** controls how many nearby frames are compared. The default
  of 10 is a sensible starting point for video sampled about once per second.
  Increase it if adjacent useful views are separated by more frames, at the cost
  of extra matching time.

### Python setup and launch

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
openreef
```

Open a dataset or model directly:

```bash
openreef /path/to/dataset
openreef /path/to/model.ply
python -m openreef /path/to/dataset
```

### OpenSplat on Apple Silicon

OpenSplat is a separate AGPL-3.0 program. A fast Mac build requires the full
Xcode application and its Metal toolchain, not only Apple's Command Line Tools.

```bash
brew install cmake opencv pytorch libomp assimp
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -downloadComponent MetalToolchain
git clone https://github.com/WebODM/OpenSplat.git ~/OpenSplat
cmake -S ~/OpenSplat -B ~/OpenSplat/build \
  -DCMAKE_PREFIX_PATH="$(brew --prefix pytorch)" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build ~/OpenSplat/build --parallel 12
```

Confirm that Metal is available:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcrun -sdk macosx metal --version
```

Then choose `~/OpenSplat/build/opensplat` in the Gaussian Splat settings inside
Render images. If macOS
blocks a PyTorch library on first launch, allow the named library under
**System Settings → Privacy & Security**. OpenSplat can run on the CPU, but its
documentation reports that CPU processing is about 100 times slower.

The local Mac interface uses OpenSplat because it supports Apple Metal.
CF-3DGS requires NVIDIA/CUDA and is therefore better treated as a possible
future server backend. Splat Labs may be useful later for hosting or publishing
completed splats rather than for running OpenReef's local reconstruction.

### Command-line pipeline

The complete non-GUI workflow can be run from Terminal:

```bash
./scripts/openreef-pipeline.sh /path/to/dataset
```

Existing outputs are skipped, so the same command can continue an interrupted
dataset. Use `Control-C` to stop. Useful examples:

```bash
# Limit conventional reconstruction to 8 cores and 24 GB RAM
./scripts/openreef-pipeline.sh /path/to/dataset --cores 8 --memory-gb 24

# Create Medium and Low outputs as well as Original
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages dense,mesh,texture --dense-medium --dense-low

# Run only Gaussian Preview after Sparse Cloud is complete
./scripts/openreef-pipeline.sh /path/to/dataset \
  --stages gaussian \
  --opensplat-executable ~/OpenSplat/build/opensplat

# Rebuild a stage even if an output already exists
./scripts/openreef-pipeline.sh /path/to/dataset --stages mesh --force
```

Run `./scripts/openreef-pipeline.sh --help` for all options. After an editable
installation, `openreef-pipeline /path/to/dataset` provides the same runner.

### Internal dataset structure

```text
dataset/
├── original/             untouched source photographs or extracted frames
├── images/               photographs currently used for reconstruction
├── models/               clearly named outputs for viewing and sharing
├── openreef-web/         optional browser-viewer export
├── colmap/               COLMAP database, sparse models, and prepared images
├── openmvs/              dense-cloud, mesh, and texture working files
├── gaussian/             OpenSplat input bridge, checkpoints, and final scene
└── .openreef/history/    recoverable archive of invalidated earlier results
```

The files in `models/` are usually links to the main processing outputs rather
than duplicate copies. This avoids consuming storage twice. The older
`images/meshes/` location is retained as a compatibility link when needed.

The selected COLMAP model is stored through `colmap/sparse/selected`. The
numbered sparse model folders are not merged or deleted. OpenSplat receives a
managed COLMAP-style view of the prepared images through `gaussian/input/`.

The RAM setting is a hard ceiling for the active child process. Leave it at
Unlimited unless OpenReef must share the computer with another demanding job;
an insufficient ceiling can cause processing to stop. OpenSplat manages its own
CPU thread use, so its CPU count is shown as automatic.

### File-format notes

- PLY is used for point clouds, untextured meshes, and OpenSplat Gaussian data.
  A Gaussian PLY contains additional properties that a conventional point
  viewer does not fully render.
- OBJ is supported for viewing conventional meshes.
- GLB is used for portable textured meshes because geometry, materials, and
  texture images can be stored in one file.
- Web export embeds external OpenMVS texture images into the GLB when needed.
- Compact web export reduces opaque texture atlases until the GLB is below a
  conservative 95 MiB target. It does not alter the source model.

### Architecture and development

```text
src/openreef/
├── app.py                 application entry point
├── web_export.py          browser-viewer export
├── core/                  model, camera, rendering, and editing logic
├── io/                    model loading, COLMAP reading, color correction
├── pipeline/              stage definitions, tasks, limits, CLI, and runner
└── ui/                    tabs, controls, sparse viewer, and 3D viewport
```

Processing runs in child processes so the interface and Viewer remain
responsive. Commands are constructed as argument lists rather than shell text.
The GUI and command-line runner use the same stage definitions and output
checks.

For development:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

### Roadmap

- **0.5:** Gaussian image masking and spatial cleanup, richer material controls,
  model history, mesh repair, scale metadata, measurements, and annotations.
- **Later:** alignment, batch and timelapse processing, online GPU workers, and
  scientific change analysis.

### Licence

OpenReef is released under the MIT License. The bundled SuperSplat Viewer is
also MIT-licensed and retains its own notice. COLMAP, OpenMVS, OpenSplat, and
other external tools retain their own licences.

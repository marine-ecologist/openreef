# OpenReef version history

OpenReef is in active development. This file records both committed releases and
the development-version increments that existed in the working tree.

## Unreleased

## 0.6.2 — 2026-09-21

- Added metric-gated 3D length and mesh-surface polygon tools with persistent
  annotations, planar and surface area, perimeter, and relief ratio diagnostics.
- Corrected Retina-display mesh picking so measurement clicks land on the
  visible 3D surface rather than an offset location.
- Added MarkerTag IDs, detection counts, reprojection error, scale source, and
  robust across-tag scale dispersion to the Process and Viewer Data panels.
- Reworked Settings into a card grid and the Viewer sidebar into compact,
  collapsible sections with expanded contextual hover help.
- Added a six-level workflow palette, prominent MarkerTag detection status, and
  source-specific image/video preparation controls.
- Made Viewer state follow project changes by clearing the previous scene and
  loading the best available result from the newly selected project.

## 0.6.1 — 2026-09-20

- Added metric-gated floating length and mesh-surface polygon measurements to
  the native 3D viewer, including persistent annotations, planar and clipped
  surface area, perimeter, relief ratio, and clear-all controls.
- Added nested MarkerTag and scale metadata for viewer use, robust cross-tag
  scale dispersion, corner reprojection diagnostics, and a detailed Viewer Data
  panel. No measurement export is included.
- Added inverted AprilTag detection and automatic supported-family fallback,
  including successful metric scaling for legacy `tag16h5` MarkerTags.
- Streamlined Images, Process, MarkerTags, and Settings pages and clarified
  processing checkboxes and unscaled MarkerTag results.

## 0.6.0 — 2026-09-20

- Added automatic non-permanent `tag36h11` MarkerTag detection after sparse
  reconstruction, robust multi-view 3D corner triangulation, and validated metric
  scaling from the default 50 mm encoded-square edge.
- Preserved raw COLMAP reconstruction output while routing undistortion, dense,
  mesh, texture, Gaussian, and 3D Tiles work through a metric sparse-model copy.
- Added MarkerTag audit metadata, explicit unscaled fallback statuses, desktop and
  command-line configuration, and Render workflow scale/residual reporting.
- Reworked the desktop shell around a compact left sidebar for Process, Data,
  Viewer, Projects, MarkerTags, Settings, and help links, removing the horizontal
  workspace tabs and leaving the main workspace wide.
- Introduced a restrained macOS-inspired charcoal appearance with neutral cards,
  borders, controls, and pipeline states, plus a compact MarkerTags summary beside
  the Quick preview panel.

## 0.5.0 — 2026-09-15

- Added local generation of spatial 3D Tiles 1.1 from a textured GLB, using an
  optional compact `REPLACE` root and spatial glTF leaf tiles. Each leaf now
  packs only its used UV islands into a tile-local, maximum 1024 px atlas so a
  large source texture is never downloaded in full for every spatial tile.
- Placed the 3D Tiles build checkpoint after Gaussian splat in Render images,
  using the same narrow action-card layout as the crop checkpoint.
- Added portable 3D Tiles entries to each dataset's `models/` folder and an
  embedded streaming-viewer section to the 3D Viewer model menu.
- Added a streaming Three.js viewer that loads coarse visible tiles first and
  progressively refines detail as the camera moves closer.
- Added Draco and KTX2 tile-content support, streaming progress, detail presets,
  the established OpenReef navigation, screenshots, and full-screen viewing.
- Added generated local-viewing and GitHub Pages instructions, including a check
  for tiles that exceed GitHub's 100 MiB per-file limit.
- Added live tile-build progress and automatic opening of the completed hierarchy
  in the embedded Viewer; Assimp is the only additional system dependency.

## 0.4.0 — development snapshot

- Consolidated the application into Input images, Render images, and 3D viewer.
- Added compact reconstruction outputs and GitHub Pages-oriented GLB compression.
- Added in-viewer web export for GLB and PLY models.
- Added optional OpenSplat training and the embedded SuperSplat viewer.
- Added model cataloguing, textured-GLB cropping, Gaussian cleanup, and visual
  orthomosaic export.

This increment existed in the working tree but was not committed or tagged as a
release before 0.5.0 work began.

## 0.3.0 — not released

No separate 0.3.0 version is present in the repository history. The recorded
development version advanced from the committed 0.2.0 baseline to 0.4.0.

## 0.2.0 — 2026-09-07

- Added the initial OpenReef desktop viewer and reconstruction workflow.
- Added COLMAP sparse reconstruction, camera inspection, processing crop, OpenMVS
  dense cloud and surface-mesh stages, lasso editing, and model export.
- Added the textured-mesh pipeline on 2026-09-10 while retaining version 0.2.0.

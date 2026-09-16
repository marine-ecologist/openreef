# OpenReef version history

OpenReef is in active development. This file records both committed releases and
the development-version increments that existed in the working tree.

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

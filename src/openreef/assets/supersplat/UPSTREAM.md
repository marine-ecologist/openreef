# Bundled SuperSplat Viewer

These runtime files come from `@playcanvas/supersplat-viewer` version 1.28.0:

- https://github.com/playcanvas/supersplat-viewer
- https://www.npmjs.com/package/@playcanvas/supersplat-viewer

The upstream viewer is MIT-licensed; see `LICENSE` in this folder. OpenReef adds
a small desktop-input adaptation in `index.js` so all viewer types share the
same controls: right-drag, Ctrl + left-drag, or Shift + two-finger movement
orbits; middle-drag, Shift + right-drag, Ctrl + Shift + left-drag, or ordinary
two-finger movement pans; and pinch or the mouse wheel zooms. Plain left-click
is reserved for selection, and an active OpenReef lasso intercepts left-drag.

When updating the bundled viewer, reapply and test that navigation adaptation.

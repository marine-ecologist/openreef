"""Pipeline stage definitions, filesystem contract, and command construction."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import struct
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class StageKey(str, Enum):
    FEATURES = "features"
    MATCHING = "matching"
    SPARSE = "sparse"
    UNDISTORT = "undistort"
    OPENMVS_IMPORT = "openmvs_import"
    DENSE = "dense"
    MESH = "mesh"


GENERATE_STAGES = (
    StageKey.FEATURES,
    StageKey.MATCHING,
    StageKey.SPARSE,
    StageKey.UNDISTORT,
)
DENSE_STAGES = (StageKey.OPENMVS_IMPORT, StageKey.DENSE, StageKey.MESH)
ALL_STAGES = (*GENERATE_STAGES, *DENSE_STAGES)

STAGE_LABELS = {
    StageKey.FEATURES: "Feature extraction",
    StageKey.MATCHING: "Sequential matching",
    StageKey.SPARSE: "Sparse reconstruction",
    StageKey.UNDISTORT: "Undistort / PINHOLE",
    StageKey.OPENMVS_IMPORT: "OpenMVS import",
    StageKey.DENSE: "Dense point cloud",
    StageKey.MESH: "Surface mesh",
}

STAGE_OUTPUTS = {
    StageKey.FEATURES: "colmap/database.db",
    StageKey.MATCHING: "matched image pairs",
    StageKey.SPARSE: "colmap/sparse/0",
    StageKey.UNDISTORT: "colmap/dense",
    StageKey.OPENMVS_IMPORT: "openmvs/scene.mvs",
    StageKey.DENSE: "Selected Original / Medium / Low clouds",
    StageKey.MESH: "Matching meshes for selected dense-cloud levels",
}

IMAGE_EXTENSIONS = {
    ".bmp",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
MESH_EXTENSIONS = frozenset({".glb", ".obj", ".ply", ".stl", ".vtp"})


class StageConfigurationError(RuntimeError):
    """A selected stage is missing an input or executable."""


@dataclass(frozen=True)
class PipelineOptions:
    cores: int
    memory_gb: float = 0.0
    use_gpu: bool = True
    camera_model: str = "SIMPLE_RADIAL"
    single_camera: bool = True
    max_image_size: int = 3200
    sequential_overlap: int = 10
    resolution_level: int = 1
    max_resolution: int = 2560
    number_views: int = 5
    number_views_fuse: int = 3
    estimate_colors: bool = True
    estimate_normals: bool = True
    dense_original: bool = True
    dense_low: bool = False
    dense_medium: bool = False
    dense_original_percent: int = 100
    dense_medium_percent: int = 20
    dense_low_percent: int = 5


@dataclass(frozen=True)
class StageCommand:
    program: str
    arguments: tuple[str, ...]
    working_directory: Path

    @property
    def display(self) -> str:
        import shlex

        return shlex.join((self.program, *self.arguments))


@dataclass(frozen=True)
class DatasetLayout:
    root: Path

    @classmethod
    def from_path(cls, value: str | Path) -> DatasetLayout:
        return cls(Path(value).expanduser().resolve())

    @property
    def images(self) -> Path:
        return self.root / "images"

    @property
    def original(self) -> Path:
        return self.root / "original"

    @property
    def meshes(self) -> Path:
        """Compatibility alias for the v0.2 root-level models folder."""
        return self.models

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def legacy_meshes(self) -> Path:
        return self.images / "meshes"

    @property
    def colmap(self) -> Path:
        return self.root / "colmap"

    @property
    def database(self) -> Path:
        return self.colmap / "database.db"

    @property
    def sparse(self) -> Path:
        return self.colmap / "sparse"

    @property
    def selected_sparse(self) -> Path:
        return self.sparse / "selected"

    @property
    def dense(self) -> Path:
        return self.colmap / "dense"

    @property
    def undistort_selection_state(self) -> Path:
        return self.dense / ".openreef_sparse_model.json"

    @property
    def openmvs(self) -> Path:
        return self.root / "openmvs"

    @property
    def scene(self) -> Path:
        return self.openmvs / "scene.mvs"

    @property
    def dense_scene(self) -> Path:
        return self.openmvs / "scene_dense.mvs"

    @property
    def dense_cloud(self) -> Path:
        return self.openmvs / "scene_dense.ply"

    @property
    def dense_cloud_low(self) -> Path:
        return self.openmvs / "scene_dense_low.ply"

    @property
    def dense_cloud_medium(self) -> Path:
        return self.openmvs / "scene_dense_medium.ply"

    @property
    def dense_cloud_original(self) -> Path:
        return self.openmvs / "scene_dense_original.ply"

    @property
    def dense_levels_state(self) -> Path:
        return self.openmvs / "scene_dense_levels.json"

    @property
    def surface_scene(self) -> Path:
        return self.openmvs / "scene_mesh.mvs"

    @property
    def surface_mesh(self) -> Path:
        return self.openmvs / "scene_mesh.ply"

    @property
    def sparse_cloud(self) -> Path | None:
        model = self.sparse_model()
        return model / "points3D.ply" if model else None

    @property
    def roi(self) -> Path:
        return self.models / f"{dataset_label(self)}_roi.json"

    @property
    def imported_roi_state(self) -> Path:
        return self.openmvs / "scene_roi.json"

    def prepare_directories(self) -> None:
        self.sparse.mkdir(parents=True, exist_ok=True)
        self.dense.mkdir(parents=True, exist_ok=True)
        self.openmvs.mkdir(parents=True, exist_ok=True)
        self.models.mkdir(parents=True, exist_ok=True)

    def image_count(self) -> int:
        if not self.images.is_dir():
            return 0
        return sum(
            1
            for path in self.images.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )

    def sparse_models(self) -> tuple[Path, ...]:
        if not self.sparse.is_dir():
            return ()
        try:
            candidates = sorted(
                (
                    path
                    for path in self.sparse.iterdir()
                    if path.is_dir() and path.name != self.selected_sparse.name
                ),
                key=lambda path: (
                    not path.name.isdigit(),
                    int(path.name) if path.name.isdigit() else path.name,
                ),
            )
        except OSError:
            return ()
        return tuple(
            candidate
            for candidate in candidates
            if all(
                (candidate / name).is_file()
                for name in ("cameras.bin", "images.bin", "points3D.bin")
            )
        )

    def sparse_model(self) -> Path | None:
        candidates = self.sparse_models()
        if not candidates:
            return None
        if self.selected_sparse.is_symlink():
            try:
                selected = self.selected_sparse.resolve(strict=True)
            except OSError:
                selected = None
            if selected in (candidate.resolve() for candidate in candidates):
                return selected
        return max(candidates, key=sparse_model_score)

    def select_sparse_model(self, model: Path) -> None:
        selected = model.resolve()
        candidates = {candidate.resolve() for candidate in self.sparse_models()}
        if selected not in candidates:
            raise ValueError(f"Not a complete sparse model folder: {model}")
        link = self.selected_sparse
        if link.exists() and not link.is_symlink():
            raise OSError(f"Cannot replace non-link sparse selection: {link}")
        link.unlink(missing_ok=True)
        link.symlink_to(selected.name, target_is_directory=True)


def sparse_model_counts(model: Path) -> tuple[int, int]:
    """Return registered-image and sparse-point counts from a COLMAP model folder."""
    return (
        _colmap_binary_count(model / "images.bin"),
        _colmap_binary_count(model / "points3D.bin"),
    )


def sparse_model_score(model: Path) -> tuple[int, int]:
    """Prefer the connected model registering the most images, then the most points."""
    return sparse_model_counts(model)


def sparse_model_identity(model: Path) -> dict[str, object]:
    files: dict[str, dict[str, int]] = {}
    for name in ("cameras.bin", "images.bin", "points3D.bin"):
        stat = (model / name).stat()
        files[name] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return {"folder": model.name, "files": files}


def _colmap_binary_count(path: Path) -> int:
    try:
        with path.open("rb") as stream:
            value = stream.read(8)
        return int(struct.unpack("<Q", value)[0]) if len(value) == 8 else 0
    except (OSError, struct.error):
        return 0


def main_model_outputs(layout: DatasetLayout) -> dict[str, Path]:
    """Find top-level reconstruction artifacts worth exposing to the user."""
    outputs: dict[str, Path] = {}
    label = dataset_label(layout)
    if layout.openmvs.is_dir():
        for path in sorted(layout.openmvs.iterdir()):
            if (
                path.is_file()
                and path.suffix.lower() in MESH_EXTENSIONS
                and path.stem.startswith("scene")
            ):
                freshness_source = {
                    "scene_dense_original.ply": layout.dense_cloud,
                    "scene_dense_medium.ply": layout.dense_cloud,
                    "scene_dense_low.ply": layout.dense_cloud,
                    "scene_mesh.ply": layout.dense_cloud,
                    "scene_mesh_medium.ply": layout.dense_cloud_medium,
                    "scene_mesh_low.ply": layout.dense_cloud_low,
                }.get(path.name)
                if (
                    freshness_source
                    and freshness_source.is_file()
                    and not _newer_than(path, freshness_source)
                ):
                    continue
                if path.name == "scene_dense.ply":
                    outputs[f"{label}_densecloud.ply"] = path
                    name = f"{label}_densecloud_high.ply"
                elif path.name == "scene_dense_original.ply":
                    name = f"{label}_densecloud_original.ply"
                elif path.name == "scene_dense_low.ply":
                    name = f"{label}_densecloud_low.ply"
                elif path.name == "scene_dense_medium.ply":
                    name = f"{label}_densecloud_medium.ply"
                elif path.name == "scene_mesh.ply":
                    outputs[f"{label}_mesh_original.ply"] = path
                    name = f"{label}_mesh.ply"
                elif "texture" in path.stem:
                    name = f"{label}_textured_mesh{path.suffix.lower()}"
                else:
                    name = f"{label}_{path.name.removeprefix('scene_')}"
                outputs[name] = path
    colmap_fused = layout.dense / "fused.ply"
    if colmap_fused.is_file():
        outputs[f"{label}_sparsecloud.ply"] = colmap_fused
    else:
        sparse_model = layout.sparse_model()
        sparse_cloud = sparse_model / "points3D.ply" if sparse_model else None
        if sparse_cloud and sparse_cloud.is_file():
            outputs[f"{label}_sparsecloud.ply"] = sparse_cloud
    return outputs


def dataset_label(layout: DatasetLayout) -> str:
    """Return a filesystem-friendly name based on the main dataset folder."""
    label = "_".join(layout.root.name.strip().split())
    return label or "openreef"


def _managed_model_link(path: Path, layout: DatasetLayout) -> bool:
    if not path.is_symlink():
        return False
    target = (path.parent / os.readlink(path)).resolve()
    return (
        target.is_relative_to(layout.openmvs)
        or target.is_relative_to(layout.dense)
        or target.is_relative_to(layout.sparse)
    )


def _migrate_legacy_models(layout: DatasetLayout) -> None:
    """Move v0.1 images/meshes content to models/ and leave a compatibility link."""
    legacy = layout.legacy_meshes
    layout.models.mkdir(parents=True, exist_ok=True)
    if legacy.is_symlink():
        try:
            if legacy.resolve() == layout.models.resolve():
                return
        except OSError:
            pass
        legacy.unlink()
    elif legacy.is_dir():
        for source in legacy.iterdir():
            destination = layout.models / source.name
            if destination.exists() or destination.is_symlink():
                if source.is_symlink() and destination.resolve() == source.resolve():
                    source.unlink()
                else:
                    continue
            elif source.is_symlink():
                target = source.resolve()
                source.unlink()
                destination.symlink_to(Path(os.path.relpath(target, destination.parent)))
            else:
                source.rename(destination)
        try:
            legacy.rmdir()
        except OSError:
            return
    if layout.images.is_dir() and not legacy.exists():
        legacy.symlink_to(Path("..") / "models", target_is_directory=True)


def sync_model_links(layout: DatasetLayout) -> tuple[Path, ...]:
    """Maintain friendly links in models/ to reconstruction outputs."""
    _migrate_legacy_models(layout)
    outputs = main_model_outputs(layout)
    legacy_pointcloud = layout.models / f"{dataset_label(layout)}_pointcloud.ply"
    if legacy_pointcloud.is_symlink() and not legacy_pointcloud.exists():
        legacy_pointcloud.unlink()

    sparse_model = layout.sparse_model()
    images_binary = sparse_model / "images.bin" if sparse_model else None
    if images_binary and images_binary.is_file():
        try:
            from openreef.io.colmap_model import read_camera_poses, save_camera_manifest

            poses = read_camera_poses(images_binary)
            camera_manifest = layout.models / f"{dataset_label(layout)}_cameras.json"
            save_camera_manifest(poses, camera_manifest)
        except (OSError, ValueError):
            pass

    for path in layout.models.iterdir():
        if _managed_model_link(path, layout) and path.name not in outputs:
            path.unlink()

    links: list[Path] = []
    for name, source in outputs.items():
        destination = layout.models / name
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() and not destination.exists():
                destination.unlink()
            elif not _managed_model_link(destination, layout):
                continue
            elif destination.resolve() == source.resolve():
                links.append(destination)
                continue
            else:
                destination.unlink()
        relative_source = Path(os.path.relpath(source, destination.parent))
        destination.symlink_to(relative_source)
        links.append(destination)
    return tuple(links)


def sync_mesh_links(layout: DatasetLayout) -> tuple[Path, ...]:
    """Backward-compatible name for integrations written against OpenReef 0.1."""
    return sync_model_links(layout)


def selected_dense_levels(
    layout: DatasetLayout,
    options: PipelineOptions,
) -> tuple[tuple[str, int, Path], ...]:
    """Return selected level name, retained point percentage, and PLY path."""
    candidates = (
        (
            "original",
            options.dense_original,
            options.dense_original_percent,
            layout.dense_cloud
            if options.dense_original_percent == 100
            else layout.dense_cloud_original,
        ),
        ("medium", options.dense_medium, options.dense_medium_percent, layout.dense_cloud_medium),
        ("low", options.dense_low, options.dense_low_percent, layout.dense_cloud_low),
    )
    return tuple(
        (level, percent, output)
        for level, selected, percent, output in candidates
        if selected
    )


def mesh_output_for_level(layout: DatasetLayout, level: str) -> Path:
    if level == "original":
        return layout.surface_mesh
    return layout.openmvs / f"scene_mesh_{level}.ply"


def validate_dense_levels(levels: tuple[tuple[str, int, Path], ...]) -> None:
    if not levels:
        raise StageConfigurationError("Select at least one dense-cloud output level.")
    invalid = [f"{name}={percent}%" for name, percent, _ in levels if not 1 <= percent <= 100]
    if invalid:
        raise StageConfigurationError(
            "Dense-cloud percentages must be between 1 and 100: " + ", ".join(invalid)
        )


def _dense_level_matches(
    layout: DatasetLayout,
    level: str,
    percent: int,
    output: Path,
) -> bool:
    if level == "original" and percent == 100 and output == layout.dense_cloud:
        return output.is_file()
    if not output.is_file() or not _newer_than(output, layout.dense_cloud):
        return False
    try:
        state = json.loads(layout.dense_levels_state.read_text(encoding="utf-8"))
        source_mtime = layout.dense_cloud.stat().st_mtime_ns
    except (OSError, ValueError):
        return False
    return state.get("source_mtime_ns") == source_mtime and state.get("levels", {}).get(
        level
    ) == percent


def stage_output_exists(
    stage: StageKey,
    layout: DatasetLayout,
    options: PipelineOptions | None = None,
) -> bool:
    if stage == StageKey.FEATURES:
        return _database_table_has_rows(layout.database, "keypoints")
    if stage == StageKey.MATCHING:
        return _database_table_has_rows(layout.database, "two_view_geometries")
    if stage == StageKey.SPARSE:
        return layout.sparse_model() is not None
    if stage == StageKey.UNDISTORT:
        sparse = layout.dense / "sparse"
        outputs_exist = (layout.dense / "images").is_dir() and all(
            (sparse / name).is_file() for name in ("cameras.bin", "images.bin", "points3D.bin")
        )
        if not outputs_exist:
            return False
        model = layout.sparse_model()
        if model is None:
            return False
        if not layout.undistort_selection_state.is_file():
            return len(layout.sparse_models()) == 1
        try:
            state = json.loads(layout.undistort_selection_state.read_text(encoding="utf-8"))
            return state == sparse_model_identity(model)
        except (OSError, ValueError):
            return False
    if stage == StageKey.OPENMVS_IMPORT:
        marker = (
            layout.undistort_selection_state
            if layout.undistort_selection_state.is_file()
            else layout.dense / "sparse" / "images.bin"
        )
        return (
            stage_output_exists(StageKey.UNDISTORT, layout)
            and layout.scene.is_file()
            and _newer_than(layout.scene, marker)
            and _roi_state_matches(layout)
        )
    if stage == StageKey.DENSE:
        complete = (
            stage_output_exists(StageKey.OPENMVS_IMPORT, layout)
            and layout.scene.is_file()
            and layout.dense_scene.is_file()
            and layout.dense_cloud.is_file()
            and _newer_than(layout.dense_scene, layout.scene)
        )
        if options:
            for level, percent, output in selected_dense_levels(layout, options):
                complete = complete and _dense_level_matches(
                    layout, level, percent, output
                )
        return complete
    if stage == StageKey.MESH:
        complete = (
            _roi_state_matches(layout)
            and layout.dense_scene.is_file()
        )
        if options:
            for level, _, dense_output in selected_dense_levels(layout, options):
                mesh_output = mesh_output_for_level(layout, level)
                complete = complete and mesh_output.is_file() and _newer_than(
                    mesh_output, dense_output
                )
            return complete
        return complete and layout.surface_mesh.is_file() and _newer_than(
            layout.surface_mesh, layout.dense_scene
        )
    return False


def validate_stage(
    stage: StageKey,
    layout: DatasetLayout,
    options: PipelineOptions | None = None,
) -> None:
    if not layout.root.is_dir():
        raise StageConfigurationError(f"Dataset folder does not exist: {layout.root}")
    if stage == StageKey.FEATURES:
        if not layout.images.is_dir():
            raise StageConfigurationError(f"Missing image folder: {layout.images}")
        if layout.image_count() == 0:
            raise StageConfigurationError(f"No supported images found in: {layout.images}")
    elif stage in (StageKey.MATCHING, StageKey.SPARSE):
        if not layout.database.is_file():
            raise StageConfigurationError("Run feature extraction first; database.db is missing.")
    elif stage == StageKey.UNDISTORT:
        if layout.sparse_model() is None:
            raise StageConfigurationError(
                "Run sparse reconstruction first; no sparse model was found."
            )
    elif stage == StageKey.OPENMVS_IMPORT:
        sparse = layout.dense / "sparse"
        required = ("cameras.bin", "images.bin", "points3D.bin")
        if not stage_output_exists(StageKey.UNDISTORT, layout) or not all(
            (sparse / name).is_file() for name in required
        ):
            raise StageConfigurationError(
                "Run image undistortion first; COLMAP dense input is incomplete."
            )
    elif stage == StageKey.DENSE:
        if not layout.scene.is_file():
            raise StageConfigurationError("Run OpenMVS import first; scene.mvs is missing.")
        if not _roi_state_matches(layout):
            raise StageConfigurationError(
                "The processing ROI changed; rerun OpenMVS import before densifying."
            )
    elif stage == StageKey.MESH:
        if not layout.dense_scene.is_file():
            raise StageConfigurationError(
                "Generate the dense point cloud first; scene_dense.mvs is missing."
            )
        if not stage_output_exists(StageKey.DENSE, layout):
            raise StageConfigurationError(
                "The dense cloud predates the current scene or ROI; rerun Dense point cloud."
            )
        if options:
            levels = selected_dense_levels(layout, options)
            validate_dense_levels(levels)
            invalid = [
                path.name
                for level, percent, path in levels
                if not _dense_level_matches(layout, level, percent, path)
            ]
            if invalid:
                raise StageConfigurationError(
                    "Generate the selected dense cloud level(s) first: " + ", ".join(invalid)
                )


def build_stage_command(
    stage: StageKey,
    layout: DatasetLayout,
    options: PipelineOptions,
) -> StageCommand:
    validate_stage(stage, layout, options)
    layout.prepare_directories()

    if stage == StageKey.FEATURES:
        return _colmap(
            layout,
            "feature_extractor",
            "--database_path",
            str(layout.database),
            "--image_path",
            str(layout.images),
            "--ImageReader.camera_model",
            options.camera_model,
            "--ImageReader.single_camera",
            _flag(options.single_camera),
            "--FeatureExtraction.num_threads",
            str(options.cores),
            "--FeatureExtraction.max_image_size",
            str(options.max_image_size),
            "--FeatureExtraction.use_gpu",
            _flag(options.use_gpu),
        )
    if stage == StageKey.MATCHING:
        return _colmap(
            layout,
            "sequential_matcher",
            "--database_path",
            str(layout.database),
            "--FeatureMatching.num_threads",
            str(options.cores),
            "--FeatureMatching.use_gpu",
            _flag(options.use_gpu),
            "--SequentialMatching.overlap",
            str(options.sequential_overlap),
        )
    if stage == StageKey.SPARSE:
        return StageCommand(
            sys.executable,
            (
                "-m",
                "openreef.pipeline.tasks",
                "sparse-colmap",
                "--executable",
                resolve_executable("colmap"),
                "--database",
                str(layout.database),
                "--images",
                str(layout.images),
                "--output",
                str(layout.sparse),
                "--cores",
                str(options.cores),
            ),
            layout.root,
        )
    if stage == StageKey.UNDISTORT:
        sparse_model = layout.sparse_model()
        assert sparse_model is not None
        return StageCommand(
            sys.executable,
            (
                "-m",
                "openreef.pipeline.tasks",
                "undistort-colmap",
                "--executable",
                resolve_executable("colmap"),
                "--images",
                str(layout.images),
                "--input",
                str(sparse_model),
                "--output",
                str(layout.dense),
                "--max-image-size",
                str(options.max_image_size),
                "--state",
                str(layout.undistort_selection_state),
            ),
            layout.root,
        )
    if stage == StageKey.OPENMVS_IMPORT:
        executable = resolve_executable("InterfaceCOLMAP")
        sparse_model = layout.sparse_model()
        assert sparse_model is not None
        return StageCommand(
            sys.executable,
            (
                "-m",
                "openreef.pipeline.tasks",
                "import-openmvs",
                "--executable",
                executable,
                "--dense-folder",
                str(layout.dense),
                "--openmvs-folder",
                str(layout.openmvs),
                "--cores",
                str(options.cores),
                "--colmap-executable",
                resolve_executable("colmap"),
                "--roi",
                str(layout.roi),
                "--sparse-model",
                sparse_model.name,
            ),
            layout.openmvs,
        )
    if stage == StageKey.DENSE:
        levels = selected_dense_levels(layout, options)
        validate_dense_levels(levels)
        return StageCommand(
            sys.executable,
            (
                "-m",
                "openreef.pipeline.tasks",
                "dense-multi",
                "--executable",
                resolve_executable("DensifyPointCloud"),
                "--openmvs-folder",
                str(layout.openmvs),
                "--cores",
                str(options.cores),
                "--resolution-level",
                str(options.resolution_level),
                "--max-resolution",
                str(options.max_resolution),
                "--number-views",
                str(options.number_views),
                "--number-views-fuse",
                str(options.number_views_fuse),
                "--estimate-colors",
                "2" if options.estimate_colors else "0",
                "--estimate-normals",
                "2" if options.estimate_normals else "0",
                "--levels",
                ",".join(level for level, _, _ in levels),
                "--original-percent",
                str(options.dense_original_percent),
                "--medium-percent",
                str(options.dense_medium_percent),
                "--low-percent",
                str(options.dense_low_percent),
            ),
            layout.openmvs,
        )
    if stage == StageKey.MESH:
        return StageCommand(
            sys.executable,
            (
                "-m",
                "openreef.pipeline.tasks",
                "mesh-multi",
                "--executable",
                resolve_executable("ReconstructMesh"),
                "--openmvs-folder",
                str(layout.openmvs),
                "--levels",
                ",".join(level for level, _, _ in selected_dense_levels(layout, options)),
                "--original-percent",
                str(options.dense_original_percent),
                "--medium-percent",
                str(options.dense_medium_percent),
                "--low-percent",
                str(options.dense_low_percent),
                "--cores",
                str(options.cores),
            ),
            layout.openmvs,
        )
    raise StageConfigurationError(f"Unknown stage: {stage}")


def resolve_executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    fallback = Path.home() / "vcpkg" / "installed" / "arm64-osx" / "tools" / "openmvs" / name
    if fallback.is_file():
        return str(fallback)
    raise StageConfigurationError(f"Required command is not installed or not on PATH: {name}")


def _colmap(layout: DatasetLayout, *arguments: str) -> StageCommand:
    return StageCommand(resolve_executable("colmap"), tuple(arguments), layout.root)


def _flag(value: bool) -> str:
    return "1" if value else "0"


def _database_table_has_rows(database: Path, table: str) -> bool:
    if not database.is_file():
        return False
    try:
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            result = connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
    except sqlite3.Error:
        return False
    return result is not None


def _newer_than(output: Path, source: Path) -> bool:
    try:
        return output.stat().st_mtime_ns >= source.stat().st_mtime_ns
    except OSError:
        return False


def _roi_state_matches(layout: DatasetLayout) -> bool:
    if not layout.imported_roi_state.is_file():
        return not layout.roi.is_file()
    try:
        state = json.loads(layout.imported_roi_state.read_text(encoding="utf-8"))
        desired = (
            json.loads(layout.roi.read_text(encoding="utf-8")) if layout.roi.is_file() else None
        )
    except (OSError, ValueError):
        return False
    return state.get("roi") == desired

"""Small filesystem preparation tasks that execute inside the pipeline process."""

from __future__ import annotations

import argparse
import json
import mmap
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from openreef.io.colmap_model import SparseROI, filter_text_model_to_roi
from openreef.pipeline.stages import sparse_model_identity, sparse_model_score


def sparse_colmap(args: argparse.Namespace) -> int:
    """Run COLMAP mapping, then export its sparse points as a PLY artifact."""
    command = [
        args.executable,
        "mapper",
        "--database_path",
        args.database,
        "--image_path",
        args.images,
        "--output_path",
        args.output,
        "--Mapper.num_threads",
        str(args.cores),
    ]
    print("Starting COLMAP sparse reconstruction", flush=True)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        return result.returncode

    output = Path(args.output)
    required = ("cameras.bin", "images.bin", "points3D.bin")
    models = sorted(
        (
            path
            for path in output.iterdir()
            if path.is_dir()
            and path.name != "selected"
            and all((path / name).is_file() for name in required)
        ),
        key=lambda path: (
            not path.name.isdigit(),
            int(path.name) if path.name.isdigit() else path.name,
        ),
    )
    if not models:
        print("COLMAP finished without a complete sparse model", flush=True)
        return 1

    print(f"COLMAP produced {len(models)} disconnected sparse model(s)", flush=True)
    for model in models:
        point_cloud = model / "points3D.ply"
        print(f"Exporting sparse model {model.name} to {point_cloud.name}", flush=True)
        conversion = subprocess.run(
            [
                args.executable,
                "model_converter",
                "--input_path",
                str(model),
                "--output_path",
                str(point_cloud),
                "--output_type",
                "PLY",
            ],
            check=False,
        )
        if conversion.returncode != 0:
            return conversion.returncode

    selected_model = max(models, key=sparse_model_score)
    selected_link = output / "selected"
    if selected_link.exists() and not selected_link.is_symlink():
        print(f"Cannot update sparse selection because {selected_link} is not a link", flush=True)
        return 1
    selected_link.unlink(missing_ok=True)
    selected_link.symlink_to(selected_model.name, target_is_directory=True)
    images, points = sparse_model_score(selected_model)
    print(
        f"Selected sparse model {selected_model.name}: "
        f"{images:,} registered images, {points:,} points",
        flush=True,
    )
    return 0


def undistort_colmap(args: argparse.Namespace) -> int:
    """Undistort the selected sparse-model folder and record its identity."""
    command = [
        args.executable,
        "image_undistorter",
        "--image_path",
        args.images,
        "--input_path",
        args.input,
        "--output_path",
        args.output,
        "--output_type",
        "COLMAP",
        "--max_image_size",
        str(args.max_image_size),
    ]
    print(f"Undistorting selected sparse model folder: {args.input}", flush=True)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        return result.returncode
    state = Path(args.state)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps(sparse_model_identity(Path(args.input)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def import_openmvs(args: argparse.Namespace) -> int:
    dense = Path(args.dense_folder)
    openmvs = Path(args.openmvs_folder)
    source_images = dense / "images"
    destination_images = openmvs / "images"
    destination_images.mkdir(parents=True, exist_ok=True)

    files = [path for path in source_images.rglob("*") if path.is_file()]
    print(f"Preparing OpenMVS image workspace ({len(files):,} files)", flush=True)
    for index, source in enumerate(files, start=1):
        relative = source.relative_to(source_images)
        destination = destination_images / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if (
            not destination.exists()
            or source.stat().st_size != destination.stat().st_size
            or source.stat().st_mtime_ns > destination.stat().st_mtime_ns
        ):
            shutil.copy2(source, destination)
        if index == 1 or index % 25 == 0 or index == len(files):
            print(f"Copied/checked images: {index:,}/{len(files):,}", flush=True)

    input_model = dense
    roi_path = Path(args.roi)
    roi_payload: dict[str, object] | None = None
    if roi_path.is_file():
        roi = SparseROI.load(roi_path)
        if roi.sparse_model and roi.sparse_model != args.sparse_model:
            print(
                f"Ignoring ROI for sparse model {roi.sparse_model}; "
                f"model {args.sparse_model} is selected",
                flush=True,
            )
        else:
            raw_model = openmvs / "colmap_txt"
            roi_model = openmvs / "colmap_roi"
            shutil.rmtree(raw_model, ignore_errors=True)
            shutil.rmtree(roi_model, ignore_errors=True)
            raw_model.mkdir(parents=True)
            conversion = subprocess.run(
                [
                    args.colmap_executable,
                    "model_converter",
                    "--input_path",
                    str(dense / "sparse"),
                    "--output_path",
                    str(raw_model),
                    "--output_type",
                    "TXT",
                ],
                check=False,
            )
            if conversion.returncode != 0:
                return conversion.returncode
            retained = filter_text_model_to_roi(raw_model, roi_model, roi)
            if retained == 0:
                print("The processing ROI retained no COLMAP points", flush=True)
                return 1
            print(f"Applying processing ROI ({retained:,} sparse points retained)", flush=True)
            input_model = roi_model
            roi_payload = json.loads(roi_path.read_text(encoding="utf-8"))

    command = [
        args.executable,
        "-i",
        str(input_model),
        "-o",
        "scene.mvs",
        "--image-folder",
        "images",
        "--max-threads",
        str(args.cores),
    ]
    print("Starting InterfaceCOLMAP", flush=True)
    result = subprocess.run(command, cwd=openmvs, check=False)
    if result.returncode == 0:
        (openmvs / "scene_roi.json").write_text(
            json.dumps({"roi": roi_payload}, indent=2) + "\n", encoding="utf-8"
        )
    return result.returncode


def dense_multi(args: argparse.Namespace) -> int:
    """Generate the canonical High cloud and optional lighter viewing copies."""
    openmvs = Path(args.openmvs_folder)
    requested = {item.strip() for item in args.levels.split(",") if item.strip()}
    if not requested:
        print("Select at least one dense-cloud output level", flush=True)
        return 2

    command = [
        args.executable,
        "scene.mvs",
        "-o",
        "scene_dense.mvs",
        "--max-threads",
        str(args.cores),
        "--resolution-level",
        str(args.resolution_level),
        "--max-resolution",
        str(args.max_resolution),
        "--number-views",
        str(args.number_views),
        "--number-views-fuse",
        str(args.number_views_fuse),
        "--estimate-colors",
        str(args.estimate_colors),
        "--estimate-normals",
        str(args.estimate_normals),
        "--estimate-roi",
        "2",
        "--crop-to-roi",
        "1",
        "--remove-dmaps",
        "1",
    ]
    print(
        "[1/1] Generating High dense cloud "
        f"(resolution level {args.resolution_level}, max {args.max_resolution}px)",
        flush=True,
    )
    result = subprocess.run(command, cwd=openmvs, check=False)
    if result.returncode != 0:
        return result.returncode

    source = openmvs / "scene_dense.ply"
    if not source.is_file():
        print(f"Dense reconstruction finished without {source.name}", flush=True)
        return 1
    previews = {
        "original": (
            openmvs / "scene_dense_original.ply",
            args.original_percent / 100,
        ),
        "medium": (openmvs / "scene_dense_medium.ply", args.medium_percent / 100),
        "low": (openmvs / "scene_dense_low.ply", args.low_percent / 100),
    }
    selected = {
        name: value
        for name, value in previews.items()
        if name in requested and value[1] < 1
    }
    if selected:
        _write_dense_previews(source, selected)
    percentages = {
        "original": args.original_percent,
        "medium": args.medium_percent,
        "low": args.low_percent,
    }
    (openmvs / "scene_dense_levels.json").write_text(
        json.dumps(
            {
                "source_mtime_ns": source.stat().st_mtime_ns,
                "levels": {name: percentages[name] for name in requested},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


def _write_dense_previews(
    source: Path,
    outputs: dict[str, tuple[Path, float]],
) -> None:
    """Stream point-sampled PLY copies while preserving OpenMVS view metadata."""
    print(f"Loading High cloud once to make {len(outputs)} viewing preview(s)", flush=True)
    with source.open("rb") as handle:
        header, point_count, properties = _read_binary_ply_header(handle)
        record_layout = _compile_ply_layout(properties)
        data_offset = handle.tell()
        output_handles: dict[str, tuple[object, int, Path]] = {}
        buffers: dict[str, bytearray] = {}
        accumulators: dict[str, int] = {}
        try:
            for name, (destination, fraction) in outputs.items():
                target = min(point_count, max(1, round(point_count * fraction)))
                temporary = destination.with_name(f".{destination.name}.openreef-tmp")
                output = temporary.open("wb")
                output.write(_header_with_vertex_count(header, target))
                output_handles[name] = (output, target, temporary)
                buffers[name] = bytearray()
                accumulators[name] = 0

            with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
                offset = data_offset
                for _ in range(point_count):
                    record_start = offset
                    offset = _ply_record_end(mapped, offset, record_layout)
                    for name, (output, target, _) in output_handles.items():
                        accumulators[name] += target
                        if accumulators[name] >= point_count:
                            accumulators[name] -= point_count
                            buffers[name].extend(mapped[record_start:offset])
                            if len(buffers[name]) >= 8 * 1024 * 1024:
                                output.write(buffers[name])
                                buffers[name].clear()

                tail = mapped[offset:]
                for name, (output, _, _) in output_handles.items():
                    output.write(buffers[name])
                    output.write(tail)
                    output.close()
        except Exception:
            for output, _, temporary in output_handles.values():
                output.close()
                temporary.unlink(missing_ok=True)
            raise

    for name, (destination, fraction) in outputs.items():
        _, target, temporary = output_handles[name]
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(destination)
        print(
            f"Created {name.title()} preview: {destination.name} "
            f"({target:,} of {point_count:,} points; {fraction:.0%})",
            flush=True,
        )


_PLY_SCALARS = {
    "char": ("b", 1),
    "uchar": ("B", 1),
    "int8": ("b", 1),
    "uint8": ("B", 1),
    "short": ("h", 2),
    "ushort": ("H", 2),
    "int16": ("h", 2),
    "uint16": ("H", 2),
    "int": ("i", 4),
    "uint": ("I", 4),
    "int32": ("i", 4),
    "uint32": ("I", 4),
    "float": ("f", 4),
    "float32": ("f", 4),
    "double": ("d", 8),
    "float64": ("d", 8),
}


def _read_binary_ply_header(handle: object) -> tuple[list[bytes], int, list[tuple[str, ...]]]:
    header: list[bytes] = []
    properties: list[tuple[str, ...]] = []
    point_count: int | None = None
    in_vertices = False
    while True:
        line = handle.readline()
        if not line:
            raise ValueError("PLY header is incomplete")
        header.append(line)
        tokens = line.decode("ascii").strip().split()
        if tokens[:2] == ["format", "binary_little_endian"]:
            pass
        elif tokens and tokens[0] == "format":
            raise ValueError("OpenReef multi-resolution output requires binary PLY input")
        elif tokens[:2] == ["element", "vertex"]:
            point_count = int(tokens[2])
            in_vertices = True
        elif tokens and tokens[0] == "element":
            in_vertices = False
        elif in_vertices and tokens and tokens[0] == "property":
            properties.append(tuple(tokens[1:-1]))
        if tokens == ["end_header"]:
            break
    if point_count is None or not properties:
        raise ValueError("PLY has no vertex element")
    return header, point_count, properties


def _header_with_vertex_count(header: list[bytes], point_count: int) -> bytes:
    output: list[bytes] = []
    for line in header:
        if line.startswith(b"element vertex "):
            ending = b"\r\n" if line.endswith(b"\r\n") else b"\n"
            line = f"element vertex {point_count}".encode() + ending
        output.append(line)
    return b"".join(output)


def _compile_ply_layout(properties: list[tuple[str, ...]]) -> list[tuple[str, int, int]]:
    layout: list[tuple[str, int, int]] = []
    fixed_size = 0
    for specification in properties:
        if specification[0] != "list":
            fixed_size += _PLY_SCALARS[specification[0]][1]
            continue
        if fixed_size:
            layout.append(("", fixed_size, 0))
            fixed_size = 0
        count_type, item_type = specification[1:]
        count_format, count_size = _PLY_SCALARS[count_type]
        layout.append((count_format, count_size, _PLY_SCALARS[item_type][1]))
    if fixed_size:
        layout.append(("", fixed_size, 0))
    return layout


def _ply_record_end(
    mapped: mmap.mmap,
    offset: int,
    layout: list[tuple[str, int, int]],
) -> int:
    for count_format, count_size, item_size in layout:
        if not count_format:
            offset += count_size
            continue
        count = struct.unpack_from("<" + count_format, mapped, offset)[0]
        offset += count_size + count * item_size
    if offset > len(mapped):
        raise ValueError("PLY vertex data ended unexpectedly")
    return offset


def mesh_multi(args: argparse.Namespace) -> int:
    """Reconstruct matching meshes from each selected dense-cloud level."""
    openmvs = Path(args.openmvs_folder)
    levels = [item.strip() for item in args.levels.split(",") if item.strip()]
    percentages = {
        "original": args.original_percent,
        "medium": args.medium_percent,
        "low": args.low_percent,
    }
    cloud_names = {
        "original": "scene_dense.ply"
        if args.original_percent == 100
        else "scene_dense_original.ply",
        "medium": "scene_dense_medium.ply",
        "low": "scene_dense_low.ply",
    }
    mesh_names = {
        "original": "scene_mesh.mvs",
        "medium": "scene_mesh_medium.mvs",
        "low": "scene_mesh_low.mvs",
    }
    for index, level in enumerate(levels, start=1):
        cloud = openmvs / cloud_names[level]
        if not cloud.is_file():
            print(f"Missing selected dense cloud: {cloud}", flush=True)
            return 1
        command = [
            args.executable,
            "scene_dense.mvs",
            "-p",
            cloud.name,
            "-o",
            mesh_names[level],
            "--max-threads",
            str(args.cores),
        ]
        print(
            f"[{index}/{len(levels)}] Reconstructing {level.title()} surface mesh "
            f"from the {percentages[level]}% dense cloud",
            flush=True,
        )
        result = subprocess.run(command, cwd=openmvs, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def texture_multi(args: argparse.Namespace) -> int:
    """Texture each selected mesh level and export a self-contained GLB."""
    openmvs = Path(args.openmvs_folder)
    levels = [item.strip() for item in args.levels.split(",") if item.strip()]
    mesh_names = {
        "original": "scene_mesh.ply",
        "medium": "scene_mesh_medium.ply",
        "low": "scene_mesh_low.ply",
    }
    output_names = {
        "original": "scene_mesh_textured.mvs",
        "medium": "scene_mesh_medium_textured.mvs",
        "low": "scene_mesh_low_textured.mvs",
    }
    for index, level in enumerate(levels, start=1):
        mesh = openmvs / mesh_names[level]
        if not mesh.is_file():
            print(f"Missing selected surface mesh: {mesh}", flush=True)
            return 1
        output = output_names[level]
        command = [
            args.executable,
            "scene_dense.mvs",
            "-m",
            mesh.name,
            "-o",
            output,
            "--export-type",
            "glb",
            "--max-threads",
            str(args.cores),
            "--resolution-level",
            str(args.resolution_level),
            "--max-texture-size",
            str(args.max_texture_size),
            "--sharpness-weight",
            str(args.sharpness_weight),
            "--global-seam-leveling",
            str(args.global_seam_leveling),
            "--local-seam-leveling",
            str(args.local_seam_leveling),
        ]
        print(
            f"[{index}/{len(levels)}] Texturing {level.title()} surface mesh as GLB",
            flush=True,
        )
        result = subprocess.run(command, cwd=openmvs, check=False)
        if result.returncode != 0:
            return result.returncode
        expected = (openmvs / output).with_suffix(".glb")
        if not expected.is_file():
            print(f"TextureMesh did not create its expected output: {expected}", flush=True)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="task", required=True)
    importer = subparsers.add_parser("import-openmvs")
    importer.add_argument("--executable", required=True)
    importer.add_argument("--dense-folder", required=True)
    importer.add_argument("--openmvs-folder", required=True)
    importer.add_argument("--cores", type=int, required=True)
    importer.add_argument("--colmap-executable", required=True)
    importer.add_argument("--roi", required=True)
    importer.add_argument("--sparse-model", required=True)
    sparse = subparsers.add_parser("sparse-colmap")
    sparse.add_argument("--executable", required=True)
    sparse.add_argument("--database", required=True)
    sparse.add_argument("--images", required=True)
    sparse.add_argument("--output", required=True)
    sparse.add_argument("--cores", type=int, required=True)
    undistort = subparsers.add_parser("undistort-colmap")
    undistort.add_argument("--executable", required=True)
    undistort.add_argument("--images", required=True)
    undistort.add_argument("--input", required=True)
    undistort.add_argument("--output", required=True)
    undistort.add_argument("--max-image-size", type=int, required=True)
    undistort.add_argument("--state", required=True)
    dense = subparsers.add_parser("dense-multi")
    dense.add_argument("--executable", required=True)
    dense.add_argument("--openmvs-folder", required=True)
    dense.add_argument("--cores", type=int, required=True)
    dense.add_argument("--resolution-level", type=int, required=True)
    dense.add_argument("--max-resolution", type=int, required=True)
    dense.add_argument("--number-views", type=int, required=True)
    dense.add_argument("--number-views-fuse", type=int, required=True)
    dense.add_argument("--estimate-colors", type=int, required=True)
    dense.add_argument("--estimate-normals", type=int, required=True)
    dense.add_argument("--levels", required=True)
    dense.add_argument("--original-percent", type=int, required=True)
    dense.add_argument("--medium-percent", type=int, required=True)
    dense.add_argument("--low-percent", type=int, required=True)
    mesh = subparsers.add_parser("mesh-multi")
    mesh.add_argument("--executable", required=True)
    mesh.add_argument("--openmvs-folder", required=True)
    mesh.add_argument("--levels", required=True)
    mesh.add_argument("--original-percent", type=int, required=True)
    mesh.add_argument("--medium-percent", type=int, required=True)
    mesh.add_argument("--low-percent", type=int, required=True)
    mesh.add_argument("--cores", type=int, required=True)
    texture = subparsers.add_parser("texture-multi")
    texture.add_argument("--executable", required=True)
    texture.add_argument("--openmvs-folder", required=True)
    texture.add_argument("--levels", required=True)
    texture.add_argument("--cores", type=int, required=True)
    texture.add_argument("--resolution-level", type=int, required=True)
    texture.add_argument("--max-texture-size", type=int, required=True)
    texture.add_argument("--sharpness-weight", type=float, required=True)
    texture.add_argument("--global-seam-leveling", type=int, required=True)
    texture.add_argument("--local-seam-leveling", type=int, required=True)
    args = parser.parse_args()
    if args.task == "import-openmvs":
        return import_openmvs(args)
    if args.task == "sparse-colmap":
        return sparse_colmap(args)
    if args.task == "undistort-colmap":
        return undistort_colmap(args)
    if args.task == "dense-multi":
        return dense_multi(args)
    if args.task == "mesh-multi":
        return mesh_multi(args)
    if args.task == "texture-multi":
        return texture_multi(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())

"""Build a spatial 3D Tiles hierarchy from an OpenReef textured GLB."""

from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from openreef.core.glb_edit import (
    _embed_external_buffers,
    _embed_external_images,
    _read_glb,
    make_compact_glb,
)
from openreef.pipeline.stages import DatasetLayout
from openreef.web_export import export_tiled_web_viewer, write_tiled_model_manifest

DEFAULT_TRIANGLES_PER_TILE = 25_000
TILE_TEXTURE_MAX_DIMENSION = 1024
TILE_TEXTURE_JPEG_QUALITY = 72
COARSE_MODEL_MAX_BYTES = 12 * 1024 * 1024
SUPPORTED_SOURCE_FORMATS = frozenset({".glb"})


@dataclass(frozen=True)
class ObjMesh:
    vertices: np.ndarray
    texcoords: np.ndarray
    normals: np.ndarray
    vertex_indices: np.ndarray
    texcoord_indices: np.ndarray
    normal_indices: np.ndarray
    materials: np.ndarray

    @property
    def triangle_count(self) -> int:
        return int(len(self.vertex_indices))


@dataclass(frozen=True)
class SpatialLeaf:
    triangle_indices: np.ndarray
    bounds: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class TileTextures:
    texcoords: np.ndarray
    texcoord_indices: np.ndarray
    material_images: dict[int, Path]


@dataclass(frozen=True)
class TextureComponent:
    rows: np.ndarray
    texcoord_ids: np.ndarray
    box: tuple[int, int, int, int]


def resolve_assimp() -> Path:
    """Find the Assimp command-line converter used for material-safe GLB conversion."""
    discovered = shutil.which("assimp")
    candidates = (
        Path(discovered) if discovered else None,
        Path("/opt/homebrew/bin/assimp"),
        Path("/usr/local/bin/assimp"),
    )
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise RuntimeError(
        "Assimp is required to build spatial 3D Tiles. On macOS, install it with "
        "Homebrew (`brew install assimp`), then reopen OpenReef."
    )


def build_dataset_tiles(
    model: str | Path,
    dataset: str | Path,
    *,
    triangles_per_tile: int = DEFAULT_TRIANGLES_PER_TILE,
) -> Path:
    """Generate, package, and register a spatial tileset for one dataset."""
    source = Path(model).expanduser().resolve()
    layout = DatasetLayout.from_path(dataset)
    if not source.is_file() or source.suffix.lower() not in SUPPORTED_SOURCE_FORMATS:
        raise ValueError("Choose a textured GLB model to build 3D Tiles.")
    if triangles_per_tile < 1_000:
        raise ValueError("Triangles per tile must be at least 1,000.")

    coarse = discover_coarse_model(source, layout)
    _progress(1, f"Preparing {source.name}")
    with TemporaryDirectory(prefix="openreef-3d-tiles-") as temporary:
        generated = Path(temporary) / "generated"
        tileset = generate_spatial_tileset(
            source,
            generated,
            coarse_model=coarse,
            triangles_per_tile=triangles_per_tile,
        )
        _progress(88, "Packaging tiled viewer")
        result = export_tiled_web_viewer(
            tileset,
            layout.tiled_web_export,
            title=layout.root.name,
        )
    entry = write_tiled_model_manifest(
        result,
        layout.tiled_model_manifest,
        title=layout.root.name,
    )
    _progress(100, "3D Tiles ready in Models")
    print(f"OPENREEF_TILE_RESULT\t{entry}", flush=True)
    return entry


def discover_coarse_model(source: Path, layout: DatasetLayout) -> Path:
    """Prefer the smallest matching textured GLB as the hierarchy's coarse root."""
    candidates: list[Path] = []
    for folder in (layout.models, layout.openmvs):
        if not folder.is_dir():
            continue
        candidates.extend(
            path.resolve()
            for path in folder.glob("*.glb")
            if path.is_file() and "textur" in path.name.casefold()
        )
    unique = {path for path in candidates if path.is_file()}
    if source not in unique:
        unique.add(source)
    preferred = [
        path
        for path in unique
        if any(level in path.name.casefold() for level in ("compact", "low"))
    ]
    pool = preferred or list(unique)
    return min(pool, key=lambda path: path.stat().st_size)


def generate_spatial_tileset(
    model: str | Path,
    output_folder: str | Path,
    *,
    coarse_model: str | Path | None = None,
    triangles_per_tile: int = DEFAULT_TRIANGLES_PER_TILE,
) -> Path:
    """Split a GLB into spatial leaf tiles beneath a coarse replace-refinement root."""
    source = Path(model).expanduser().resolve()
    output = Path(output_folder).expanduser().resolve()
    coarse = Path(coarse_model).expanduser().resolve() if coarse_model else source
    assimp = resolve_assimp()
    output.mkdir(parents=True, exist_ok=True)
    tiles_folder = output / "tiles"
    textures_folder = output / "textures"
    root_folder = output / "root"
    work_folder = output / ".build"
    for folder in (tiles_folder, textures_folder, root_folder, work_folder):
        folder.mkdir(parents=True, exist_ok=True)

    gltf, binary = _read_glb(source)
    _embed_external_buffers(gltf, binary, source.parent)
    _embed_external_images(gltf, binary, source.parent)
    source_textures = work_folder / "source-textures"
    source_textures.mkdir()
    source_images = _write_source_textures(gltf, binary, source_textures)
    material_images = _material_images(gltf, source_images)
    primitive_materials = _primitive_materials(gltf)

    converted_obj = work_folder / "source.obj"
    _run_assimp(assimp, source, converted_obj, "obj")
    mesh = read_assimp_obj(converted_obj, primitive_materials)
    if mesh.triangle_count == 0:
        raise ValueError("The selected GLB contains no triangle mesh to tile.")
    _progress(14, f"Partitioning {mesh.triangle_count:,} triangles")
    leaves = partition_mesh(mesh, triangles_per_tile=triangles_per_tile)

    for index, leaf in enumerate(leaves):
        temporary_obj = work_folder / f"tile_{index:04d}.obj"
        temporary_mtl = work_folder / f"tile_{index:04d}.mtl"
        output_gltf = tiles_folder / f"tile_{index:04d}.gltf"
        tile_textures = repack_tile_textures(
            mesh,
            leaf.triangle_indices,
            material_images,
            textures_folder,
            stem=f"tile_{index:04d}",
        )
        _write_tile_mtl(temporary_mtl, gltf, tile_textures.material_images)
        write_obj_subset(
            mesh,
            leaf.triangle_indices,
            temporary_obj,
            temporary_mtl,
            tile_textures=tile_textures,
        )
        _run_assimp(assimp, temporary_obj, output_gltf, "gltf2")
        _rewrite_gltf_texture_uris(output_gltf, textures_folder)
        temporary_obj.unlink(missing_ok=True)
        temporary_mtl.unlink(missing_ok=True)
        percent = 18 + round(62 * (index + 1) / len(leaves))
        _progress(percent, f"Built spatial tile {index + 1} of {len(leaves)}")

    root_model = root_folder / "coarse.glb"
    try:
        make_compact_glb(
            coarse,
            root_model,
            max_bytes=_coarse_target_bytes(coarse),
        )
    except ValueError:
        root_model.unlink(missing_ok=True)
    bounds = _tiles_bounds(mesh.vertices[mesh.vertex_indices.reshape(-1)])
    diagonal = _bounds_diagonal(bounds)
    root = {
        "boundingVolume": {"box": _bounding_box(bounds)},
        "geometricError": max(diagonal * 0.08, 0.001),
        "refine": "REPLACE",
        "children": [
            {
                "boundingVolume": {"box": _bounding_box(leaf.bounds)},
                "geometricError": 0,
                "content": {"uri": f"tiles/tile_{index:04d}.gltf"},
            }
            for index, leaf in enumerate(leaves)
        ],
    }
    if root_model.is_file():
        root["content"] = {"uri": "root/coarse.glb"}
    tileset = {
        "asset": {"version": "1.1", "generator": "OpenReef 0.6.2"},
        "geometricError": root["geometricError"],
        "root": root,
        "extras": {
            "openreef": {
                "source": source.name,
                "coarseSource": coarse.name if root_model.is_file() else None,
                "triangleCount": mesh.triangle_count,
                "leafTiles": len(leaves),
                "trianglesPerTile": triangles_per_tile,
            }
        },
    }
    path = output / "tileset.json"
    path.write_text(json.dumps(tileset, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(work_folder)
    _progress(84, f"Generated {len(leaves)} spatial tiles")
    return path


def read_assimp_obj(path: str | Path, primitive_materials: Sequence[int]) -> ObjMesh:
    """Read the predictable triangulated OBJ written by Assimp."""
    vertices: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces_v: list[tuple[int, int, int]] = []
    faces_vt: list[tuple[int, int, int]] = []
    faces_vn: list[tuple[int, int, int]] = []
    materials: list[int] = []
    primitive_index = -1

    with Path(path).open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("v "):
                values = line.split()
                vertices.append((float(values[1]), float(values[2]), float(values[3])))
            elif line.startswith("vt "):
                values = line.split()
                texcoords.append((float(values[1]), float(values[2])))
            elif line.startswith("vn "):
                values = line.split()
                normals.append((float(values[1]), float(values[2]), float(values[3])))
            elif line.startswith(("g ", "o ")):
                primitive_index += 1
            elif line.startswith("f "):
                tokens = line.split()[1:]
                if len(tokens) < 3:
                    continue
                parsed = [_parse_obj_index(token) for token in tokens]
                bounded_index = min(max(primitive_index, 0), len(primitive_materials) - 1)
                material = (
                    int(primitive_materials[bounded_index])
                    if primitive_materials
                    else -1
                )
                for offset in range(1, len(parsed) - 1):
                    triangle = (parsed[0], parsed[offset], parsed[offset + 1])
                    faces_v.append(tuple(item[0] for item in triangle))
                    faces_vt.append(tuple(item[1] for item in triangle))
                    faces_vn.append(tuple(item[2] for item in triangle))
                    materials.append(material)

    return ObjMesh(
        np.asarray(vertices, dtype=np.float64),
        np.asarray(texcoords, dtype=np.float64).reshape(-1, 2),
        np.asarray(normals, dtype=np.float64).reshape(-1, 3),
        np.asarray(faces_v, dtype=np.int64).reshape(-1, 3),
        np.asarray(faces_vt, dtype=np.int64).reshape(-1, 3),
        np.asarray(faces_vn, dtype=np.int64).reshape(-1, 3),
        np.asarray(materials, dtype=np.int64),
    )


def partition_mesh(mesh: ObjMesh, *, triangles_per_tile: int) -> tuple[SpatialLeaf, ...]:
    """Partition triangles by centroid along the two widest model axes."""
    centroids = mesh.vertices[mesh.vertex_indices].mean(axis=1)
    spans = np.ptp(centroids, axis=0)
    axes = tuple(int(value) for value in np.argsort(spans)[-2:])
    pending = [np.arange(mesh.triangle_count, dtype=np.int64)]
    leaves: list[np.ndarray] = []
    while pending:
        indices = pending.pop()
        if len(indices) <= triangles_per_tile:
            leaves.append(indices)
            continue
        points = centroids[indices][:, axes]
        split = np.median(points, axis=0)
        quadrant = (points[:, 0] >= split[0]).astype(np.uint8)
        quadrant += 2 * (points[:, 1] >= split[1]).astype(np.uint8)
        children = [indices[quadrant == value] for value in range(4)]
        children = [child for child in children if len(child)]
        if len(children) == 1:
            order = np.argsort(points[:, int(np.argmax(np.ptp(points, axis=0)))])
            midpoint = len(order) // 2
            children = [indices[order[:midpoint]], indices[order[midpoint:]]]
        pending.extend(children)
    leaves.sort(key=lambda values: int(values.min()))
    return tuple(
        SpatialLeaf(indices, _tiles_bounds(mesh.vertices[mesh.vertex_indices[indices].reshape(-1)]))
        for indices in leaves
    )


def write_obj_subset(
    mesh: ObjMesh,
    triangle_indices: np.ndarray,
    destination: Path,
    material_file: Path,
    *,
    tile_textures: TileTextures | None = None,
) -> None:
    """Write one spatial triangle subset with compact local OBJ indices."""
    selected_v = mesh.vertex_indices[triangle_indices]
    used_v, inverse_v = np.unique(selected_v, return_inverse=True)
    local_v = inverse_v.reshape(-1, 3) + 1
    texcoords = tile_textures.texcoords if tile_textures is not None else mesh.texcoords
    selected_vt = (
        tile_textures.texcoord_indices
        if tile_textures is not None
        else mesh.texcoord_indices[triangle_indices]
    )
    valid_vt = selected_vt >= 0
    if np.any(valid_vt):
        used_vt, inverse_vt = np.unique(selected_vt[valid_vt], return_inverse=True)
        local_vt = np.full(selected_vt.shape, -1, dtype=np.int64)
        local_vt[valid_vt] = inverse_vt + 1
    else:
        used_vt = np.empty(0, dtype=np.int64)
        local_vt = np.full(selected_vt.shape, -1, dtype=np.int64)
    selected_vn = mesh.normal_indices[triangle_indices]
    valid_vn = selected_vn >= 0
    if np.any(valid_vn):
        used_vn, inverse_vn = np.unique(selected_vn[valid_vn], return_inverse=True)
        local_vn = np.full(selected_vn.shape, -1, dtype=np.int64)
        local_vn[valid_vn] = inverse_vn + 1
    else:
        used_vn = np.empty(0, dtype=np.int64)
        local_vn = np.full(selected_vn.shape, -1, dtype=np.int64)

    with destination.open("w", encoding="utf-8") as stream:
        stream.write(f"mtllib {material_file.name}\n")
        for x, y, z in mesh.vertices[used_v]:
            stream.write(f"v {x:.9g} {y:.9g} {z:.9g}\n")
        for u, v in texcoords[used_vt]:
            stream.write(f"vt {u:.9g} {v:.9g}\n")
        for x, y, z in mesh.normals[used_vn]:
            stream.write(f"vn {x:.9g} {y:.9g} {z:.9g}\n")
        selected_materials = mesh.materials[triangle_indices]
        for material in np.unique(selected_materials):
            stream.write(f"usemtl material_{int(material)}\n")
            rows = np.flatnonzero(selected_materials == material)
            for row in rows:
                values = [
                    _format_obj_vertex(local_v[row, col], local_vt[row, col], local_vn[row, col])
                    for col in range(3)
                ]
                stream.write(f"f {' '.join(values)}\n")


def _write_source_textures(
    gltf: dict[str, Any],
    binary: bytearray,
    destination: Path,
) -> dict[int, Path]:
    paths: dict[int, Path] = {}
    for index, image in enumerate(gltf.get("images", [])):
        view = gltf["bufferViews"][int(image["bufferView"])]
        offset = int(view.get("byteOffset", 0))
        payload = bytes(binary[offset : offset + int(view["byteLength"])])
        mime = str(image.get("mimeType") or "application/octet-stream")
        extension = mimetypes.guess_extension(mime) or ".bin"
        if extension == ".jpe":
            extension = ".jpg"
        path = destination / f"source_{index}{extension}"
        path.write_bytes(payload)
        paths[index] = path
    return paths


def _material_images(
    gltf: dict[str, Any],
    images: dict[int, Path],
) -> dict[int, Path]:
    resolved: dict[int, Path] = {}
    textures = gltf.get("textures", [])
    for material_index, material in enumerate(gltf.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        texture_info = pbr.get("baseColorTexture")
        if not isinstance(texture_info, dict):
            continue
        texture_index = int(texture_info.get("index", -1))
        if not 0 <= texture_index < len(textures):
            continue
        image_index = int(textures[texture_index].get("source", -1))
        if image_index in images:
            resolved[material_index] = images[image_index]
    return resolved


def repack_tile_textures(
    mesh: ObjMesh,
    triangle_indices: np.ndarray,
    material_images: dict[int, Path],
    destination: Path,
    *,
    stem: str,
) -> TileTextures:
    """Pack only the selected UV islands into small, tile-local texture atlases."""
    selected_vt = mesh.texcoord_indices[triangle_indices]
    selected_materials = mesh.materials[triangle_indices]
    rewritten = np.full(selected_vt.shape, -1, dtype=np.int64)
    packed_texcoords: list[tuple[float, float]] = []
    packed_images: dict[int, Path] = {}

    for material in np.unique(selected_materials):
        material_index = int(material)
        source_path = material_images.get(material_index)
        if source_path is None:
            continue
        rows = np.flatnonzero(selected_materials == material)
        valid_rows = rows[np.all(selected_vt[rows] >= 0, axis=1)]
        if not len(valid_rows):
            continue
        with Image.open(source_path) as opened:
            source = opened.copy()
        components = _texture_components(
            mesh.texcoords,
            selected_vt,
            valid_rows,
            source.size,
        )
        if not components:
            continue
        atlas, placements = _pack_texture_components(source, components)
        has_alpha = atlas.mode in {"RGBA", "LA"} and atlas.getchannel("A").getextrema()[0] < 255
        suffix = ".png" if has_alpha else ".jpg"
        output = destination / f"{stem}_material_{material_index}{suffix}"
        if has_alpha:
            atlas.save(output, "PNG", optimize=True, compress_level=9)
        else:
            atlas.convert("RGB").save(
                output,
                "JPEG",
                quality=TILE_TEXTURE_JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )
        packed_images[material_index] = output

        image_width, image_height = source.size
        atlas_width, atlas_height = atlas.size
        for component, (x, y, width, height) in zip(components, placements, strict=True):
            x0, y0, x1, y1 = component.box
            crop_width = max(1, x1 - x0)
            crop_height = max(1, y1 - y0)
            bottom0 = image_height - y1
            mapping: dict[int, int] = {}
            for texcoord_id in component.texcoord_ids:
                u, v = mesh.texcoords[int(texcoord_id)]
                relative_u = (float(u) * image_width - x0) / crop_width
                relative_v = (float(v) * image_height - bottom0) / crop_height
                packed_u = (x + np.clip(relative_u, 0, 1) * width) / atlas_width
                packed_v = (
                    atlas_height - (y + height) + np.clip(relative_v, 0, 1) * height
                ) / atlas_height
                mapping[int(texcoord_id)] = len(packed_texcoords)
                packed_texcoords.append((float(packed_u), float(packed_v)))
            for row in component.rows:
                for column in range(3):
                    rewritten[row, column] = mapping[int(selected_vt[row, column])]

    return TileTextures(
        np.asarray(packed_texcoords, dtype=np.float64).reshape(-1, 2),
        rewritten,
        packed_images,
    )


def _texture_components(
    texcoords: np.ndarray,
    selected_indices: np.ndarray,
    rows: np.ndarray,
    image_size: tuple[int, int],
) -> tuple[TextureComponent, ...]:
    """Return UV-connected triangle groups and padded source-image crop boxes."""
    parent = np.arange(len(rows), dtype=np.int64)
    rank = np.zeros(len(rows), dtype=np.uint8)

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = int(parent[value])
        return value

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        if rank[left_root] < rank[right_root]:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        if rank[left_root] == rank[right_root]:
            rank[left_root] += 1

    seen: dict[int, int] = {}
    for local_row, selected_row in enumerate(rows):
        for texcoord_id in selected_indices[selected_row]:
            identifier = int(texcoord_id)
            previous = seen.get(identifier)
            if previous is None:
                seen[identifier] = local_row
            else:
                union(local_row, previous)

    groups: dict[int, list[int]] = {}
    for local_row, selected_row in enumerate(rows):
        groups.setdefault(find(local_row), []).append(int(selected_row))

    image_width, image_height = image_size
    components: list[TextureComponent] = []
    for selected_rows in groups.values():
        component_rows = np.asarray(selected_rows, dtype=np.int64)
        texcoord_ids = np.unique(selected_indices[component_rows].reshape(-1))
        uv = np.clip(texcoords[texcoord_ids], 0, 1)
        padding = 3
        x0 = max(0, int(np.floor(float(uv[:, 0].min()) * image_width)) - padding)
        x1 = min(
            image_width,
            int(np.ceil(float(uv[:, 0].max()) * image_width)) + padding + 1,
        )
        bottom0 = max(0, int(np.floor(float(uv[:, 1].min()) * image_height)) - padding)
        bottom1 = min(
            image_height,
            int(np.ceil(float(uv[:, 1].max()) * image_height)) + padding + 1,
        )
        y0, y1 = image_height - bottom1, image_height - bottom0
        components.append(TextureComponent(component_rows, texcoord_ids, (x0, y0, x1, y1)))
    components.sort(key=lambda component: component.box[3] - component.box[1], reverse=True)
    return tuple(components)


def _pack_texture_components(
    source: Image.Image,
    components: Sequence[TextureComponent],
) -> tuple[Image.Image, tuple[tuple[int, int, int, int], ...]]:
    sizes = np.asarray(
        [(item.box[2] - item.box[0], item.box[3] - item.box[1]) for item in components],
        dtype=np.float64,
    )
    total_area = float(np.sum(sizes[:, 0] * sizes[:, 1]))
    largest = float(np.max(sizes))
    scale = min(
        1.0,
        TILE_TEXTURE_MAX_DIMENSION / max(largest, 1),
        np.sqrt(TILE_TEXTURE_MAX_DIMENSION**2 * 0.72 / max(total_area, 1)),
    )
    placements: list[tuple[int, int, int, int]] = []
    while scale >= 0.02:
        scaled = np.maximum(2, np.ceil(sizes * scale).astype(np.int64))
        placements = _shelf_pack(scaled, TILE_TEXTURE_MAX_DIMENSION)
        required_height = max((y + height for _, y, _, height in placements), default=1)
        if required_height <= TILE_TEXTURE_MAX_DIMENSION:
            break
        scale *= 0.82
    if not placements:
        raise ValueError("Could not pack this tile's texture islands")

    required_width = max((x + width for x, _, width, _ in placements), default=1)
    required_height = max((y + height for _, y, _, height in placements), default=1)
    if required_height > TILE_TEXTURE_MAX_DIMENSION:
        raise ValueError("This tile has too many texture islands to pack")
    atlas_width = min(TILE_TEXTURE_MAX_DIMENSION, _next_power_of_two(required_width))
    atlas_height = min(TILE_TEXTURE_MAX_DIMENSION, _next_power_of_two(required_height))
    mode = "RGBA" if source.mode in {"RGBA", "LA"} else "RGB"
    atlas = Image.new(mode, (atlas_width, atlas_height), (0, 0, 0, 0) if mode == "RGBA" else 0)
    for component, (x, y, width, height) in zip(components, placements, strict=True):
        patch = source.crop(component.box)
        if patch.size != (width, height):
            patch = patch.resize((width, height), Image.Resampling.LANCZOS)
        if patch.mode != mode:
            patch = patch.convert(mode)
        atlas.paste(patch, (x, y))
    return atlas, tuple(placements)


def _coarse_target_bytes(_source: Path) -> int:
    """Keep the optional preview small enough that it never dominates startup."""
    return COARSE_MODEL_MAX_BYTES


def _shelf_pack(sizes: np.ndarray, width_limit: int) -> list[tuple[int, int, int, int]]:
    placements: list[tuple[int, int, int, int]] = []
    x = y = row_height = 0
    for width, height in sizes:
        tile_width, tile_height = int(width), int(height)
        if x and x + tile_width > width_limit:
            x = 0
            y += row_height
            row_height = 0
        placements.append((x, y, tile_width, tile_height))
        x += tile_width
        row_height = max(row_height, tile_height)
    return placements


def _next_power_of_two(value: int) -> int:
    return 1 if value <= 1 else 1 << (value - 1).bit_length()


def _write_tile_mtl(
    path: Path,
    gltf: dict[str, Any],
    material_images: dict[int, Path],
) -> None:
    lines: list[str] = []
    for index, material in enumerate(gltf.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        color = pbr.get("baseColorFactor", [1, 1, 1, 1])
        lines.extend(
            (
                f"newmtl material_{index}",
                f"Kd {float(color[0]):.6g} {float(color[1]):.6g} {float(color[2]):.6g}",
                f"d {float(color[3]):.6g}",
                "illum 1",
            )
        )
        image = material_images.get(index)
        if image is not None:
            lines.append(f"map_Kd {image}")
        lines.append("")
    if not lines:
        lines = ["newmtl material_-1", "Kd 1 1 1", "illum 1", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _rewrite_gltf_texture_uris(path: Path, textures_folder: Path) -> None:
    gltf = json.loads(path.read_text(encoding="utf-8"))
    available = {item.name for item in textures_folder.iterdir() if item.is_file()}
    for image in gltf.get("images", []):
        name = Path(str(image.get("uri", ""))).name
        if name in available:
            image["uri"] = f"../textures/{name}"
    path.write_text(
        json.dumps(gltf, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _primitive_materials(gltf: dict[str, Any]) -> tuple[int, ...]:
    return tuple(
        int(primitive.get("material", -1))
        for mesh in gltf.get("meshes", [])
        for primitive in mesh.get("primitives", [])
        if int(primitive.get("mode", 4)) == 4
    )


def _run_assimp(assimp: Path, source: Path, destination: Path, output_format: str) -> None:
    result = subprocess.run(
        [str(assimp), "export", str(source), str(destination), f"-f{output_format}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not destination.is_file():
        details = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError(f"Assimp could not convert {source.name}: {details[-1200:]}")


def _parse_obj_index(token: str) -> tuple[int, int, int]:
    fields = token.split("/")
    vertex = int(fields[0]) - 1
    texcoord = int(fields[1]) - 1 if len(fields) > 1 and fields[1] else -1
    normal = int(fields[2]) - 1 if len(fields) > 2 and fields[2] else -1
    return vertex, texcoord, normal


def _format_obj_vertex(vertex: int, texcoord: int, normal: int) -> str:
    if texcoord >= 0 and normal >= 0:
        return f"{vertex}/{texcoord}/{normal}"
    if texcoord >= 0:
        return f"{vertex}/{texcoord}"
    if normal >= 0:
        return f"{vertex}//{normal}"
    return str(vertex)


def _tiles_bounds(points: np.ndarray) -> tuple[float, float, float, float, float, float]:
    # glTF content is converted from Y-up to the 3D Tiles Z-up frame at runtime.
    converted = np.column_stack((points[:, 0], -points[:, 2], points[:, 1]))
    minimum = converted.min(axis=0)
    maximum = converted.max(axis=0)
    return (
        float(minimum[0]),
        float(maximum[0]),
        float(minimum[1]),
        float(maximum[1]),
        float(minimum[2]),
        float(maximum[2]),
    )


def _bounding_box(bounds: tuple[float, float, float, float, float, float]) -> list[float]:
    x0, x1, y0, y1, z0, z1 = bounds
    return [
        (x0 + x1) / 2,
        (y0 + y1) / 2,
        (z0 + z1) / 2,
        (x1 - x0) / 2,
        0,
        0,
        0,
        (y1 - y0) / 2,
        0,
        0,
        0,
        (z1 - z0) / 2,
    ]


def _bounds_diagonal(bounds: tuple[float, float, float, float, float, float]) -> float:
    return float(
        np.linalg.norm(
            (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
        )
    )


def _progress(percent: int, message: str) -> None:
    print(f"OPENREEF_TILE_PROGRESS\t{percent}\t{message}", flush=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="textured GLB to tile")
    parser.add_argument("--dataset", type=Path, required=True, help="OpenReef dataset folder")
    parser.add_argument(
        "--triangles-per-tile",
        type=int,
        default=DEFAULT_TRIANGLES_PER_TILE,
        help="maximum leaf-tile triangle count",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        build_dataset_tiles(
            args.model,
            args.dataset,
            triangles_per_tile=args.triangles_per_tile,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"3D Tiles build failed: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

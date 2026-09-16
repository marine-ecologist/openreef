import json
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from openreef.core.glb_edit import _build_glb
from openreef.tile_builder import (
    TILE_TEXTURE_MAX_DIMENSION,
    ObjMesh,
    build_dataset_tiles,
    generate_spatial_tileset,
    partition_mesh,
    resolve_assimp,
)
from openreef.web_export import read_tiled_model_manifest


def _assimp_available() -> bool:
    try:
        resolve_assimp()
    except RuntimeError:
        return False
    return True


def _source_glb(path: Path) -> None:
    positions = np.asarray(
        ((-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0), (1, 0, 0), (1, 1, 0)),
        dtype="<f4",
    ).tobytes()
    texcoords = np.asarray(
        ((0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5), (1, 0.5), (1, 1)),
        dtype="<f4",
    ).tobytes()
    indices = np.asarray((0, 1, 2, 0, 2, 3, 2, 4, 5), dtype="<u2").tobytes()
    image_file = BytesIO()
    Image.new("RGB", (8, 8), (20, 130, 180)).save(image_file, "PNG")
    image = image_file.getvalue()
    binary = bytearray(positions + texcoords + indices + image)
    position_end = len(positions)
    texcoord_end = position_end + len(texcoords)
    index_end = texcoord_end + len(indices)
    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
                        "indices": 2,
                        "material": 0,
                    }
                ]
            }
        ],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
        "textures": [{"source": 0}],
        "images": [{"bufferView": 3, "mimeType": "image/png"}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions)},
            {"buffer": 0, "byteOffset": position_end, "byteLength": len(texcoords)},
            {"buffer": 0, "byteOffset": texcoord_end, "byteLength": len(indices)},
            {"buffer": 0, "byteOffset": index_end, "byteLength": len(image)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 6, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5126, "count": 6, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 9, "type": "SCALAR"},
        ],
    }
    path.write_bytes(_build_glb(gltf, binary))


def test_partition_mesh_creates_spatial_leaves_below_triangle_limit() -> None:
    vertices = np.asarray(
        ((0, 0, 0), (1, 0, 0), (0, 1, 0), (10, 0, 0), (11, 0, 0), (10, 1, 0)),
        dtype=float,
    )
    mesh = ObjMesh(
        vertices=vertices,
        texcoords=np.empty((0, 2)),
        normals=np.empty((0, 3)),
        vertex_indices=np.asarray(((0, 1, 2), (3, 4, 5))),
        texcoord_indices=np.full((2, 3), -1),
        normal_indices=np.full((2, 3), -1),
        materials=np.asarray((0, 0)),
    )

    leaves = partition_mesh(mesh, triangles_per_tile=1)

    assert len(leaves) == 2
    assert all(len(leaf.triangle_indices) == 1 for leaf in leaves)
    assert leaves[0].bounds != leaves[1].bounds


@pytest.mark.skipif(not _assimp_available(), reason="Assimp is not installed")
def test_generate_spatial_tileset_builds_real_gltf_leaf_tiles(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    _source_glb(source)

    tileset_path = generate_spatial_tileset(
        source,
        tmp_path / "generated",
        triangles_per_tile=1,
    )

    tileset = json.loads(tileset_path.read_text())
    children = tileset["root"]["children"]
    assert tileset["asset"]["version"] == "1.1"
    assert tileset["root"]["refine"] == "REPLACE"
    assert tileset["root"]["content"]["uri"] == "root/coarse.glb"
    assert len(children) >= 2
    first_gltf = tileset_path.parent / children[0]["content"]["uri"]
    content = json.loads(first_gltf.read_text())
    assert first_gltf.with_suffix(".bin").is_file()
    texture_uri = content["images"][0]["uri"]
    assert texture_uri.startswith("../textures/tile_")
    texture_path = (first_gltf.parent / texture_uri).resolve()
    assert texture_path.is_file()
    with Image.open(texture_path) as texture:
        assert max(texture.size) <= TILE_TEXTURE_MAX_DIMENSION


@pytest.mark.skipif(not _assimp_available(), reason="Assimp is not installed")
def test_build_dataset_tiles_packages_and_registers_viewer_model(tmp_path: Path) -> None:
    dataset = tmp_path / "reef"
    source = dataset / "models" / "reef_textured_mesh.glb"
    source.parent.mkdir(parents=True)
    _source_glb(source)

    entry = build_dataset_tiles(source, dataset, triangles_per_tile=1_000)
    manifest = read_tiled_model_manifest(entry)

    assert entry == dataset / "models" / "reef_3d_tiles.json"
    assert manifest.viewer == dataset / "openreef-web-tiles" / "index.html"
    assert manifest.tileset == (
        dataset / "openreef-web-tiles" / "tiles" / "tileset.json"
    )
    assert manifest.tileset.is_file()

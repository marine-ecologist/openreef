import struct
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
import pyvista as pv
from PIL import Image

from openreef.core.glb_edit import (
    GLB_TRIANGLE_ID,
    _build_glb,
    _primitive_indices,
    _read_glb,
    make_compact_glb,
    make_glb_self_contained,
)
from openreef.core.mesh_edit import save_document
from openreef.core.model import ModelDocument, ModelPart


def source_glb(path: Path, *, external_image: bool = False) -> None:
    positions = np.asarray(
        ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
        dtype="<f4",
    ).tobytes()
    texture_coordinates = np.asarray(
        ((0, 0), (1, 0), (1, 1), (0, 1)),
        dtype="<f4",
    ).tobytes()
    indices = np.asarray((0, 1, 2, 0, 2, 3), dtype="<u2").tobytes()
    image = b"PNG!"
    binary = bytearray(positions + texture_coordinates + indices)
    if not external_image:
        binary.extend(image)
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
        "images": (
            [{"uri": "reef.png"}]
            if external_image
            else [{"bufferView": 3, "mimeType": "image/png"}]
        ),
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {
                "buffer": 0,
                "byteOffset": len(positions),
                "byteLength": len(texture_coordinates),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(positions) + len(texture_coordinates),
                "byteLength": len(indices),
                "target": 34963,
            },
            *(
                []
                if external_image
                else [
                    {
                        "buffer": 0,
                        "byteOffset": len(positions) + len(texture_coordinates) + len(indices),
                        "byteLength": len(image),
                    }
                ]
            ),
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC2"},
            {
                "bufferView": 2,
                "componentType": 5123,
                "count": 6,
                "type": "SCALAR",
            },
        ],
    }
    path.write_bytes(_build_glb(gltf, binary))


def test_save_edited_glb_reuses_materials_images_and_retained_triangle(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source)
    mesh = pv.PolyData(
        np.asarray(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), dtype=float),
        faces=np.asarray((3, 0, 2, 3)),
    )
    mesh.cell_data[GLB_TRIANGLE_ID] = np.asarray((1,), dtype=np.int64)
    document = ModelDocument(
        source.with_name("reef_trimmed.glb"),
        (ModelPart("Reef", mesh, "mesh"),),
        material_source=source,
    )

    destination = save_document(document, tmp_path / "reef_edited.glb")

    gltf, binary = _read_glb(destination)
    primitive = gltf["meshes"][0]["primitives"][0]
    retained, _ = _primitive_indices(primitive, gltf, binary)
    image_view = gltf["bufferViews"][gltf["images"][0]["bufferView"]]
    image_offset = image_view["byteOffset"]
    assert retained.tolist() == [0, 2, 3]
    assert bytes(binary[image_offset : image_offset + image_view["byteLength"]]) == b"PNG!"
    assert primitive["material"] == 0
    assert destination.read_bytes()[:4] == b"glTF"


def test_save_glb_rejects_simplified_mesh_without_source_triangle_ids(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source)
    mesh = pv.Plane().triangulate()
    document = ModelDocument(
        source,
        (ModelPart("Reef", mesh, "mesh"),),
        material_source=source,
    )

    with pytest.raises(ValueError, match="complexity"):
        save_document(document, tmp_path / "edited.glb")


def test_save_edited_glb_embeds_external_texture_image(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source, external_image=True)
    (tmp_path / "reef.png").write_bytes(b"external PNG")
    mesh = pv.PolyData(
        np.asarray(((0, 0, 0), (1, 0, 0), (1, 1, 0)), dtype=float),
        faces=np.asarray((3, 0, 1, 2)),
    )
    mesh.cell_data[GLB_TRIANGLE_ID] = np.asarray((0,), dtype=np.int64)
    document = ModelDocument(
        source,
        (ModelPart("Reef", mesh, "mesh"),),
        material_source=source,
    )

    destination = save_document(document, tmp_path / "export" / "reef_edited.glb")

    gltf, binary = _read_glb(destination)
    image = gltf["images"][0]
    view = gltf["bufferViews"][image["bufferView"]]
    assert "uri" not in image
    assert image["mimeType"] == "image/png"
    assert bytes(binary[view["byteOffset"] : view["byteOffset"] + view["byteLength"]]) == (
        b"external PNG"
    )


def test_make_glb_self_contained_embeds_openmvs_sidecar(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source, external_image=True)
    (tmp_path / "reef.png").write_bytes(b"external PNG")

    destination = make_glb_self_contained(source, tmp_path / "web" / "model.glb")

    gltf, binary = _read_glb(destination)
    image = gltf["images"][0]
    view = gltf["bufferViews"][image["bufferView"]]
    assert "uri" not in image
    assert bytes(binary[view["byteOffset"] : view["byteOffset"] + view["byteLength"]]) == (
        b"external PNG"
    )


def test_make_compact_glb_recompresses_texture_below_limit(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source, external_image=True)
    pixels = np.random.default_rng(42).integers(0, 256, (128, 128, 3), dtype=np.uint8)
    image_data = BytesIO()
    Image.fromarray(pixels).save(image_data, format="PNG")
    (tmp_path / "reef.png").write_bytes(image_data.getvalue())

    destination = make_compact_glb(
        source,
        tmp_path / "web" / "model.glb",
        max_bytes=20_000,
    )

    assert destination.stat().st_size < 20_000
    gltf, _ = _read_glb(destination)
    assert gltf["images"][0]["mimeType"] == "image/jpeg"


def test_make_compact_glb_embeds_external_index_buffer(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source)
    gltf, binary = _read_glb(source)
    index_view = gltf["bufferViews"][2]
    start = int(index_view["byteOffset"])
    end = start + int(index_view["byteLength"])
    external_indices = bytes(binary[start:end])
    (tmp_path / "reef-indices.bin").write_bytes(external_indices)
    gltf["buffers"].append(
        {"byteLength": len(external_indices), "uri": "reef-indices.bin"}
    )
    index_view["buffer"] = 1
    index_view["byteOffset"] = 0
    source.write_bytes(_build_glb(gltf, binary))

    destination = make_compact_glb(source, tmp_path / "web" / "model.glb")

    compact_gltf, compact_binary = _read_glb(destination)
    compact_view = compact_gltf["bufferViews"][2]
    primitive = compact_gltf["meshes"][0]["primitives"][0]
    indices, _ = _primitive_indices(primitive, compact_gltf, compact_binary)
    assert len(compact_gltf["buffers"]) == 1
    assert "uri" not in compact_gltf["buffers"][0]
    assert compact_view["buffer"] == 0
    assert indices.tolist() == [0, 1, 2, 0, 2, 3]


def test_source_fixture_has_expected_glb_length(tmp_path: Path) -> None:
    source = tmp_path / "reef.glb"
    source_glb(source)
    payload = source.read_bytes()
    assert struct.unpack_from("<I", payload, 8)[0] == len(payload)

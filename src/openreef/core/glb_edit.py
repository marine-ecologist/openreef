"""Write triangle-subset GLBs while retaining their embedded materials and images."""

from __future__ import annotations

import base64
import copy
import json
import mimetypes
import struct
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import unquote, unquote_to_bytes, urlparse

import numpy as np
from PIL import Image

from openreef.core.model import ModelDocument

GLB_TRIANGLE_ID = "__openreef_glb_triangle_id"
WEB_COMPACT_TARGET = 95 * 1024 * 1024

_COMPONENT_DTYPES = {
    5121: np.dtype("<u1"),
    5123: np.dtype("<u2"),
    5125: np.dtype("<u4"),
}


def save_textured_glb(document: ModelDocument, path: str | Path) -> Path:
    """Save retained source triangles while copying the original GLB payload."""
    source = document.material_source
    if source is None or source.suffix.lower() != ".glb":
        raise ValueError("A textured GLB source is required")
    source = source.expanduser().resolve()
    destination = Path(path).expanduser().resolve()
    if destination.suffix.lower() != ".glb":
        raise ValueError("Edited textured models must be saved as GLB")

    retained = _retained_triangle_ids(document)
    gltf, binary = _read_glb(source)
    _embed_external_buffers(gltf, binary, source.parent)
    _embed_external_images(gltf, binary, source.parent)
    _replace_primitive_indices(gltf, binary, retained)
    payload = _build_glb(gltf, binary)
    return _write_atomic(destination, payload)


def make_glb_self_contained(source: str | Path, path: str | Path) -> Path:
    """Copy a GLB while embedding any URI-based local texture images."""
    source_path = Path(source).expanduser().resolve()
    destination = Path(path).expanduser().resolve()
    gltf, binary = _read_glb(source_path)
    _embed_external_buffers(gltf, binary, source_path.parent)
    _embed_external_images(gltf, binary, source_path.parent)
    buffers = gltf.setdefault("buffers", [{}])
    if not buffers or buffers[0].get("uri"):
        raise ValueError("The GLB must use its embedded binary buffer")
    buffers[0]["byteLength"] = len(binary)
    return _write_atomic(destination, _build_glb(gltf, binary))


def make_compact_glb(
    source: str | Path,
    path: str | Path,
    *,
    max_bytes: int = WEB_COMPACT_TARGET,
) -> Path:
    """Write a self-contained GLB below a byte ceiling by compressing textures."""
    if max_bytes <= 0:
        raise ValueError("The compact GLB size limit must be positive")
    source_path = Path(source).expanduser().resolve()
    destination = Path(path).expanduser().resolve()
    gltf, binary = _read_glb(source_path)
    _embed_external_buffers(gltf, binary, source_path.parent)
    _embed_external_images(gltf, binary, source_path.parent)
    payload = _build_glb(gltf, binary)
    if len(payload) <= max_bytes:
        return _write_atomic(destination, payload)

    presets = (
        (8192, 86),
        (6144, 82),
        (4096, 82),
        (4096, 72),
        (3072, 72),
        (2048, 72),
        (1536, 68),
        (1024, 64),
    )
    smallest_size = len(payload)
    for maximum_dimension, quality in presets:
        candidate_gltf = copy.deepcopy(gltf)
        replacements = _compress_glb_images(
            candidate_gltf,
            binary,
            maximum_dimension=maximum_dimension,
            quality=quality,
        )
        if not replacements:
            continue
        candidate_binary = _repack_buffer_views(candidate_gltf, binary, replacements)
        candidate = _build_glb(candidate_gltf, candidate_binary)
        smallest_size = min(smallest_size, len(candidate))
        print(
            "OPENREEF_PHASE\t"
            f"Compact texture {maximum_dimension}px / quality {quality}: "
            f"{len(candidate) / (1024 * 1024):.1f} MiB",
            flush=True,
        )
        if len(candidate) <= max_bytes:
            return _write_atomic(destination, candidate)

    raise ValueError(
        "Could not compact this GLB below "
        f"{max_bytes / (1024 * 1024):.0f} MiB (smallest was "
        f"{smallest_size / (1024 * 1024):.1f} MiB). Use a lower-resolution "
        "textured mesh and try again."
    )


def _compress_glb_images(
    gltf: dict[str, Any],
    binary: bytearray,
    *,
    maximum_dimension: int,
    quality: int,
) -> dict[int, bytes]:
    replacements: dict[int, bytes] = {}
    for image in gltf.get("images", []):
        view_index = image.get("bufferView")
        if view_index is None:
            continue
        view = gltf["bufferViews"][int(view_index)]
        offset = int(view.get("byteOffset", 0))
        length = int(view["byteLength"])
        original = bytes(binary[offset : offset + length])
        try:
            with Image.open(BytesIO(original)) as texture:
                texture.load()
                texture.thumbnail(
                    (maximum_dimension, maximum_dimension),
                    Image.Resampling.LANCZOS,
                )
                output = BytesIO()
                has_alpha = texture.mode in {"RGBA", "LA"} and (
                    texture.getchannel("A").getextrema()[0] < 255
                )
                if has_alpha:
                    texture.save(output, format="PNG", optimize=True, compress_level=9)
                    mime_type = "image/png"
                else:
                    texture.convert("RGB").save(
                        output,
                        format="JPEG",
                        quality=quality,
                        optimize=True,
                        progressive=True,
                    )
                    mime_type = "image/jpeg"
        except (OSError, ValueError):
            continue
        compact = output.getvalue()
        if len(compact) >= len(original):
            continue
        replacements[int(view_index)] = compact
        image["mimeType"] = mime_type
    return replacements


def _repack_buffer_views(
    gltf: dict[str, Any],
    binary: bytearray,
    replacements: dict[int, bytes],
) -> bytearray:
    packed = bytearray()
    for index, view in enumerate(gltf.get("bufferViews", [])):
        if int(view.get("buffer", 0)) != 0:
            raise ValueError("Compact GLB export supports one embedded buffer")
        offset = int(view.get("byteOffset", 0))
        length = int(view["byteLength"])
        chunk = replacements.get(index, bytes(binary[offset : offset + length]))
        while len(packed) % 4:
            packed.append(0)
        view["byteOffset"] = len(packed)
        view["byteLength"] = len(chunk)
        packed.extend(chunk)
    buffers = gltf.setdefault("buffers", [{}])
    if not buffers or buffers[0].get("uri"):
        raise ValueError("The GLB must use its embedded binary buffer")
    buffers[0]["byteLength"] = len(packed)
    return packed


def _write_atomic(destination: Path, payload: bytes) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.openreef-tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _retained_triangle_ids(document: ModelDocument) -> np.ndarray:
    values: list[np.ndarray] = []
    for part in document.parts:
        if part.kind != "mesh":
            continue
        cell_data = part.dataset.cell_data
        if GLB_TRIANGLE_ID not in cell_data:
            raise ValueError(
                "This textured model has been remeshed or simplified. Set mesh complexity "
                "to 100% and apply only lasso edits before saving it as GLB."
            )
        ids = np.asarray(cell_data[GLB_TRIANGLE_ID], dtype=np.int64).reshape(-1)
        if len(ids) != int(part.dataset.n_cells):
            raise ValueError("The GLB triangle mapping is incomplete")
        values.append(ids)
    if not values:
        raise ValueError("The edited GLB contains no mesh triangles")
    retained = np.concatenate(values)
    if len(np.unique(retained)) != len(retained) or np.any(retained < 0):
        raise ValueError("The GLB triangle mapping is invalid")
    return np.sort(retained)


def _read_glb(path: Path) -> tuple[dict[str, Any], bytearray]:
    payload = path.read_bytes()
    if len(payload) < 20:
        raise ValueError(f"Invalid GLB file: {path.name}")
    magic, version, declared_length = struct.unpack_from("<4sII", payload)
    if magic != b"glTF" or version != 2 or declared_length != len(payload):
        raise ValueError(f"Unsupported or damaged GLB file: {path.name}")

    json_chunk: bytes | None = None
    binary_chunk: bytes | None = None
    offset = 12
    while offset + 8 <= len(payload):
        length, chunk_type = struct.unpack_from("<I4s", payload, offset)
        offset += 8
        chunk = payload[offset : offset + length]
        offset += length
        if len(chunk) != length:
            raise ValueError(f"Truncated GLB file: {path.name}")
        if chunk_type == b"JSON":
            json_chunk = chunk
        elif chunk_type == b"BIN\x00":
            binary_chunk = chunk
    if json_chunk is None or binary_chunk is None:
        raise ValueError("The GLB must contain JSON and embedded binary data")
    try:
        gltf = json.loads(json_chunk.rstrip(b" \t\r\n\x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid GLB metadata: {exc}") from exc
    return gltf, bytearray(binary_chunk)


def _embed_external_images(
    gltf: dict[str, Any],
    binary: bytearray,
    source_folder: Path,
) -> None:
    """Move URI-based texture images into the edited GLB binary buffer."""
    buffer_views = gltf.setdefault("bufferViews", [])
    for image in gltf.get("images", []):
        uri = image.get("uri")
        if not uri:
            continue
        payload, mime_type = _load_image_uri(str(uri), source_folder)
        while len(binary) % 4:
            binary.append(0)
        byte_offset = len(binary)
        binary.extend(payload)
        image.pop("uri", None)
        image["bufferView"] = len(buffer_views)
        image["mimeType"] = image.get("mimeType") or mime_type
        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(payload),
            }
        )


def _embed_external_buffers(
    gltf: dict[str, Any],
    binary: bytearray,
    source_folder: Path,
) -> None:
    """Merge local/data URI buffers into the GLB binary chunk and remap views."""
    buffers = gltf.get("buffers", [])
    if not buffers:
        gltf["buffers"] = [{"byteLength": len(binary)}]
        return

    first_is_embedded = not buffers[0].get("uri")
    packed = bytearray(binary if first_is_embedded else b"")
    offsets: dict[int, int] = {0: 0} if first_is_embedded else {}

    for index, descriptor in enumerate(buffers):
        uri = descriptor.get("uri")
        if not uri:
            if index == 0 and first_is_embedded:
                if int(descriptor.get("byteLength", 0)) > len(binary):
                    raise ValueError("The embedded GLB buffer is truncated")
                continue
            raise ValueError("A secondary GLB buffer is missing its URI")
        payload = _load_buffer_uri(str(uri), source_folder)
        declared = int(descriptor.get("byteLength", len(payload)))
        if declared > len(payload):
            raise ValueError(f"External GLB buffer is truncated: {_uri_name(str(uri))}")
        while len(packed) % 4:
            packed.append(0)
        offsets[index] = len(packed)
        packed.extend(payload)

    for view in gltf.get("bufferViews", []):
        source_index = int(view.get("buffer", 0))
        if source_index not in offsets:
            raise ValueError(f"GLB buffer view refers to missing buffer {source_index}")
        view["byteOffset"] = offsets[source_index] + int(view.get("byteOffset", 0))
        view["buffer"] = 0

    binary[:] = packed
    gltf["buffers"] = [{"byteLength": len(binary)}]


def _load_buffer_uri(uri: str, source_folder: Path) -> bytes:
    if uri.startswith("data:"):
        try:
            header, encoded = uri.split(",", 1)
            return (
                base64.b64decode(encoded, validate=True)
                if ";base64" in header
                else unquote_to_bytes(encoded)
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("The GLB contains an invalid buffer data URI") from exc

    parsed = urlparse(uri)
    if parsed.scheme or parsed.netloc:
        raise ValueError("Remote GLB geometry buffers cannot be embedded")
    buffer_path = (source_folder / unquote(parsed.path)).resolve()
    if not buffer_path.is_file():
        raise ValueError(f"External GLB buffer is missing: {buffer_path.name}")
    return buffer_path.read_bytes()


def _uri_name(uri: str) -> str:
    parsed = urlparse(uri)
    return Path(unquote(parsed.path)).name or "unnamed buffer"


def _load_image_uri(uri: str, source_folder: Path) -> tuple[bytes, str]:
    if uri.startswith("data:"):
        try:
            header, encoded = uri.split(",", 1)
        except ValueError as exc:
            raise ValueError("The GLB contains an invalid image data URI") from exc
        mime_type = header[5:].split(";", 1)[0] or "application/octet-stream"
        try:
            payload = (
                base64.b64decode(encoded, validate=True)
                if ";base64" in header
                else unquote_to_bytes(encoded)
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("The GLB contains an invalid embedded image") from exc
        return payload, mime_type

    parsed = urlparse(uri)
    if parsed.scheme or parsed.netloc:
        raise ValueError("Remote GLB texture images cannot be embedded")
    image_path = (source_folder / unquote(parsed.path)).resolve()
    if not image_path.is_file():
        raise ValueError(f"Texture image is missing: {image_path.name}")
    mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    return image_path.read_bytes(), mime_type


def _replace_primitive_indices(
    gltf: dict[str, Any],
    binary: bytearray,
    retained: np.ndarray,
) -> None:
    meshes = gltf.get("meshes", [])
    accessors = gltf.setdefault("accessors", [])
    buffer_views = gltf.setdefault("bufferViews", [])
    descriptors: list[tuple[dict[str, Any], np.ndarray, int]] = []
    triangle_offset = 0

    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            if int(primitive.get("mode", 4)) != 4:
                raise ValueError("Edited GLB saving currently supports triangle meshes only")
            indices, component_type = _primitive_indices(
                primitive,
                gltf,
                binary,
            )
            if len(indices) % 3:
                raise ValueError("The source GLB contains an incomplete triangle primitive")
            triangle_count = len(indices) // 3
            descriptors.append((primitive, indices.reshape(-1, 3), component_type))
            triangle_offset += triangle_count

    if not descriptors:
        raise ValueError("The source GLB contains no triangle primitives")
    if retained[-1] >= triangle_offset:
        raise ValueError("Edited triangles do not match the source GLB")

    global_offset = 0
    retained_set = set(int(value) for value in retained)
    for primitive, triangles, component_type in descriptors:
        selected_rows = [
            index
            for index in range(len(triangles))
            if global_offset + index in retained_set
        ]
        global_offset += len(triangles)
        if not selected_rows:
            primitive["extras"] = {
                **primitive.get("extras", {}),
                "openreefHidden": True,
            }
            selected = np.asarray((0, 0, 0), dtype=_COMPONENT_DTYPES[component_type])
        else:
            primitive.get("extras", {}).pop("openreefHidden", None)
            selected = np.asarray(triangles[selected_rows], dtype=_COMPONENT_DTYPES[component_type])
            selected = selected.reshape(-1)

        while len(binary) % 4:
            binary.append(0)
        byte_offset = len(binary)
        index_bytes = selected.tobytes()
        binary.extend(index_bytes)
        view_index = len(buffer_views)
        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(index_bytes),
                "target": 34963,
            }
        )
        accessor_index = len(accessors)
        accessors.append(
            {
                "bufferView": view_index,
                "byteOffset": 0,
                "componentType": component_type,
                "count": int(len(selected)),
                "type": "SCALAR",
                "min": [int(selected.min())],
                "max": [int(selected.max())],
            }
        )
        primitive["indices"] = accessor_index

    buffers = gltf.setdefault("buffers", [{}])
    if not buffers or buffers[0].get("uri"):
        raise ValueError("The GLB must use its embedded binary buffer")
    buffers[0]["byteLength"] = len(binary)


def _primitive_indices(
    primitive: dict[str, Any],
    gltf: dict[str, Any],
    binary: bytearray,
) -> tuple[np.ndarray, int]:
    accessor_index = primitive.get("indices")
    if accessor_index is None:
        position_index = primitive.get("attributes", {}).get("POSITION")
        if position_index is None:
            raise ValueError("A GLB primitive is missing positions")
        count = int(gltf["accessors"][position_index]["count"])
        component_type = 5123 if count <= np.iinfo(np.uint16).max else 5125
        return np.arange(count, dtype=_COMPONENT_DTYPES[component_type]), component_type

    accessor = gltf["accessors"][accessor_index]
    if accessor.get("type") != "SCALAR" or accessor.get("sparse"):
        raise ValueError("Unsupported GLB index accessor")
    component_type = int(accessor["componentType"])
    dtype = _COMPONENT_DTYPES.get(component_type)
    if dtype is None:
        raise ValueError(f"Unsupported GLB index type: {component_type}")
    view = gltf["bufferViews"][accessor["bufferView"]]
    if int(view.get("buffer", 0)) != 0:
        raise ValueError("External GLB index buffers are not supported")
    offset = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    count = int(accessor["count"])
    end = offset + count * dtype.itemsize
    if offset < 0 or end > len(binary):
        raise ValueError("The GLB index buffer is out of bounds")
    return np.frombuffer(binary, dtype=dtype, count=count, offset=offset).copy(), component_type


def _build_glb(gltf: dict[str, Any], binary: bytearray) -> bytes:
    json_payload = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_payload += b" " * (-len(json_payload) % 4)
    binary_length = len(binary)
    binary_payload = bytes(binary) + b"\x00" * (-binary_length % 4)
    total = 12 + 8 + len(json_payload) + 8 + len(binary_payload)
    return b"".join(
        (
            struct.pack("<4sII", b"glTF", 2, total),
            struct.pack("<I4s", len(json_payload), b"JSON"),
            json_payload,
            struct.pack("<I4s", len(binary_payload), b"BIN\x00"),
            binary_payload,
        )
    )

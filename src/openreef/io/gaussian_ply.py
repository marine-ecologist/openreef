"""Minimal OpenSplat PLY reader that retains Gaussian-specific attributes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyvista as pv

from openreef.core.model import ModelDocument, ModelPart

GAUSSIAN_PROPERTIES = frozenset(
    {
        "x",
        "y",
        "z",
        "f_dc_0",
        "f_dc_1",
        "f_dc_2",
        "opacity",
        "scale_0",
        "scale_1",
        "scale_2",
        "rot_0",
        "rot_1",
        "rot_2",
        "rot_3",
    }
)

_NUMPY_TYPES = {
    "char": "i1",
    "int8": "i1",
    "uchar": "u1",
    "uint8": "u1",
    "short": "i2",
    "int16": "i2",
    "ushort": "u2",
    "uint16": "u2",
    "int": "i4",
    "int32": "i4",
    "uint": "u4",
    "uint32": "u4",
    "float": "f4",
    "float32": "f4",
    "double": "f8",
    "float64": "f8",
}


@dataclass(frozen=True)
class PlyVertexHeader:
    format: str
    count: int
    properties: tuple[tuple[str, str], ...]
    data_offset: int
    has_list_properties: bool = False


@dataclass(frozen=True)
class SplatCleanupResult:
    """Result of a non-destructive Gaussian cleanup preview."""

    document: ModelDocument
    retained: int
    removed: int


def read_gaussian_ply(path: Path) -> pv.PolyData | None:
    """Read an OpenSplat PLY, or return ``None`` for an ordinary PLY."""
    header = _read_vertex_header(path)
    names = {name for _, name in header.properties}
    if not GAUSSIAN_PROPERTIES.issubset(names):
        return None
    if header.has_list_properties:
        raise ValueError("List properties are not supported in Gaussian vertices")
    if any(kind not in _NUMPY_TYPES for kind, _ in header.properties):
        raise ValueError("Gaussian PLY contains an unsupported vertex property type")

    byte_order = "<" if header.format == "binary_little_endian" else ">"
    dtype = np.dtype(
        [(name, byte_order + _NUMPY_TYPES[kind]) for kind, name in header.properties]
    )
    if header.format in {"binary_little_endian", "binary_big_endian"}:
        with path.open("rb") as stream:
            stream.seek(header.data_offset)
            raw = stream.read(dtype.itemsize * header.count)
        if len(raw) != dtype.itemsize * header.count:
            raise ValueError("Gaussian PLY ended before all splats were read")
        records = np.frombuffer(raw, dtype=dtype, count=header.count)
    elif header.format == "ascii":
        rows = np.loadtxt(path, skiprows=_header_line_count(path), max_rows=header.count)
        rows = np.atleast_2d(rows)
        if rows.shape != (header.count, len(header.properties)):
            raise ValueError("Gaussian PLY vertex table has an unexpected shape")
        records = np.empty(header.count, dtype=dtype)
        for index, (_, name) in enumerate(header.properties):
            records[name] = rows[:, index]
    else:
        raise ValueError(f"Unsupported Gaussian PLY format: {header.format}")

    points = np.column_stack((records["x"], records["y"], records["z"]))
    dataset = pv.PolyData(points)
    for _, name in header.properties:
        if name not in {"x", "y", "z"}:
            dataset.point_data[name] = np.asarray(records[name])
    return dataset


def clean_gaussian_document(
    document: ModelDocument,
    *,
    minimum_opacity: float = 0.02,
    maximum_scale_percentile: float = 99.0,
    maximum_aspect_ratio: float | None = 50.0,
    bounds: tuple[float, float, float, float, float, float] | None = None,
) -> SplatCleanupResult:
    """Remove faint, oversized, stretched, or out-of-ROI splats non-destructively."""
    if len(document.parts) != 1:
        raise ValueError("Gaussian cleanup expects one splat part")
    part = document.parts[0]
    dataset = part.dataset
    names = set(dataset.point_data.keys())
    if not (GAUSSIAN_PROPERTIES - {"x", "y", "z"}).issubset(names):
        raise ValueError("The selected model is not an OpenSplat Gaussian PLY")

    points = np.asarray(dataset.points)
    total = len(points)
    mask = np.ones(total, dtype=bool)

    logits = np.asarray(dataset.point_data["opacity"], dtype=float)
    opacity = np.empty_like(logits)
    positive = logits >= 0
    opacity[positive] = 1.0 / (1.0 + np.exp(-logits[positive]))
    exp_logits = np.exp(logits[~positive])
    opacity[~positive] = exp_logits / (1.0 + exp_logits)
    mask &= opacity >= max(0.0, min(float(minimum_opacity), 1.0))

    scale_log = np.column_stack(
        [np.asarray(dataset.point_data[f"scale_{index}"], dtype=float) for index in range(3)]
    )
    maximum_scale = np.max(scale_log, axis=1)
    percentile = max(90.0, min(float(maximum_scale_percentile), 100.0))
    if percentile < 100.0 and total:
        mask &= maximum_scale <= np.percentile(maximum_scale, percentile)
    if maximum_aspect_ratio is not None:
        # Gaussian axes are stored as logarithmic scales. Comparing their log
        # range avoids exponent overflow and catches the needle-like ellipsoids
        # that render as long rays or halos around a reconstruction.
        aspect_limit = max(1.0, float(maximum_aspect_ratio))
        mask &= np.ptp(scale_log, axis=1) <= np.log(aspect_limit)

    if bounds is not None:
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        mask &= (
            (points[:, 0] >= xmin)
            & (points[:, 0] <= xmax)
            & (points[:, 1] >= ymin)
            & (points[:, 1] <= ymax)
            & (points[:, 2] >= zmin)
            & (points[:, 2] <= zmax)
        )

    cleaned = pv.PolyData(points[mask])
    for name in dataset.point_data.keys():
        cleaned.point_data[name] = np.asarray(dataset.point_data[name])[mask]
    cleaned_document = ModelDocument(
        source=document.source,
        parts=(ModelPart(part.name, cleaned, part.kind, part.vertex_color),),
    )
    retained = int(np.count_nonzero(mask))
    return SplatCleanupResult(cleaned_document, retained, total - retained)


def write_gaussian_ply(document: ModelDocument, path: str | Path) -> Path:
    """Write a Gaussian document as a binary PLY while retaining every attribute."""
    if len(document.parts) != 1:
        raise ValueError("Gaussian PLY export expects one splat part")
    dataset = document.parts[0].dataset
    names = tuple(str(name) for name in dataset.point_data.keys())
    required = GAUSSIAN_PROPERTIES - {"x", "y", "z"}
    if not required.issubset(names):
        raise ValueError("The selected model is not an OpenSplat Gaussian PLY")
    if any(" " in name or not name.isascii() for name in names):
        raise ValueError("Gaussian property names must be plain ASCII words")

    points = np.asarray(dataset.points, dtype=np.float32)
    count = len(points)
    arrays: dict[str, np.ndarray] = {
        "x": points[:, 0],
        "y": points[:, 1],
        "z": points[:, 2],
    }
    for name in names:
        array = np.asarray(dataset.point_data[name])
        if array.ndim != 1 or len(array) != count:
            raise ValueError(f"Gaussian property {name!r} is not a scalar vertex attribute")
        arrays[name] = array

    properties: list[tuple[str, str, np.dtype]] = []
    for name, array in arrays.items():
        ply_type, dtype = _writable_type(np.asarray(array).dtype)
        properties.append((ply_type, name, dtype))
    records = np.empty(count, dtype=[(name, dtype) for _, name, dtype in properties])
    for _, name, dtype in properties:
        records[name] = np.asarray(arrays[name], dtype=dtype)

    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    header = "\n".join(
        (
            "ply",
            "format binary_little_endian 1.0",
            "comment OpenReef Gaussian splat export",
            f"element vertex {count}",
            *(f"property {kind} {name}" for kind, name, _ in properties),
            "end_header",
            "",
        )
    ).encode("ascii")
    with destination.open("wb") as stream:
        stream.write(header)
        stream.write(records.tobytes())
    return destination


def _writable_type(dtype: np.dtype) -> tuple[str, np.dtype]:
    """Return a portable little-endian PLY scalar type for a NumPy dtype."""
    kind = dtype.kind
    if kind == "f":
        return ("double", np.dtype("<f8")) if dtype.itemsize > 4 else ("float", np.dtype("<f4"))
    if kind == "u":
        if dtype.itemsize == 1:
            return "uchar", np.dtype("u1")
        if dtype.itemsize == 2:
            return "ushort", np.dtype("<u2")
        return "uint", np.dtype("<u4")
    if kind in {"i", "b"}:
        if dtype.itemsize == 1:
            return "char", np.dtype("i1")
        if dtype.itemsize == 2:
            return "short", np.dtype("<i2")
        return "int", np.dtype("<i4")
    raise ValueError(f"Unsupported Gaussian property dtype: {dtype}")


def _read_vertex_header(path: Path) -> PlyVertexHeader:
    file_format = ""
    vertex_count = 0
    properties: list[tuple[str, str]] = []
    has_list_properties = False
    current_element = ""
    with path.open("rb") as stream:
        if stream.readline().strip() != b"ply":
            raise ValueError("Not a PLY file")
        while True:
            line = stream.readline()
            if not line:
                raise ValueError("PLY header has no end_header marker")
            try:
                text = line.decode("ascii").strip()
            except UnicodeDecodeError as exc:
                raise ValueError("PLY header is not ASCII") from exc
            fields = text.split()
            if fields[:1] == ["format"] and len(fields) >= 2:
                file_format = fields[1]
            elif fields[:1] == ["element"] and len(fields) == 3:
                current_element = fields[1]
                if current_element == "vertex":
                    vertex_count = int(fields[2])
            elif fields[:1] == ["property"] and current_element == "vertex":
                if fields[1:2] == ["list"]:
                    has_list_properties = True
                elif len(fields) != 3:
                    raise ValueError("PLY vertex property is malformed")
                else:
                    properties.append((fields[1], fields[2]))
            elif text == "end_header":
                return PlyVertexHeader(
                    file_format,
                    vertex_count,
                    tuple(properties),
                    stream.tell(),
                    has_list_properties,
                )


def _header_line_count(path: Path) -> int:
    with path.open("rb") as stream:
        for count, line in enumerate(stream, start=1):
            if line.strip() == b"end_header":
                return count
    raise ValueError("PLY header has no end_header marker")

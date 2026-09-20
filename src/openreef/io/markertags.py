"""Detect temporary AprilTag scale markers and metric-scale COLMAP models.

MarkerTags are non-permanent field markers.  Their encoded square is the scale
reference; the surrounding handling disc is deliberately ignored.
"""

from __future__ import annotations

import json
import math
import shutil
import struct
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np

IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
APRILTAG_DICTIONARIES = {
    "tag16h5": "DICT_APRILTAG_16h5",
    "tag25h9": "DICT_APRILTAG_25h9",
    "tag36h10": "DICT_APRILTAG_36h10",
    "tag36h11": "DICT_APRILTAG_36h11",
}
COLMAP_CAMERA_MODELS: dict[int, tuple[str, int]] = {
    0: ("SIMPLE_PINHOLE", 3),
    1: ("PINHOLE", 4),
    2: ("SIMPLE_RADIAL", 4),
    3: ("RADIAL", 5),
    4: ("OPENCV", 8),
    5: ("OPENCV_FISHEYE", 8),
    6: ("FULL_OPENCV", 12),
    7: ("FOV", 5),
    8: ("SIMPLE_RADIAL_FISHEYE", 4),
    9: ("RADIAL_FISHEYE", 5),
    10: ("THIN_PRISM_FISHEYE", 12),
}


@dataclass(frozen=True)
class ColmapCamera:
    camera_id: int
    model_id: int
    model: str
    width: int
    height: int
    params: tuple[float, ...]


@dataclass(frozen=True)
class RegisteredImage:
    image_id: int
    camera_id: int
    name: str
    quaternion: tuple[float, float, float, float]
    translation: tuple[float, float, float]

    @property
    def rotation(self) -> np.ndarray:
        return quaternion_rotation(np.asarray(self.quaternion, dtype=float))

    @property
    def center(self) -> np.ndarray:
        rotation = self.rotation
        return -rotation.T @ np.asarray(self.translation, dtype=float)


@dataclass
class Detection:
    tag_id: int
    image: str
    corners: np.ndarray
    center: np.ndarray
    image_id: int | None = None
    camera_id: int | None = None
    registered: bool = False


@dataclass(frozen=True)
class RayObservation:
    detection: Detection
    point: np.ndarray
    normalized: np.ndarray
    projection: np.ndarray
    camera_center: np.ndarray
    focal_pixels: float


def read_cameras_binary(path: str | Path) -> dict[int, ColmapCamera]:
    cameras: dict[int, ColmapCamera] = {}
    with Path(path).open("rb") as stream:
        (count,) = _read(stream, "<Q")
        for _ in range(count):
            camera_id, model_id, width, height = _read(stream, "<iiQQ")
            try:
                model, parameter_count = COLMAP_CAMERA_MODELS[int(model_id)]
            except KeyError as exc:
                raise ValueError(f"Unsupported COLMAP camera model id: {model_id}") from exc
            params = tuple(float(value) for value in _read(stream, f"<{parameter_count}d"))
            cameras[int(camera_id)] = ColmapCamera(
                int(camera_id), int(model_id), model, int(width), int(height), params
            )
    return cameras


def read_registered_images(path: str | Path) -> dict[str, RegisteredImage]:
    images: dict[str, RegisteredImage] = {}
    with Path(path).open("rb") as stream:
        (count,) = _read(stream, "<Q")
        for _ in range(count):
            values = _read(stream, "<i7di")
            name = _read_c_string(stream)
            (point_count,) = _read(stream, "<Q")
            stream.seek(int(point_count) * 24, 1)
            image = RegisteredImage(
                image_id=int(values[0]),
                quaternion=tuple(float(value) for value in values[1:5]),
                translation=tuple(float(value) for value in values[5:8]),
                camera_id=int(values[8]),
                name=name,
            )
            images[Path(name).as_posix()] = image
    return images


def detect_markertags(images: str | Path, family: str = "tag36h11") -> list[Detection]:
    """Scan source images with OpenCV's AprilTag detector."""
    import cv2

    aruco = getattr(cv2, "aruco", None)
    if aruco is None:
        raise RuntimeError(
            "MarkerTag detection needs OpenCV's aruco module; install "
            "opencv-contrib-python-headless."
        )
    constant_name = APRILTAG_DICTIONARIES.get(family.lower())
    if constant_name is None or not hasattr(aruco, constant_name):
        raise ValueError(f"Unsupported AprilTag family: {family}")
    dictionary = aruco.getPredefinedDictionary(getattr(aruco, constant_name))
    parameters = aruco.DetectorParameters()
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
    # MarkerTags may be manufactured as black relief on a white face or with
    # the inverse relief/pigment arrangement. Accept both valid polarities.
    parameters.detectInvertedMarker = True
    detector = (
        aruco.ArucoDetector(dictionary, parameters)
        if hasattr(aruco, "ArucoDetector")
        else None
    )

    root = Path(images)
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    detections: list[Detection] = []
    for path in paths:
        gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue
        if detector is not None:
            corners, ids, _ = detector.detectMarkers(gray)
        else:  # OpenCV 4.6 compatibility
            corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=parameters)
        if ids is None:
            continue
        relative = path.relative_to(root).as_posix()
        for marker_corners, tag_id in zip(corners, ids.reshape(-1), strict=True):
            points = np.asarray(marker_corners, dtype=float).reshape(4, 2)
            detections.append(
                Detection(
                    tag_id=int(tag_id),
                    image=relative,
                    corners=points,
                    center=points.mean(axis=0),
                )
            )
    return detections


def associate_registered_images(
    detections: list[Detection], registered: dict[str, RegisteredImage]
) -> None:
    """Attach COLMAP image/camera ids to detections, tolerating path separators."""
    by_basename: dict[str, list[RegisteredImage]] = defaultdict(list)
    for image in registered.values():
        by_basename[Path(image.name).name].append(image)
    for detection in detections:
        image = registered.get(Path(detection.image).as_posix())
        if image is None:
            matches = by_basename.get(Path(detection.image).name, [])
            image = matches[0] if len(matches) == 1 else None
        if image is not None:
            detection.image_id = image.image_id
            detection.camera_id = image.camera_id
            detection.registered = True


def reconstruct_tags(
    detections: list[Detection],
    cameras: dict[int, ColmapCamera],
    registered: dict[str, RegisteredImage],
    *,
    max_reprojection_error_px: float = 5.0,
) -> dict[int, dict[str, Any]]:
    """Triangulate canonical corners/centres from registered multi-view detections."""
    images_by_id = {image.image_id: image for image in registered.values()}
    by_tag: dict[int, list[Detection]] = defaultdict(list)
    for detection in detections:
        if detection.registered:
            by_tag[detection.tag_id].append(detection)

    reconstructed: dict[int, dict[str, Any]] = {}
    for tag_id, tag_detections in sorted(by_tag.items()):
        points_3d: list[np.ndarray | None] = []
        point_details: list[dict[str, Any] | None] = []
        for point_index in range(5):
            observations: list[RayObservation] = []
            for detection in tag_detections:
                if detection.image_id is None or detection.camera_id is None:
                    continue
                image = images_by_id.get(detection.image_id)
                camera = cameras.get(detection.camera_id)
                if image is None or camera is None:
                    continue
                pixel = detection.center if point_index == 4 else detection.corners[point_index]
                try:
                    normalized, focal = normalized_image_point(pixel, camera)
                except ValueError:
                    continue
                projection = np.column_stack(
                    (image.rotation, np.asarray(image.translation, dtype=float))
                )
                observations.append(
                    RayObservation(
                        detection,
                        np.asarray(pixel, dtype=float),
                        normalized,
                        projection,
                        image.center,
                        focal,
                    )
                )
            result = triangulate_robust(observations, max_reprojection_error_px)
            if result is None:
                points_3d.append(None)
                point_details.append(None)
            else:
                point, used, residual = result
                points_3d.append(point)
                point_details.append(
                    {
                        "observations": len(used),
                        "images": sorted({item.detection.image for item in used}),
                        "reprojection_rms_px": residual,
                    }
                )
        corners = points_3d[:4]
        center = points_3d[4]
        reconstructed[tag_id] = {
            "corners": corners,
            "center": center,
            "point_details": point_details,
            "registered_observations": len(tag_detections),
            "registered_images": sorted({item.image for item in tag_detections}),
        }
    return reconstructed


def normalized_image_point(
    pixel: np.ndarray, camera: ColmapCamera
) -> tuple[np.ndarray, float]:
    """Undistort a COLMAP pixel into normalized pinhole coordinates."""
    import cv2

    params = camera.params
    if camera.model == "SIMPLE_PINHOLE":
        f, cx, cy = params
        return np.asarray(((pixel[0] - cx) / f, (pixel[1] - cy) / f)), float(f)
    if camera.model == "PINHOLE":
        fx, fy, cx, cy = params
        return np.asarray(((pixel[0] - cx) / fx, (pixel[1] - cy) / fy)), (fx + fy) / 2

    if camera.model in {"SIMPLE_RADIAL", "RADIAL"}:
        f, cx, cy, *coefficients = params
        matrix = np.asarray(((f, 0, cx), (0, f, cy), (0, 0, 1)), dtype=float)
        distortion = np.zeros(5, dtype=float)
        distortion[: len(coefficients)] = coefficients
        value = cv2.undistortPoints(
            np.asarray(pixel, dtype=float).reshape(1, 1, 2), matrix, distortion
        )[0, 0]
        return value, float(f)
    if camera.model in {"OPENCV", "FULL_OPENCV", "THIN_PRISM_FISHEYE"}:
        fx, fy, cx, cy, *coefficients = params
        matrix = np.asarray(((fx, 0, cx), (0, fy, cy), (0, 0, 1)), dtype=float)
        value = cv2.undistortPoints(
            np.asarray(pixel, dtype=float).reshape(1, 1, 2),
            matrix,
            np.asarray(coefficients, dtype=float),
        )[0, 0]
        return value, (fx + fy) / 2
    if camera.model in {
        "OPENCV_FISHEYE",
        "SIMPLE_RADIAL_FISHEYE",
        "RADIAL_FISHEYE",
    }:
        if camera.model == "OPENCV_FISHEYE":
            fx, fy, cx, cy, *coefficients = params
        else:
            f, cx, cy, *coefficients = params
            fx = fy = f
        matrix = np.asarray(((fx, 0, cx), (0, fy, cy), (0, 0, 1)), dtype=float)
        distortion = np.zeros(4, dtype=float)
        distortion[: len(coefficients)] = coefficients
        value = cv2.fisheye.undistortPoints(
            np.asarray(pixel, dtype=float).reshape(1, 1, 2), matrix, distortion
        )[0, 0]
        return value, (fx + fy) / 2
    raise ValueError(f"MarkerTag triangulation does not support camera model {camera.model}")


def triangulate_robust(
    observations: list[RayObservation], max_error_px: float
) -> tuple[np.ndarray, list[RayObservation], float] | None:
    """Linear multi-view triangulation with reprojection and baseline rejection."""
    if len(observations) < 2:
        return None
    active = list(observations)
    while len(active) >= 2:
        rows: list[np.ndarray] = []
        for observation in active:
            x, y = observation.normalized
            projection = observation.projection
            rows.extend((x * projection[2] - projection[0], y * projection[2] - projection[1]))
        _, _, vh = np.linalg.svd(np.asarray(rows))
        homogeneous = vh[-1]
        if abs(float(homogeneous[3])) <= 1.0e-12:
            return None
        point = homogeneous[:3] / homogeneous[3]
        depths = [
            float((item.projection[:, :3] @ point + item.projection[:, 3])[2])
            for item in active
        ]
        if sum(depth > 0 for depth in depths) < 2:
            return None
        errors = []
        for item in active:
            camera_point = item.projection[:, :3] @ point + item.projection[:, 3]
            if camera_point[2] <= 1.0e-12:
                errors.append(float("inf"))
                continue
            projected = camera_point[:2] / camera_point[2]
            errors.append(float(np.linalg.norm(projected - item.normalized) * item.focal_pixels))
        worst = int(np.argmax(errors))
        if errors[worst] <= max_error_px:
            rays = [point - item.camera_center for item in active]
            directions = [ray / max(np.linalg.norm(ray), 1.0e-12) for ray in rays]
            max_angle = max(
                math.degrees(
                    math.acos(float(np.clip(np.dot(first, second), -1.0, 1.0)))
                )
                for index, first in enumerate(directions)
                for second in directions[index + 1 :]
            )
            if max_angle < 0.5:
                return None
            rms = math.sqrt(float(np.mean(np.square(errors))))
            return point, active, rms
        if len(active) == 2:
            return None
        active.pop(worst)
    return None


def estimate_metric_scale(
    reconstructed: dict[int, dict[str, Any]], tag_size_m: float
) -> dict[str, Any]:
    """Robustly aggregate reconstructed tag edges into one metres/unit scale."""
    measurements: list[dict[str, Any]] = []
    for tag_id, tag in reconstructed.items():
        corners = tag["corners"]
        for start, end in ((0, 1), (1, 2), (2, 3), (3, 0)):
            if corners[start] is None or corners[end] is None:
                continue
            length = float(np.linalg.norm(corners[start] - corners[end]))
            if not np.isfinite(length) or length <= 1.0e-12:
                continue
            measurements.append(
                {
                    "tag_id": tag_id,
                    "edge": [start, end],
                    "reconstructed_length": length,
                    "scale_candidate": tag_size_m / length,
                }
            )
    if len(measurements) < 2:
        return {
            "status": "insufficient_observations",
            "reason": "At least two reconstructed MarkerTag edges are required.",
            "measurements": measurements,
        }

    candidates = np.asarray([item["scale_candidate"] for item in measurements], dtype=float)
    median = float(np.median(candidates))
    deviations = np.abs(candidates - median)
    mad = float(np.median(deviations))
    tolerance = max(median * 0.10, 3.0 * 1.4826 * mad)
    inlier_mask = deviations <= tolerance
    inliers = [item for item, keep in zip(measurements, inlier_mask, strict=True) if keep]
    if len(inliers) < 2:
        return {
            "status": "rejected_inconsistent",
            "reason": "MarkerTag edge scale estimates did not agree.",
            "measurements": measurements,
        }
    scale = float(np.median([item["scale_candidate"] for item in inliers]))
    residuals = [item["reconstructed_length"] * scale - tag_size_m for item in inliers]
    residual_rms_m = math.sqrt(float(np.mean(np.square(residuals))))
    relative_rms = residual_rms_m / tag_size_m
    inlier_tag_ids = sorted({int(item["tag_id"]) for item in inliers})
    tag_scale_estimates = []
    for tag_id in inlier_tag_ids:
        estimates = [
            float(item["scale_candidate"])
            for item in inliers
            if int(item["tag_id"]) == tag_id
        ]
        tag_scale_estimates.append(
            {"tag_id": tag_id, "scale_factor": float(np.median(estimates))}
        )
    independent = np.asarray(
        [item["scale_factor"] for item in tag_scale_estimates], dtype=float
    )
    median_tag_scale = float(np.median(independent))
    scale_residual_pct = None
    if len(independent) >= 2 and median_tag_scale > 0:
        mad = float(np.median(np.abs(independent - median_tag_scale)))
        scale_residual_pct = 100.0 * 1.4826 * mad / median_tag_scale
    if relative_rms > 0.10:
        return {
            "status": "rejected_inconsistent",
            "reason": "MarkerTag edge residual exceeds 10% of the known edge length.",
            "measurements": measurements,
            "inlier_measurements": len(inliers),
            "scale_factor": scale,
            "residual_rms_m": residual_rms_m,
            "relative_residual": relative_rms,
            "tag_scale_estimates": tag_scale_estimates,
            "median_tag_scale": median_tag_scale,
            "scale_residual_pct": scale_residual_pct,
            "inlier_tag_ids": inlier_tag_ids,
        }
    return {
        "status": "scaled",
        "scale_factor": scale,
        "residual_rms_m": residual_rms_m,
        "relative_residual": relative_rms,
        "measurements": measurements,
        "inlier_measurements": len(inliers),
        "inlier_tags": len(inlier_tag_ids),
        "inlier_tag_ids": inlier_tag_ids,
        "tag_scale_estimates": tag_scale_estimates,
        "median_tag_scale": median_tag_scale,
        "scale_residual_pct": scale_residual_pct,
    }


def scale_colmap_model(source: Path, destination: Path, scale: float) -> None:
    """Create a metric COLMAP binary model without modifying the raw SfM result."""
    temporary = destination.with_name(f".{destination.name}.openreef-build")
    shutil.rmtree(temporary, ignore_errors=True)
    temporary.mkdir(parents=True)
    shutil.copy2(source / "cameras.bin", temporary / "cameras.bin")
    _scale_images_binary(source / "images.bin", temporary / "images.bin", scale)
    points = _scale_points_binary(source / "points3D.bin", temporary / "points3D.bin", scale)
    _write_points_ply(temporary / "points3D.ply", points)
    shutil.rmtree(destination, ignore_errors=True)
    temporary.replace(destination)


def _scale_images_binary(source: Path, destination: Path, scale: float) -> None:
    with source.open("rb") as input_stream, destination.open("wb") as output_stream:
        (count,) = _read(input_stream, "<Q")
        output_stream.write(struct.pack("<Q", count))
        for _ in range(count):
            values = list(_read(input_stream, "<i7di"))
            values[5:8] = [float(value) * scale for value in values[5:8]]
            output_stream.write(struct.pack("<i7di", *values))
            name = _read_c_string_bytes(input_stream)
            output_stream.write(name + b"\0")
            (point_count,) = _read(input_stream, "<Q")
            output_stream.write(struct.pack("<Q", point_count))
            payload = input_stream.read(int(point_count) * 24)
            if len(payload) != int(point_count) * 24:
                raise ValueError("Unexpected end of COLMAP images.bin")
            output_stream.write(payload)


def _scale_points_binary(
    source: Path, destination: Path, scale: float
) -> list[tuple[float, float, float, int, int, int]]:
    points: list[tuple[float, float, float, int, int, int]] = []
    with source.open("rb") as input_stream, destination.open("wb") as output_stream:
        (count,) = _read(input_stream, "<Q")
        output_stream.write(struct.pack("<Q", count))
        for _ in range(count):
            point_id, x, y, z, red, green, blue, error = _read(input_stream, "<Q3d3Bd")
            xyz = (x * scale, y * scale, z * scale)
            output_stream.write(
                struct.pack(
                    "<Q3d3Bd", point_id, *xyz, red, green, blue, error
                )
            )
            (track_count,) = _read(input_stream, "<Q")
            output_stream.write(struct.pack("<Q", track_count))
            track = input_stream.read(int(track_count) * 8)
            if len(track) != int(track_count) * 8:
                raise ValueError("Unexpected end of COLMAP points3D.bin")
            output_stream.write(track)
            points.append((*xyz, int(red), int(green), int(blue)))
    return points


def _write_points_ply(
    path: Path, points: list[tuple[float, float, float, int, int, int]]
) -> None:
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {len(points)}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n"
    ).encode("ascii")
    with path.open("wb") as stream:
        stream.write(header)
        for point in points:
            stream.write(struct.pack("<3f3B", *point))


def run_markertag_workflow(
    images: Path,
    sparse_model: Path,
    metric_model: Path,
    metadata_path: Path,
    *,
    family: str = "tag36h11",
    tag_size_m: float = 0.050,
) -> dict[str, Any]:
    """Detect, triangulate, validate, scale, and persist MarkerTag metadata."""
    from openreef.pipeline.stages import sparse_model_identity

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now().astimezone().isoformat()
    base: dict[str, Any] = {
        "version": 1,
        "marker_type": "MarkerTag",
        "purpose": "non-permanent scale marker",
        "family": family,
        "tag_edge_m": tag_size_m,
        "scale_metric": "AprilTag encoded-square edge",
        "excluded_from_scale": {
            "disc_diameter_m": 0.090,
            "disc_height_m": 0.008,
            "tag_face_relief_m": 0.0006,
        },
        "source_model": sparse_model_identity(sparse_model),
        "created_at": created_at,
    }
    try:
        detections = detect_markertags(images, family)
        detected_family = family
        if not detections:
            # A dataset can contain an older MarkerTag generation than the
            # project default. Probe the remaining supported AprilTag families
            # and retain the strongest result instead of reporting a false zero.
            alternatives = {
                candidate: detect_markertags(images, candidate)
                for candidate in APRILTAG_DICTIONARIES
                if candidate != family.lower()
            }
            detected_family, detections = max(
                alternatives.items(), key=lambda item: len(item[1]), default=(family, [])
            )
            if not detections:
                detected_family = family
        base["family"] = detected_family
        if detected_family != family:
            base["requested_family"] = family
        family = detected_family
    except (RuntimeError, ValueError) as exc:
        payload = dict(
            base,
            status="detection_unavailable",
            reason=str(exc),
            scaled=False,
            unique_tags=0,
            observations=0,
            detections=[],
            markertags={
                "detected": False,
                "family": family,
                "tag_size_m": tag_size_m,
                "unique_tags": 0,
                "ids": [],
                "detections": 0,
                "tags_used_for_scale": 0,
                "corner_reprojection_rmse_px": None,
            },
            scale={
                "applied": False,
                "source": "markertag",
                "units": None,
                "scale_factor": None,
                "median_tag_scale": None,
                "scale_residual_pct": None,
            },
        )
        _write_json(metadata_path, payload)
        return payload

    cameras = read_cameras_binary(sparse_model / "cameras.bin")
    registered = read_registered_images(sparse_model / "images.bin")
    associate_registered_images(detections, registered)
    reconstructed = reconstruct_tags(detections, cameras, registered)
    unique_ids = sorted({item.tag_id for item in detections})
    registered_observations = sum(item.registered for item in detections)

    if not detections:
        scale_result: dict[str, Any] = {
            "status": "no_detections",
            "reason": "No MarkerTags were detected in the image set.",
            "measurements": [],
        }
    elif registered_observations < 2:
        scale_result = {
            "status": "insufficient_observations",
            "reason": "MarkerTags must be detected in at least two registered images.",
            "measurements": [],
        }
    else:
        scale_result = estimate_metric_scale(reconstructed, tag_size_m)

    scaled = scale_result["status"] == "scaled"
    scale = float(scale_result.get("scale_factor", 1.0))
    if scaled:
        scale_colmap_model(sparse_model, metric_model, scale)
    else:
        shutil.rmtree(metric_model, ignore_errors=True)

    reconstructed_json: dict[str, Any] = {}
    for tag_id, tag in reconstructed.items():
        multiplier = scale if scaled else 1.0
        corners = [
            None if point is None else [float(value * multiplier) for value in point]
            for point in tag["corners"]
        ]
        center = tag["center"]
        reconstructed_json[str(tag_id)] = {
            "corners_3d": corners,
            "center_3d": (
                None if center is None else [float(value * multiplier) for value in center]
            ),
            "coordinate_units": "metres" if scaled else "COLMAP units",
            "registered_observations": tag["registered_observations"],
            "registered_images": tag["registered_images"],
            "triangulation": tag["point_details"],
        }

    detection_json = []
    for detection in detections:
        reconstructed_tag = reconstructed_json.get(str(detection.tag_id), {})
        detection_json.append(
            {
                "family": family,
                "tag_id": detection.tag_id,
                "image": detection.image,
                "image_id": detection.image_id,
                "camera_id": detection.camera_id,
                "registered": detection.registered,
                "pixel_corners": detection.corners.tolist(),
                "pixel_center": detection.center.tolist(),
                "reconstructed_3d_corners": reconstructed_tag.get("corners_3d"),
                "reconstructed_3d_center": reconstructed_tag.get("center_3d"),
                "coordinate_units": reconstructed_tag.get("coordinate_units"),
            }
        )

    corner_residuals = [
        float(detail["reprojection_rms_px"])
        for tag in reconstructed.values()
        for detail in tag["point_details"][:4]
        if detail is not None
    ]
    corner_reprojection_rmse_px = (
        math.sqrt(float(np.mean(np.square(corner_residuals))))
        if corner_residuals
        else None
    )
    markertags_metadata = {
        "detected": bool(detections),
        "family": family,
        "tag_size_m": tag_size_m,
        "unique_tags": len(unique_ids),
        "ids": unique_ids,
        "detections": len(detections),
        "tags_used_for_scale": int(scale_result.get("inlier_tags", 0)),
        "corner_reprojection_rmse_px": corner_reprojection_rmse_px,
    }
    scale_metadata = {
        "applied": scaled,
        "source": "markertag",
        "units": "m" if scaled else None,
        "scale_factor": scale_result.get("scale_factor"),
        "median_tag_scale": scale_result.get("median_tag_scale"),
        "scale_residual_pct": scale_result.get("scale_residual_pct"),
    }

    payload = dict(
        base,
        status=scale_result["status"],
        reason=scale_result.get("reason", ""),
        scaled=scaled,
        unique_tags=len(unique_ids),
        tag_ids=unique_ids,
        observations=len(detections),
        registered_observations=registered_observations,
        scale_factor=scale_result.get("scale_factor"),
        residual_rms_m=scale_result.get("residual_rms_m"),
        relative_residual=scale_result.get("relative_residual"),
        scale_measurements=scale_result.get("measurements", []),
        inlier_measurements=scale_result.get("inlier_measurements", 0),
        tag_scale_estimates=scale_result.get("tag_scale_estimates", []),
        markertags=markertags_metadata,
        scale=scale_metadata,
        reconstructed_tags=reconstructed_json,
        detections=detection_json,
        coordinate_system=(
            "metric COLMAP world coordinates" if scaled else "unscaled COLMAP world coordinates"
        ),
        metric_model=str(metric_model) if scaled else None,
    )
    _write_json(metadata_path, payload)
    return payload


def read_viewer_metadata(path: str | Path) -> dict[str, Any] | None:
    """Read MarkerTag metadata and normalize legacy v0.6 flat payloads."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if not isinstance(payload.get("markertags"), dict):
        payload["markertags"] = {
            "detected": int(payload.get("unique_tags", 0)) > 0,
            "family": payload.get("family"),
            "tag_size_m": payload.get("tag_edge_m"),
            "unique_tags": int(payload.get("unique_tags", 0)),
            "ids": payload.get("tag_ids", []),
            "detections": int(payload.get("observations", 0)),
            "tags_used_for_scale": int(payload.get("inlier_tags", 0)),
            "corner_reprojection_rmse_px": payload.get(
                "corner_reprojection_rmse_px"
            ),
        }
    if not isinstance(payload.get("scale"), dict):
        applied = payload.get("scaled") is True
        payload["scale"] = {
            "applied": applied,
            "source": "markertag",
            "units": "m" if applied else None,
            "scale_factor": payload.get("scale_factor"),
            "median_tag_scale": payload.get("median_tag_scale"),
            "scale_residual_pct": payload.get("scale_residual_pct"),
        }
    return payload


def has_metric_scale(payload: dict[str, Any] | None) -> bool:
    """Return whether viewer coordinates are confirmed to be metres."""

    if not payload:
        return False
    scale = payload.get("scale")
    return (
        isinstance(scale, dict)
        and scale.get("applied") is True
        and scale.get("units") == "m"
    )


def format_viewer_diagnostics(payload: dict[str, Any] | None) -> str:
    """Format saved detection and scale diagnostics for the Viewer Data panel."""

    if payload is None:
        return "MARKERTAGS\nStatus: Not scanned\n\nSCALE\nStatus: Not applied"
    markers = payload.get("markertags", {})
    scale = payload.get("scale", {})
    ids = markers.get("ids", [])
    ids_text = ", ".join(str(value) for value in ids) if ids else "—"
    tag_size = _diagnostic_number(markers.get("tag_size_m"), multiplier=1000, suffix=" mm")
    reprojection = _diagnostic_number(
        markers.get("corner_reprojection_rmse_px"), suffix=" px"
    )
    factor = _diagnostic_number(scale.get("scale_factor"), precision=8)
    median = _diagnostic_number(scale.get("median_tag_scale"), precision=8)
    residual = _diagnostic_number(scale.get("scale_residual_pct"), suffix=" %")
    source = str(scale.get("source") or "—").replace("markertag", "MarkerTags")
    units = "metres" if scale.get("units") == "m" else str(scale.get("units") or "—")
    return "\n".join(
        (
            "MARKERTAGS",
            f"Status: {'Detected' if markers.get('detected') else 'Not detected'}",
            f"Family: {markers.get('family') or '—'}",
            f"Physical tag size: {tag_size}",
            f"Unique tags: {int(markers.get('unique_tags', 0))}",
            f"Tag IDs: {ids_text}",
            f"Image detections: {int(markers.get('detections', 0))}",
            f"Tags used for scale: {int(markers.get('tags_used_for_scale', 0))}",
            f"Corner reprojection RMSE: {reprojection}",
            "",
            "SCALE",
            f"Status: {'Applied' if scale.get('applied') is True else 'Not applied'}",
            f"Source: {source}",
            f"Units: {units}",
            f"Scale factor: {factor}",
            f"Median tag scale: {median}",
            f"Robust scale SD (MAD): {residual}",
        )
    )


def _diagnostic_number(
    value: object,
    *,
    multiplier: float = 1.0,
    suffix: str = "",
    precision: int = 4,
) -> str:
    if value is None:
        return "—"
    try:
        numeric = float(value) * multiplier
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(numeric):
        return "—"
    return f"{numeric:.{precision}g}{suffix}"


def quaternion_rotation(quaternion: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(quaternion))
    if norm <= 1.0e-12:
        raise ValueError("COLMAP camera quaternion has zero length")
    w, x, y, z = quaternion / norm
    return np.asarray(
        (
            (1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w),
            (2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w),
            (2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y),
        ),
        dtype=float,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(stream: BinaryIO, format_string: str) -> tuple[Any, ...]:
    size = struct.calcsize(format_string)
    value = stream.read(size)
    if len(value) != size:
        raise ValueError("Unexpected end of COLMAP binary model")
    return struct.unpack(format_string, value)


def _read_c_string(stream: BinaryIO) -> str:
    return _read_c_string_bytes(stream).decode("utf-8", errors="replace")


def _read_c_string_bytes(stream: BinaryIO) -> bytes:
    value = bytearray()
    while True:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unexpected end of COLMAP image name")
        if byte == b"\0":
            return bytes(value)
        value.extend(byte)

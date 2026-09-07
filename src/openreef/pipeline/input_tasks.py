"""Prepare immutable source imagery and pipeline-ready images."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from openreef.io.color_correction import enhance_underwater
from openreef.pipeline.stages import IMAGE_EXTENSIONS, DatasetLayout, sync_model_links

ACTIVE_PROCESS: subprocess.Popen[str] | None = None


def _emit_phase(message: str) -> None:
    print(f"OPENREEF_PHASE\t{message}", flush=True)


def _emit_progress(current: int, total: int, name: str = "") -> None:
    print(f"OPENREEF_PROGRESS\t{current}\t{total}\t{name}", flush=True)


def _image_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def _copy_or_link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _adopt_existing_images(layout: DatasetLayout) -> None:
    existing = _image_files(layout.images)
    if not existing:
        return
    _emit_phase(f"Preserving {len(existing):,} current images as originals")
    for index, source in enumerate(existing, start=1):
        destination = layout.original / source.relative_to(layout.images)
        _copy_or_link(source, destination)
        _emit_progress(index, len(existing), source.name)


def _import_photos(source_folder: Path, original: Path) -> int:
    files = _image_files(source_folder)
    if not files:
        raise RuntimeError(f"No supported photos found in {source_folder}")
    if source_folder.resolve() == original.resolve():
        return len(files)
    _emit_phase(f"Importing {len(files):,} original photos")
    for index, source in enumerate(files, start=1):
        destination = original / source.relative_to(source_folder)
        _copy_or_link(source, destination)
        _emit_progress(index, len(files), source.name)
    return len(files)


def _video_duration(video: Path, ffprobe: str) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def _extract_video(video: Path, layout: DatasetLayout, interval: float) -> int:
    global ACTIVE_PROCESS
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Video import requires ffmpeg and ffprobe on PATH")

    source_folder = layout.root / "source"
    source_video = source_folder / video.name
    _copy_or_link(video, source_video)
    frame_folder = layout.original / f"video_{video.stem}"
    if frame_folder.exists():
        shutil.rmtree(frame_folder)
    frame_folder.mkdir(parents=True)
    duration = _video_duration(source_video, ffprobe)
    estimated = max(1, int(duration / interval) + 1)
    _emit_phase(f"Extracting one frame every {interval:g}s from {video.name}")

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "warning",
        "-y",
        "-i",
        str(source_video),
        "-vf",
        f"fps=1/{interval:g}",
        "-q:v",
        "2",
        "-progress",
        "pipe:1",
        "-nostats",
        str(frame_folder / "frame_%06d.jpg"),
    ]
    ACTIVE_PROCESS = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    last_reported = -1
    assert ACTIVE_PROCESS.stdout is not None
    for line in ACTIVE_PROCESS.stdout:
        value = line.strip()
        if value.startswith("frame="):
            try:
                current = int(value.split("=", 1)[1])
            except ValueError:
                continue
            if current != last_reported:
                _emit_progress(min(current, estimated), estimated, "Extracting video frames")
                last_reported = current
        elif value and not value.startswith(("fps=", "bitrate=", "speed=", "progress=")):
            print(value, flush=True)
    return_code = ACTIVE_PROCESS.wait()
    ACTIVE_PROCESS = None
    if return_code != 0:
        raise RuntimeError(f"ffmpeg exited with code {return_code}")
    frames = _image_files(frame_folder)
    if not frames:
        raise RuntimeError("ffmpeg completed without producing any frames")
    _emit_progress(len(frames), len(frames), f"Extracted {len(frames):,} frames")
    return len(frames)


def _archive_downstream(layout: DatasetLayout) -> None:
    targets = [
        path
        for path in (layout.colmap, layout.openmvs, layout.models)
        if path.exists() or path.is_symlink()
    ]
    if not targets:
        return
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    history = layout.root / ".openreef" / "history" / timestamp
    counter = 1
    while history.exists():
        history = history.with_name(f"{timestamp}-{counter}")
        counter += 1
    history.mkdir(parents=True)
    _emit_phase("Archiving stale reconstruction outputs")
    for source in targets:
        destination = history / source.name
        source.rename(destination)
        print(f"Preserved {source.name}/ at {destination}", flush=True)


def _build_pipeline_images(
    layout: DatasetLayout,
    color_correct: bool,
    quality: int,
    invalidate_downstream: bool,
) -> int:
    import cv2

    originals = _image_files(layout.original)
    if not originals:
        raise RuntimeError(f"No original images found in {layout.original}")
    state_folder = layout.root / ".openreef"
    build_folder = state_folder / "images-build"
    if build_folder.exists():
        shutil.rmtree(build_folder)
    build_folder.mkdir(parents=True)
    operation = "Color correcting" if color_correct else "Preparing"
    _emit_phase(f"{operation} {len(originals):,} pipeline images")

    for index, source in enumerate(originals, start=1):
        relative = source.relative_to(layout.original)
        if color_correct:
            destination = (build_folder / relative).with_suffix(".jpg")
            destination.parent.mkdir(parents=True, exist_ok=True)
            image = cv2.imread(str(source), cv2.IMREAD_COLOR)
            if image is None:
                print(f"Skipping unreadable image: {source}", flush=True)
                continue
            corrected = enhance_underwater(image)
            if not cv2.imwrite(str(destination), corrected, [cv2.IMWRITE_JPEG_QUALITY, quality]):
                raise RuntimeError(f"Could not write corrected image: {destination}")
        else:
            destination = build_folder / relative
            _copy_or_link(source, destination)
        _emit_progress(index, len(originals), source.name)

    if invalidate_downstream:
        _archive_downstream(layout)

    if layout.images.exists():
        preserved = state_folder / "preserved-non-images"
        for path in layout.images.rglob("*"):
            if path.is_file() and path.suffix.lower() not in IMAGE_EXTENSIONS:
                destination = preserved / path.relative_to(layout.images)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        shutil.rmtree(layout.images)
    os.replace(build_folder, layout.images)
    sync_model_links(layout)
    return len(_image_files(layout.images))


def prepare(args: argparse.Namespace) -> int:
    layout = DatasetLayout.from_path(args.dataset)
    layout.root.mkdir(parents=True, exist_ok=True)
    layout.original.mkdir(parents=True, exist_ok=True)
    sync_model_links(layout)
    _adopt_existing_images(layout)

    source = Path(args.source).expanduser().resolve()
    if args.source_kind in ("photos", "existing"):
        _import_photos(source, layout.original)
    elif args.source_kind == "video":
        if not source.is_file():
            raise RuntimeError(f"Video does not exist: {source}")
        _extract_video(source, layout, args.interval)
    else:
        raise RuntimeError(f"Unknown source type: {args.source_kind}")

    input_changed = args.source_kind != "existing" or args.color_correct
    count = _build_pipeline_images(
        layout,
        args.color_correct,
        args.jpeg_quality,
        invalidate_downstream=input_changed,
    )
    state_folder = layout.root / ".openreef"
    state_folder.mkdir(parents=True, exist_ok=True)
    metadata = {
        "prepared_at": datetime.now().astimezone().isoformat(),
        "source_kind": args.source_kind,
        "source": str(source),
        "video_interval_seconds": args.interval if args.source_kind == "video" else None,
        "color_corrected": args.color_correct,
        "pipeline_images": count,
    }
    (state_folder / "input.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    _emit_phase(f"Ready: {count:,} images available to Sparse Cloud")
    return 0


def _handle_signal(signum: int, frame: object) -> None:
    del frame
    if ACTIVE_PROCESS and ACTIVE_PROCESS.poll() is None:
        ACTIVE_PROCESS.terminate()
    raise SystemExit(128 + signum)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--source-kind", choices=("photos", "video", "existing"), required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--color-correct", action="store_true")
    parser.add_argument("--jpeg-quality", type=int, default=98)
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    try:
        return prepare(args)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

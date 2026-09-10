"""Headless command-line runner for the OpenReef reconstruction pipeline."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from openreef.pipeline.stages import (
    ALL_STAGES,
    STAGE_LABELS,
    DatasetLayout,
    PipelineOptions,
    StageConfigurationError,
    StageKey,
    build_stage_command,
    stage_output_exists,
    sync_model_links,
)


def _stage_list(value: str) -> tuple[StageKey, ...]:
    try:
        stages = tuple(StageKey(item.strip().replace("-", "_")) for item in value.split(","))
    except ValueError as exc:
        choices = ", ".join(stage.value for stage in ALL_STAGES)
        raise argparse.ArgumentTypeError(f"Unknown stage. Available stages: {choices}") from exc
    if not stages:
        raise argparse.ArgumentTypeError("Select at least one stage")
    return stages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openreef-pipeline",
        description="Run OpenReef reconstruction without launching the desktop interface.",
    )
    parser.add_argument("dataset", type=Path, help="Dataset containing the images/ folder")
    parser.add_argument(
        "--stages",
        type=_stage_list,
        default=ALL_STAGES,
        metavar="LIST",
        help="Comma-separated stages; defaults to the complete pipeline",
    )
    parser.add_argument("--force", action="store_true", help="Run stages even if output exists")
    parser.add_argument("--cores", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--memory-gb", type=float, default=0.0, help="0 means unlimited")
    parser.add_argument(
        "--gpu", action=argparse.BooleanOptionalAction, default=True, help="Use COLMAP GPU"
    )
    parser.add_argument("--camera-model", default="SIMPLE_RADIAL")
    parser.add_argument("--single-camera", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-image-size", type=int, default=3200)
    parser.add_argument("--sequential-overlap", type=int, default=10)
    parser.add_argument("--resolution-level", type=int, default=1)
    parser.add_argument("--max-resolution", type=int, default=2560)
    parser.add_argument("--number-views", type=int, default=5)
    parser.add_argument("--number-views-fuse", type=int, default=3)
    parser.add_argument(
        "--estimate-colors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Estimate dense point colors",
    )
    parser.add_argument(
        "--estimate-normals",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Estimate dense point normals",
    )
    parser.add_argument(
        "--dense-original",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Create the Original dense-cloud, surface-mesh, and texture outputs",
    )
    parser.add_argument(
        "--dense-low",
        action="store_true",
        help="Also create the Low dense-cloud, surface-mesh, and texture outputs",
    )
    parser.add_argument(
        "--dense-medium",
        action="store_true",
        help="Also create the Medium dense-cloud, surface-mesh, and texture outputs",
    )
    parser.add_argument("--dense-original-percent", type=int, default=100)
    parser.add_argument("--dense-medium-percent", type=int, default=20)
    parser.add_argument("--dense-low-percent", type=int, default=5)
    parser.add_argument(
        "--texture-resolution-level",
        type=int,
        choices=range(0, 5),
        default=0,
        help="Texture source-image scale: 0 is full resolution; each level halves it",
    )
    parser.add_argument("--max-texture-size", type=int, default=8192)
    parser.add_argument("--texture-sharpness", type=float, default=0.5)
    parser.add_argument(
        "--global-seam-leveling",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--local-seam-leveling",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser


def run_pipeline(args: argparse.Namespace) -> int:
    layout = DatasetLayout.from_path(args.dataset)
    options = PipelineOptions(
        cores=args.cores,
        memory_gb=args.memory_gb,
        use_gpu=args.gpu,
        camera_model=args.camera_model,
        single_camera=args.single_camera,
        max_image_size=args.max_image_size,
        sequential_overlap=args.sequential_overlap,
        resolution_level=args.resolution_level,
        max_resolution=args.max_resolution,
        number_views=args.number_views,
        number_views_fuse=args.number_views_fuse,
        estimate_colors=args.estimate_colors,
        estimate_normals=args.estimate_normals,
        dense_original=args.dense_original,
        dense_low=args.dense_low,
        dense_medium=args.dense_medium,
        dense_original_percent=args.dense_original_percent,
        dense_medium_percent=args.dense_medium_percent,
        dense_low_percent=args.dense_low_percent,
        texture_resolution_level=args.texture_resolution_level,
        max_texture_size=args.max_texture_size,
        texture_sharpness=args.texture_sharpness,
        global_seam_leveling=args.global_seam_leveling,
        local_seam_leveling=args.local_seam_leveling,
    )
    print(f"OpenReef command-line pipeline\nDataset: {layout.root}", flush=True)
    for index, stage in enumerate(args.stages, start=1):
        label = STAGE_LABELS[stage]
        if not args.force and stage_output_exists(stage, layout, options):
            print(
                f"[{index}/{len(args.stages)}] {label}: existing output found, skipping",
                flush=True,
            )
            continue
        try:
            command = build_stage_command(stage, layout, options)
        except (OSError, StageConfigurationError) as exc:
            print(f"ERROR: {label}: {exc}", file=sys.stderr, flush=True)
            return 2

        print(f"\n[{index}/{len(args.stages)}] {label}\n$ {command.display}", flush=True)
        wrapped = (
            sys.executable,
            "-m",
            "openreef.pipeline.limited_exec",
            "--memory-gb",
            str(options.memory_gb),
            "--",
            command.program,
            *command.arguments,
        )
        try:
            result = subprocess.run(wrapped, cwd=command.working_directory, check=False)
        except KeyboardInterrupt:
            print("\nPipeline stopped by user.", file=sys.stderr, flush=True)
            return 130
        if result.returncode != 0:
            print(f"ERROR: {label} exited with code {result.returncode}", file=sys.stderr)
            return result.returncode
        if not stage_output_exists(stage, layout, options):
            print(f"ERROR: {label} completed but expected output is missing", file=sys.stderr)
            return 3
        sync_model_links(layout)
        print(f"✓ {label} complete", flush=True)

    links = sync_model_links(layout)
    print(f"\nPipeline complete. Model files: {layout.models}", flush=True)
    for path in links:
        print(f"  {path.name}", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_pipeline(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())

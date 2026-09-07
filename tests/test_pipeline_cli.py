from pathlib import Path

from openreef.pipeline.cli import build_parser
from openreef.pipeline.stages import ALL_STAGES, StageKey


def test_cli_defaults_to_complete_pipeline(tmp_path: Path) -> None:
    args = build_parser().parse_args([str(tmp_path)])

    assert args.dataset == tmp_path
    assert args.stages == ALL_STAGES
    assert args.gpu
    assert args.single_camera
    assert args.estimate_colors
    assert args.estimate_normals
    assert args.dense_original
    assert not args.dense_low
    assert not args.dense_medium
    assert args.dense_original_percent == 100
    assert args.dense_medium_percent == 20
    assert args.dense_low_percent == 5


def test_cli_accepts_selected_stages_and_resource_options(tmp_path: Path) -> None:
    args = build_parser().parse_args(
        [
            str(tmp_path),
            "--stages",
            "sparse,undistort,openmvs-import,dense,mesh",
            "--cores",
            "8",
            "--memory-gb",
            "24",
            "--no-gpu",
            "--force",
            "--dense-low",
            "--dense-medium",
            "--dense-medium-percent",
            "25",
            "--dense-low-percent",
            "8",
        ]
    )

    assert args.stages == (
        StageKey.SPARSE,
        StageKey.UNDISTORT,
        StageKey.OPENMVS_IMPORT,
        StageKey.DENSE,
        StageKey.MESH,
    )
    assert args.cores == 8
    assert args.memory_gb == 24
    assert not args.gpu
    assert args.force
    assert args.dense_low
    assert args.dense_medium
    assert args.dense_medium_percent == 25
    assert args.dense_low_percent == 8

import subprocess
from argparse import Namespace
from pathlib import Path

import pytest

from openreef.pipeline.stages import (
    DatasetLayout,
    PipelineOptions,
    StageConfigurationError,
    StageKey,
    build_stage_command,
)
from openreef.pipeline.tasks import sparse_colmap


def _sparse_inputs(tmp_path: Path) -> DatasetLayout:
    layout = DatasetLayout(tmp_path)
    layout.images.mkdir()
    (layout.images / "reef.jpg").touch()
    layout.database.parent.mkdir()
    layout.database.touch()
    return layout


def test_sparse_stage_selects_caspar_bundle_adjustment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _sparse_inputs(tmp_path)
    monkeypatch.setattr("openreef.pipeline.stages.resolve_executable", lambda name: f"/{name}")

    command = build_stage_command(
        StageKey.SPARSE,
        layout,
        PipelineOptions(
            cores=4,
            bundle_adjustment_backend="caspar",
            bundle_adjustment_gpu_index=1,
        ),
    )

    assert command.arguments[command.arguments.index("--ba-backend") + 1] == "caspar"
    assert command.arguments[command.arguments.index("--ba-gpu-index") + 1] == "1"


def test_sparse_stage_rejects_unsupported_caspar_camera_model(tmp_path: Path) -> None:
    layout = _sparse_inputs(tmp_path)

    with pytest.raises(StageConfigurationError, match="SIMPLE_RADIAL and PINHOLE"):
        build_stage_command(
            StageKey.SPARSE,
            layout,
            PipelineOptions(
                cores=4,
                camera_model="OPENCV",
                bundle_adjustment_backend="caspar",
            ),
        )


@pytest.mark.parametrize(
    ("backend", "ceres_gpu", "expected"),
    (
        ("ceres", 0, ()),
        ("ceres", 1, ("--Mapper.ba_use_gpu", "1", "--Mapper.ba_gpu_index", "2")),
        (
            "caspar",
            0,
            (
                "--Mapper.ba_local_backend",
                "CASPAR",
                "--Mapper.ba_global_backend",
                "CASPAR",
                "--Mapper.ba_gpu_index",
                "2",
            ),
        ),
    ),
)
def test_sparse_mapper_backend_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    ceres_gpu: int,
    expected: tuple[str, ...],
) -> None:
    output = tmp_path / "sparse"
    model = output / "0"
    model.mkdir(parents=True)
    (model / "cameras.bin").touch()
    (model / "images.bin").write_bytes((4).to_bytes(8, "little"))
    (model / "points3D.bin").write_bytes((100).to_bytes(8, "little"))
    commands: list[tuple[str, ...]] = []

    def run(command: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        assert not check
        commands.append(tuple(command))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("openreef.pipeline.tasks.subprocess.run", run)
    result = sparse_colmap(
        Namespace(
            executable="colmap",
            database=str(tmp_path / "database.db"),
            images=str(tmp_path / "images"),
            output=str(output),
            cores=8,
            ba_backend=backend,
            ceres_use_gpu=ceres_gpu,
            ba_gpu_index=2,
            levels="original",
            medium_percent=20,
            low_percent=5,
            compact_percent=1,
        )
    )

    assert result == 0
    mapper = commands[0]
    assert mapper[:2] == ("colmap", "mapper")
    for index, argument in enumerate(expected):
        assert mapper[mapper.index(expected[0]) + index] == argument
    if not expected:
        assert "--Mapper.ba_use_gpu" not in mapper
        assert "--Mapper.ba_local_backend" not in mapper

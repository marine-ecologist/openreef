from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

import openreef.pipeline.runner as runner_module
from openreef.pipeline.runner import PipelineRunner
from openreef.pipeline.stages import PipelineOptions, StageCommand, StageKey


def test_runner_streams_output_without_blocking(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    monkeypatch.setattr(
        runner_module,
        "build_stage_command",
        lambda stage, layout, options: StageCommand(
            "/bin/sh",
            ("-c", 'printf "first line\\n"; printf "second line\\n"'),
            tmp_path,
        ),
    )
    monkeypatch.setattr(
        runner_module,
        "stage_output_exists",
        lambda stage, layout, options=None: True,
    )

    runner = PipelineRunner()
    output: list[str] = []
    result: list[tuple[bool, str]] = []
    loop = QEventLoop()
    runner.output_received.connect(output.append)

    def finished(success: bool, message: str) -> None:
        result.append((success, message))
        loop.quit()

    runner.job_finished.connect(finished)
    runner.run(tmp_path, [StageKey.FEATURES], PipelineOptions(cores=2))
    QTimer.singleShot(10_000, loop.quit)
    loop.exec()

    if runner.is_running:
        runner.cancel()
        cleanup_loop = QEventLoop()
        runner.job_finished.connect(lambda success, message: cleanup_loop.quit())
        QTimer.singleShot(6000, cleanup_loop.quit)
        cleanup_loop.exec()

    assert result == [(True, "Selected stages completed")]
    assert "first line" in "".join(output)
    assert "second line" in "".join(output)
    assert app is not None

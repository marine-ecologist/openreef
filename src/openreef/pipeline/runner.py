"""Non-blocking sequential pipeline execution using Qt processes."""

from __future__ import annotations

import re
import sys
from collections import deque
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QObject, QProcess, QProcessEnvironment, QTimer, Signal

from openreef.pipeline.stages import (
    STAGE_LABELS,
    DatasetLayout,
    PipelineOptions,
    StageConfigurationError,
    StageKey,
    build_stage_command,
    selected_dense_levels,
    stage_output_exists,
    sync_model_links,
    textured_output_for_level,
)

ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class PipelineRunner(QObject):
    output_received = Signal(str)
    stage_changed = Signal(str, str, str)
    current_stage_changed = Signal(str)
    progress_changed = Signal(int, int)
    running_changed = Signal(bool)
    job_finished = Signal(bool, str)
    artifact_ready = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.finished.connect(self._process_finished)
        self._process.errorOccurred.connect(self._process_error)
        self._queue: deque[StageKey] = deque()
        self._layout: DatasetLayout | None = None
        self._options: PipelineOptions | None = None
        self._active: StageKey | None = None
        self._total = 0
        self._completed = 0
        self._cancelled = False
        self._elapsed = QElapsedTimer()

    @property
    def is_running(self) -> bool:
        return self._active is not None or bool(self._queue)

    @property
    def elapsed_seconds(self) -> int:
        return max(0, self._elapsed.elapsed() // 1000) if self._elapsed.isValid() else 0

    def run(
        self,
        dataset_root: str | Path,
        stages: list[StageKey],
        options: PipelineOptions,
    ) -> None:
        if self.is_running:
            self.output_received.emit("A pipeline is already running.\n")
            return
        if not stages:
            self.job_finished.emit(False, "Select at least one stage.")
            return

        self._layout = DatasetLayout.from_path(dataset_root)
        self._options = options
        self._queue = deque(stages)
        self._active = None
        self._total = len(stages)
        self._completed = 0
        self._cancelled = False
        self._elapsed.start()
        self.progress_changed.emit(0, self._total)
        self.running_changed.emit(True)
        for stage in stages:
            self.stage_changed.emit(stage.value, "queued", "Queued")
        self.output_received.emit(
            f"\nOpenReef pipeline\nDataset: {self._layout.root}\n"
            f"Selected stages: {', '.join(STAGE_LABELS[item] for item in stages)}\n"
        )
        self._start_next()

    def cancel(self) -> None:
        if not self.is_running:
            return
        self._cancelled = True
        self._queue.clear()
        self.output_received.emit("\nStop requested; asking the active stage to exit cleanly…\n")
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.terminate()
            QTimer.singleShot(5000, self._kill_if_running)
        else:
            self._finish(False, "Pipeline stopped")

    def _start_next(self) -> None:
        if not self._queue:
            self._finish(True, "Selected stages completed")
            return
        assert self._layout is not None
        assert self._options is not None
        self._active = self._queue.popleft()
        label = STAGE_LABELS[self._active]
        try:
            command = build_stage_command(self._active, self._layout, self._options)
        except (StageConfigurationError, OSError) as exc:
            self.stage_changed.emit(self._active.value, "failed", str(exc))
            self.output_received.emit(f"\nERROR: {exc}\n")
            self._queue.clear()
            self._finish(False, str(exc))
            return

        self.current_stage_changed.emit(label)
        self.stage_changed.emit(self._active.value, "running", "Running…")
        self.output_received.emit(f"\n{'=' * 72}\n[{self._completed + 1}/{self._total}] {label}\n")
        self.output_received.emit(f"$ {command.display}\n{'-' * 72}\n")

        environment = QProcessEnvironment.systemEnvironment()
        openmvs_bin = str(Path.home() / "vcpkg" / "installed" / "arm64-osx" / "tools" / "openmvs")
        environment.insert("PATH", f"{openmvs_bin}:{environment.value('PATH')}")
        self._process.setProcessEnvironment(environment)
        self._process.setWorkingDirectory(str(command.working_directory))
        self._process.setProgram(sys.executable)
        self._process.setArguments(
            [
                "-m",
                "openreef.pipeline.limited_exec",
                "--memory-gb",
                str(self._options.memory_gb),
                "--",
                command.program,
                *command.arguments,
            ]
        )
        self._process.start()

    def _read_output(self) -> None:
        raw = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if raw:
            self.output_received.emit(strip_ansi(raw))

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._read_output()
        if self._active is None:
            return
        stage = self._active
        self._active = None
        if self._cancelled:
            self.stage_changed.emit(stage.value, "stopped", "Stopped")
            self._finish(False, "Pipeline stopped")
            return
        if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
            message = f"{STAGE_LABELS[stage]} exited with code {exit_code}"
            self.stage_changed.emit(stage.value, "failed", message)
            self.output_received.emit(f"\nERROR: {message}\n")
            self._queue.clear()
            self._finish(False, message)
            return
        assert self._layout is not None
        if not stage_output_exists(stage, self._layout, self._options):
            message = f"{STAGE_LABELS[stage]} finished but its expected output was not found."
            self.stage_changed.emit(stage.value, "failed", message)
            self.output_received.emit(f"\nERROR: {message}\n")
            self._queue.clear()
            self._finish(False, message)
            return

        self._completed += 1
        self.stage_changed.emit(stage.value, "complete", "Complete")
        self.progress_changed.emit(self._completed, self._total)
        self.output_received.emit(f"\n✓ {STAGE_LABELS[stage]} complete\n")
        try:
            links = sync_model_links(self._layout)
        except OSError as exc:
            self.output_received.emit(f"Warning: could not update mesh shortcuts: {exc}\n")
        else:
            if links:
                self.output_received.emit(
                    f"Model shortcuts updated in {self._layout.models} ({len(links)} linked)\n"
                )
        if stage == StageKey.DENSE and self._layout.dense_cloud.is_file():
            self.artifact_ready.emit(str(self._layout.dense_cloud))
        elif stage == StageKey.MESH and self._layout.surface_mesh.is_file():
            self.artifact_ready.emit(str(self._layout.surface_mesh))
        elif stage == StageKey.TEXTURE and self._options:
            for level, _, _ in selected_dense_levels(self._layout, self._options):
                output = textured_output_for_level(self._layout, level)
                if output.is_file():
                    self.artifact_ready.emit(str(output))
                    break
        self._start_next()

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.ProcessError.FailedToStart or self._active is None:
            return
        stage = self._active
        self._active = None
        message = f"Could not start {STAGE_LABELS[stage]}: {self._process.errorString()}"
        self.stage_changed.emit(stage.value, "failed", message)
        self.output_received.emit(f"\nERROR: {message}\n")
        self._queue.clear()
        self._finish(False, message)

    def _kill_if_running(self) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self.output_received.emit("Stage did not stop in 5 seconds; terminating it now.\n")
            self._process.kill()

    def _finish(self, success: bool, message: str) -> None:
        self._queue.clear()
        self._active = None
        self.current_stage_changed.emit("Idle")
        self.running_changed.emit(False)
        self.job_finished.emit(success, message)
        self.output_received.emit(f"\n{message}. Elapsed: {format_elapsed(self.elapsed_seconds)}\n")


def strip_ansi(value: str) -> str:
    return ANSI_ESCAPE.sub("", value).replace("\r", "")


def format_elapsed(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

"""Asynchronous input preparation with structured progress messages."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


@dataclass(frozen=True)
class InputJob:
    dataset: Path
    source_kind: str
    source: Path
    interval: float = 1.0
    color_correct: bool = False
    jpeg_quality: int = 98


class InputRunner(QObject):
    output_received = Signal(str)
    phase_changed = Signal(str)
    progress_changed = Signal(int, int)
    running_changed = Signal(bool)
    job_finished = Signal(bool, str)
    images_ready = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self._buffer = ""
        self._job: InputJob | None = None
        self._stopping = False

    @property
    def is_running(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, job: InputJob) -> None:
        if self.is_running:
            self.output_received.emit("Input preparation is already running.\n")
            return
        if not job.dataset.is_dir():
            self.job_finished.emit(False, f"Dataset folder does not exist: {job.dataset}")
            return
        self._job = job
        self._stopping = False
        self._buffer = ""
        arguments = [
            "-m",
            "openreef.pipeline.input_tasks",
            "--dataset",
            str(job.dataset),
            "--source-kind",
            job.source_kind,
            "--source",
            str(job.source),
            "--interval",
            str(job.interval),
            "--jpeg-quality",
            str(job.jpeg_quality),
        ]
        if job.color_correct:
            arguments.append("--color-correct")
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PATH", f"/opt/homebrew/bin:{environment.value('PATH')}")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(job.dataset))
        self.process.setProgram(sys.executable)
        self.process.setArguments(arguments)
        self.output_received.emit(
            f"\nPreparing input images\nDataset: {job.dataset}\nSource: {job.source}\n"
        )
        self.phase_changed.emit("Starting…")
        self.progress_changed.emit(0, 0)
        self.running_changed.emit(True)
        self.process.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stopping = True
        self.output_received.emit("\nStop requested…\n")
        self.process.terminate()
        QTimer.singleShot(5000, self._kill_if_running)

    def _read_output(self) -> None:
        chunk = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._buffer += chunk.replace("\r", "")
        lines = self._buffer.split("\n")
        self._buffer = lines.pop()
        for line in lines:
            self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        if line.startswith("OPENREEF_PHASE\t"):
            message = line.split("\t", 1)[1]
            self.phase_changed.emit(message)
            self.output_received.emit(f"\n{message}\n")
            return
        if line.startswith("OPENREEF_PROGRESS\t"):
            fields = line.split("\t", 3)
            try:
                current, total = int(fields[1]), int(fields[2])
            except (IndexError, ValueError):
                return
            self.progress_changed.emit(current, total)
            if len(fields) == 4 and fields[3]:
                self.phase_changed.emit(f"{current:,}/{total:,} — {fields[3]}")
            return
        self.output_received.emit(line + "\n")

    def _finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._read_output()
        if self._buffer:
            self._handle_line(self._buffer)
            self._buffer = ""
        job = self._job
        self._job = None
        self.running_changed.emit(False)
        if job is None:
            return
        if self._stopping:
            self.phase_changed.emit("Stopped")
            self.job_finished.emit(False, "Input preparation stopped")
            return
        success = exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0
        if success:
            message = "Input images ready"
            self.phase_changed.emit(message)
            self.job_finished.emit(True, message)
            self.images_ready.emit(str(job.dataset / "images"))
        else:
            message = f"Input preparation failed with code {exit_code}"
            self.phase_changed.emit(message)
            self.job_finished.emit(False, message)

    def _error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            message = f"Could not start input processing: {self.process.errorString()}"
            self._job = None
            self.output_received.emit(f"ERROR: {message}\n")
            self.running_changed.emit(False)
            self.job_finished.emit(False, message)

    def _kill_if_running(self) -> None:
        if self.is_running:
            self.process.kill()

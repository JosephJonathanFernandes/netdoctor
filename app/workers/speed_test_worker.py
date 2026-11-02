"""Background worker for running a speed test without blocking the GUI."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.services.speed_test import SpeedTestResult, SpeedTestService


class SpeedTestSignals(QObject):
    started = Signal()
    progress = Signal(str, str)  # stage, message
    finished = Signal(object)    # SpeedTestResult
    error = Signal(str)


class SpeedTestWorker(QThread):
    def __init__(self, service: Optional[SpeedTestService] = None, parent=None):
        super().__init__(parent)
        self.service = service or SpeedTestService()
        self.signals = SpeedTestSignals()
        self.service.progress_callback = self._on_progress

    def _on_progress(self, stage: str, message: str) -> None:
        self.signals.progress.emit(stage, message)

    def cancel(self) -> None:
        self.service.cancel()

    def run(self) -> None:
        self.signals.started.emit()
        try:
            result = self.service.run()
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))

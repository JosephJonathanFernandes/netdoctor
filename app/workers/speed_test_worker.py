"""Background worker for running a speed test without blocking the GUI."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from app.services.speed_test import SpeedTestService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SpeedTestSignals(QObject):
    """Signals emitted by SpeedTestWorker."""

    started = Signal()
    progress = Signal(str, str)  # stage, message
    finished = Signal(object)    # SpeedTestResult
    error = Signal(str)


class SpeedTestWorker(QThread):
    """QThread that runs SpeedTestService and marshals results to the GUI thread."""

    def __init__(self, service: SpeedTestService | None = None, parent=None):
        super().__init__(parent)
        self.service = service or SpeedTestService()
        self.signals = SpeedTestSignals()
        self.service.progress_callback = self._on_progress

    def _on_progress(self, stage: str, message: str) -> None:
        self.signals.progress.emit(stage, message)

    def cancel(self) -> None:
        self.service.cancel()

    def run(self) -> None:
        logger.info("Speed test worker started")
        self.signals.started.emit()
        try:
            result = self.service.run()
            self.signals.finished.emit(result)
        except Exception as exc:  # pragma: no cover - defensive GUI guard
            logger.exception("Speed test worker failed")
            self.signals.error.emit(str(exc))

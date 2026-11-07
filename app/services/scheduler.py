"""Scheduled automatic speed tests for NetDoctor.

Runs speed tests in the background at a configurable interval and persists
results automatically. Intended for "set and forget" monitoring.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.services.speed_test import SpeedTestResult, SpeedTestService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SchedulerSignals(QObject):
    started = Signal()
    stopped = Signal()
    test_started = Signal()
    test_completed = Signal(object)  # SpeedTestResult
    test_failed = Signal(str)
    error = Signal(str)


class SchedulerService(QThread):
    """Periodically runs speed tests in the background."""

    def __init__(self, interval_minutes: float = 60.0, parent=None):
        super().__init__(parent)
        self.interval_minutes = max(5.0, float(interval_minutes))
        self.signals = SchedulerSignals()
        self._running = False
        self._service = SpeedTestService()
        self._service.progress_callback = lambda stage, msg: logger.debug(
            "Scheduler test stage=%s msg=%s", stage, msg
        )

    def set_interval(self, minutes: float) -> None:
        self.interval_minutes = max(5.0, float(minutes))

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        self.signals.started.emit()
        logger.info("Scheduler started (interval=%.1f min)", self.interval_minutes)
        try:
            while self._running:
                self.signals.test_started.emit()
                try:
                    result = self._service.run()
                    if result.status == "completed":
                        self.signals.test_completed.emit(result)
                    else:
                        self.signals.test_failed.emit(
                            result.error_message or "Test failed"
                        )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Scheduled test error")
                    self.signals.test_failed.emit(str(exc))

                # Sleep in small increments so stop() is responsive.
                slept = 0.0
                while slept < self.interval_minutes * 60.0 and self._running:
                    time.sleep(min(5.0, self.interval_minutes * 60.0 - slept))
                    slept += 5.0
        finally:
            self.signals.stopped.emit()
            logger.info("Scheduler stopped")

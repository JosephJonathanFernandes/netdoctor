"""Background worker for real-time network monitoring using psutil."""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

import psutil

from app.utils.logging import get_logger
from app.utils.platform_info import ping_host

logger = get_logger(__name__)


class MonitoringSignals(QObject):
    """Signals emitted by MonitoringWorker."""

    started = Signal()
    stopped = Signal()
    sample = Signal(object)   # dict of current metrics
    error = Signal(str)


class MonitoringWorker(QThread):
    """Periodically samples network interface counters and optional latency.

    Runs in a background thread. Emits one ``sample`` signal per interval.
    """

    def __init__(self, interval_seconds: float = 2.0, parent=None):
        super().__init__(parent)
        self.interval_seconds = max(0.5, float(interval_seconds))
        self.signals = MonitoringSignals()
        self._running = False
        self._last_counters: Optional[dict] = None
        self._last_time: Optional[float] = None

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        self.signals.started.emit()
        logger.info("Monitoring worker started (interval=%.1fs)", self.interval_seconds)
        try:
            while self._running:
                sample = self._collect_sample()
                if sample is not None:
                    self.signals.sample.emit(sample)
                slept = 0.0
                while slept < self.interval_seconds and self._running:
                    time.sleep(min(0.2, self.interval_seconds - slept))
                    slept += 0.2
        except Exception:  # pragma: no cover - defensive
            logger.exception("Monitoring worker crashed")
            self.signals.error.emit("Monitoring worker crashed")
        finally:
            self.signals.stopped.emit()
            logger.info("Monitoring worker stopped")

    def _collect_sample(self) -> Optional[dict]:
        try:
            counters = psutil.net_io_counters(pernic=True)
        except Exception:
            logger.exception("Failed to read psutil network counters")
            return None

        now = time.time()
        total_sent = sum(c.bytes_sent for c in counters.values())
        total_recv = sum(c.bytes_recv for c in counters.values())

        sample: dict = {
            "timestamp": now,
            "bytes_sent": total_sent,
            "bytes_recv": total_recv,
            "upload_bps": None,
            "download_bps": None,
            "latency_ms": None,
            "interface_count": len(counters),
        }

        if self._last_counters is not None and self._last_time is not None:
            elapsed = now - self._last_time
            if elapsed > 0:
                sample["upload_bps"] = (total_sent - self._last_counters["sent"]) / elapsed
                sample["download_bps"] = (total_recv - self._last_counters["recv"]) / elapsed

        try:
            ping = ping_host("1.1.1.1", count=1, timeout=1.5)
            sample["latency_ms"] = ping.get("avg_ms")
        except Exception:
            sample["latency_ms"] = None

        self._last_counters = {"sent": total_sent, "recv": total_recv}
        self._last_time = now
        return sample

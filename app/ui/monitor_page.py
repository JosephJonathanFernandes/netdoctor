"""Network Monitor page: real-time interface traffic with a live graph."""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ui.chart import MplCanvas
from app.ui.theme import add_shadow, make_card, palette_dict
from app.ui.widgets import MetricTile
from app.utils.formatting import format_bits_per_sec, format_bytes, format_ms
from app.workers.monitoring_worker import MonitoringWorker


class MonitorPage(QWidget):
    def __init__(self, interval_seconds: float = 2.0, parent=None):
        super().__init__(parent)
        self._interval = interval_seconds
        self._worker: MonitoringWorker | None = None
        self._running = False
        self._dark = True

        max_points = 200
        self._times: deque[float] = deque(maxlen=max_points)
        self._download_bps: deque[float | None] = deque(maxlen=max_points)
        self._upload_bps: deque[float | None] = deque(maxlen=max_points)
        self._latency_ms: deque[float | None] = deque(maxlen=max_points)
        self._t0: float | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Network Monitor")
        title.setObjectName("h1")
        subtitle = QLabel("Real-time interface traffic and latency")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        root.addLayout(header)

        control = QHBoxLayout()
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.interval_label = QLabel("Interval:")
        self.interval_label.setObjectName("muted")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(int(self._interval))
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setToolTip("Sampling interval")
        control.addWidget(self.start_btn)
        control.addWidget(self.stop_btn)
        control.addSpacing(20)
        control.addWidget(self.interval_label)
        control.addWidget(self.interval_spin)
        control.addStretch()
        root.addLayout(control)

        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.tile_sent = MetricTile("Bytes sent")
        self.tile_recv = MetricTile("Bytes received")
        self.tile_up = MetricTile("Upload rate")
        self.tile_down = MetricTile("Download rate")
        self.tile_latency = MetricTile("Latency")
        self.tile_status = MetricTile("Connection")
        metrics.addWidget(self.tile_sent, 0, 0)
        metrics.addWidget(self.tile_recv, 0, 1)
        metrics.addWidget(self.tile_up, 0, 2)
        metrics.addWidget(self.tile_down, 1, 0)
        metrics.addWidget(self.tile_latency, 1, 1)
        metrics.addWidget(self.tile_status, 1, 2)
        for c in range(3):
            metrics.setColumnStretch(c, 1)
        root.addLayout(metrics)

        chart_card = make_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(18, 14, 18, 14)
        chart_layout.setSpacing(10)
        ctitle = QLabel("Live activity (interface traffic)")
        ctitle.setObjectName("h2")
        self.chart = MplCanvas(width=9, height=3.6, dark=True)
        self.chart.setMinimumHeight(260)
        self.chart_empty = QLabel("Start monitoring to see live activity")
        self.chart_empty.setObjectName("muted")
        self.chart_empty.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(ctitle)
        chart_layout.addWidget(self.chart)
        chart_layout.addWidget(self.chart_empty)
        add_shadow(chart_card)
        root.addWidget(chart_card, 1)

        note = QLabel(
            "These counters measure system-wide network interface traffic "
            "(local network + internet). They are not the same as verified "
            "internet throughput from a speed test."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 11px;")
        root.addWidget(note)

        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.interval_spin.valueChanged.connect(self._on_interval_changed)

    def start_monitoring(self) -> None:
        if self._running:
            return
        self._running = True
        self._reset_chart_data()
        self._t0 = None

        self._worker = MonitoringWorker(interval_seconds=float(self.interval_spin.value()))
        self._worker.signals.sample.connect(self._on_sample)
        self._worker.signals.error.connect(self._on_error)
        self._worker.signals.started.connect(self._on_started)
        self._worker.signals.stopped.connect(self._on_stopped)
        self._worker.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.interval_spin.setEnabled(False)
        self.tile_status.set_value("Starting…", "connecting")
        self.chart_empty.hide()
        self.chart.show()

    def stop_monitoring(self) -> None:
        if not self._running or self._worker is None:
            return
        self._worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_started(self) -> None:
        self.tile_status.set_value("Active", "monitoring")

    def _on_sample(self, sample: dict) -> None:
        now = sample.get("timestamp")
        if self._t0 is None:
            self._t0 = now
        elapsed = (now - self._t0) if self._t0 else 0

        self._times.append(elapsed)
        up = sample.get("upload_bps")
        down = sample.get("download_bps")
        lat = sample.get("latency_ms")
        self._upload_bps.append(up)
        self._download_bps.append(down)
        self._latency_ms.append(lat)

        self.tile_sent.set_value(
            format_bytes(sample.get("bytes_sent")), "interface total"
        )
        self.tile_recv.set_value(
            format_bytes(sample.get("bytes_recv")), "interface total"
        )
        self.tile_up.set_value(
            format_bits_per_sec(up), "interface upload"
        )
        self.tile_down.set_value(
            format_bits_per_sec(down), "interface download"
        )
        self.tile_latency.set_value(
            format_ms(lat), "to 1.1.1.1 (best effort)"
        )
        self._refresh_chart()

    def _on_error(self, message: str) -> None:
        self.tile_status.set_value("Error", message)
        self.stop_monitoring()

    def _on_stopped(self) -> None:
        self._running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.interval_spin.setEnabled(True)
        self.tile_status.set_value("Stopped", "monitoring ended")

    def _on_interval_changed(self, value: int) -> None:
        self._interval = float(value)
        if self._worker is not None:
            self._worker.interval_seconds = self._interval

    def _reset_chart_data(self) -> None:
        self._times.clear()
        self._download_bps.clear()
        self._upload_bps.clear()
        self._latency_ms.clear()
        self._t0 = None
        self.chart.plot_empty("Waiting for samples…")

    def _refresh_chart(self) -> None:
        if not self._times:
            return
        xs = list(self._times)
        down_mbps = [(b or 0) / 1_000_000.0 for b in self._download_bps]
        up_mbps = [(b or 0) / 1_000_000.0 for b in self._upload_bps]
        self.chart._axes.clear()
        colors = self.chart._colors
        self.chart._axes.plot(xs, down_mbps, color=colors["accent"], linewidth=1.6, label="Download (Mbps)")
        self.chart._axes.plot(xs, up_mbps, color=colors["success"], linewidth=1.6, label="Upload (Mbps)")
        self.chart._axes.set_ylabel("Mbps", color=colors["text_muted"])
        self.chart._axes.set_xlabel("Elapsed (s)", color=colors["text_muted"])
        self.chart._axes.set_title("Interface throughput", color=colors["text"], fontsize=10, pad=8)
        self.chart._axes.legend(fontsize=7, frameon=False, loc="upper left")
        self.chart._apply_style()
        self.chart.figure.tight_layout()
        self.chart.draw()

    def set_interval(self, seconds: float) -> None:
        self.interval_spin.setValue(int(seconds))

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        self.chart._colors = palette_dict(dark)
        self.chart.draw()

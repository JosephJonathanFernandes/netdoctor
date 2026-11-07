"""Speed Test page: one-click test with progressive results and cancellation."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from app.services.speed_test import SpeedTestResult, SpeedTestService, format_result_for_display
from app.ui.theme import DARK, LIGHT, add_shadow, make_card, palette_dict
from app.ui.widgets import MetricTile
from app.workers.speed_test_worker import SpeedTestWorker


class SpeedTestPage(QWidget):
    test_completed = Signal(object)

    def __init__(self, service: Optional[SpeedTestService] = None, parent=None):
        super().__init__(parent)
        self._service = service or SpeedTestService()
        self._worker: Optional[SpeedTestWorker] = None
        self._running = False
        self._dark = True

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Speed Test")
        title.setObjectName("h1")
        subtitle = QLabel("One-click download, upload and latency test")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        root.addLayout(header)

        # Control bar
        control = QHBoxLayout()
        self.start_btn = QPushButton("Start Test")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumHeight(52)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setAccessibleName("Start speed test")
        self.start_btn.setAccessibleDescription(
            "Run a one-click download, upload and latency speed test"
        )
        self.start_btn.setToolTip("Start a one-click speed test (Ctrl+R)")
        add_shadow(self.start_btn, blur=32, offset_y=8)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setMinimumHeight(52)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setAccessibleName("Cancel speed test")
        self.cancel_btn.setAccessibleDescription("Cancel the in-progress speed test")
        control.addWidget(self.start_btn)
        control.addWidget(self.cancel_btn)
        control.addStretch()
        root.addLayout(control)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("Idle")
        self.progress.setMinimumHeight(8)
        root.addWidget(self.progress)

        self.stage_label = QLabel("Ready to test")
        self.stage_label.setObjectName("muted")
        self.stage_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        root.addWidget(self.stage_label)

        # Results grid
        results = QGridLayout()
        results.setSpacing(12)
        self.tile_download = MetricTile("Download")
        self.tile_upload = MetricTile("Upload")
        self.tile_latency = MetricTile("Latency")
        self.tile_jitter = MetricTile("Jitter")
        self.tile_loss = MetricTile("Packet loss")
        self.tile_server = MetricTile("Server")
        results.addWidget(self.tile_download, 0, 0)
        results.addWidget(self.tile_upload, 0, 1)
        results.addWidget(self.tile_latency, 0, 2)
        results.addWidget(self.tile_jitter, 1, 0)
        results.addWidget(self.tile_loss, 1, 1)
        results.addWidget(self.tile_server, 1, 2)
        for c in range(3):
            results.setColumnStretch(c, 1)
        root.addLayout(results)

        # Details card
        details = make_card()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(18, 14, 18, 14)
        details_layout.setSpacing(8)
        self.detail_timestamp = QLabel("Timestamp: —")
        self.detail_timestamp.setObjectName("muted")
        self.detail_status = QLabel("Status: —")
        self.detail_status.setObjectName("muted")
        self.detail_error = QLabel("")
        self.detail_error.setObjectName("muted")
        self.detail_error.setWordWrap(True)
        self.detail_error.setStyleSheet("color: #f87171; font-size: 11px;")
        details_layout.addWidget(self.detail_timestamp)
        details_layout.addWidget(self.detail_status)
        details_layout.addWidget(self.detail_error)
        root.addWidget(details)

        root.addStretch()

        note = QLabel(
            "Results vary with server selection, Wi-Fi conditions and network load. "
            "Jitter and packet loss are estimated using ICMP ping to a diagnostic host "
            "(1.1.1.1) and are labelled as estimates, not speedtest-verified measurements."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 11px;")
        root.addWidget(note)

        self.start_btn.clicked.connect(self.start_test)
        self.cancel_btn.clicked.connect(self.cancel_test)

    def is_running(self) -> bool:
        return self._running or (self._worker is not None and self._worker.isRunning())

    def set_test_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running and not self._running)
        self.cancel_btn.setEnabled(running and self._worker is not None)

    def start_test(self) -> None:
        if self._running:
            return
        self._running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setFormat("Running…")
        self.stage_label.setText("Starting test…")
        self._clear_results()
        self.detail_error.setText("")

        self._worker = SpeedTestWorker(self._service)
        self._worker.signals.started.connect(self._on_started)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.error.connect(self._on_error)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def cancel_test(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        self.stage_label.setText("Cancelling…")
        self.cancel_btn.setEnabled(False)

    def _on_started(self) -> None:
        self.stage_label.setText("Test in progress…")

    def _on_progress(self, stage: str, message: str) -> None:
        self.stage_label.setText(message)
        stage_order = {
            "checking_connectivity": 8,
            "finding_server": 18,
            "measuring_latency": 32,
            "downloading": 58,
            "uploading": 82,
            "measuring_jitter": 92,
            "measuring_packet_loss": 96,
        }
        self.progress.setValue(stage_order.get(stage, 50))

    def _on_finished(self, result: SpeedTestResult) -> None:
        self._display_result(result)
        self.test_completed.emit(result)
        self._update_button_states(running=False)

    def _on_error(self, message: str) -> None:
        self.stage_label.setText("Error")
        self.detail_error.setText(f"Error: {message}")
        self._update_button_states(running=False)

    def _worker_finished(self) -> None:
        self._update_button_states(running=False)

    def _update_button_states(self, running: bool) -> None:
        self._running = running
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        if not running:
            self.progress.setFormat("Idle")
            self.progress.setValue(0)

    def _clear_results(self) -> None:
        for tile in (self.tile_download, self.tile_upload, self.tile_latency,
                     self.tile_jitter, self.tile_loss, self.tile_server):
            tile.set_value("—", "pending")
        self.detail_timestamp.setText("Timestamp: —")
        self.detail_status.setText("Status: —")

    def _display_result(self, result: SpeedTestResult) -> None:
        disp = format_result_for_display(result)
        self.tile_download.set_value(disp["download"], "Mbps" if disp["download"] != "n/a" else "unavailable")
        self.tile_upload.set_value(disp["upload"], "Mbps" if disp["upload"] != "n/a" else "unavailable")
        self.tile_latency.set_value(disp["latency"], "measured" if disp["latency"] != "n/a" else "unavailable")
        self.tile_jitter.set_value(disp["jitter"], "estimated" if disp["jitter"] != "n/a" else "unavailable")
        self.tile_loss.set_value(disp["packet_loss"], "ICMP estimate" if disp["packet_loss"] != "n/a" else "unavailable")
        server = disp["server"]
        if disp["server_sponsor"]:
            server = f"{server} ({disp['server_sponsor']})"
        self.tile_server.set_value(server, disp["server_country"] or "")

        self.detail_timestamp.setText(f"Timestamp: {disp['timestamp']}")
        self.detail_status.setText(f"Status: {disp['status'].capitalize()}")
        self.detail_error.setText(f"Error: {disp['error']}" if disp["error"] else "")

        if disp["status"] == "completed":
            self.stage_label.setText("Test complete.")
        elif disp["status"] == "cancelled":
            self.stage_label.setText("Test cancelled.")
        else:
            self.stage_label.setText("Test failed.")

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        colors = DARK if dark else LIGHT
        for tile in (self.tile_download, self.tile_upload, self.tile_latency,
                     self.tile_jitter, self.tile_loss, self.tile_server):
            tile.hint_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 10px;")

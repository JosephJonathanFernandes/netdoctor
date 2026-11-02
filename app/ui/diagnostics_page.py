"""Diagnostics page: real network checks presented in plain language."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from app.services.diagnostics import DiagnosticsService
from app.ui.theme import DARK, LIGHT, add_shadow, make_card, palette_dict, status_badge_color


class _DiagnosticsSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)


class _DiagnosticsWorker(QThread):
    def __init__(self, service: DiagnosticsService, parent=None):
        super().__init__(parent)
        self.service = service
        self.signals = _DiagnosticsSignals()

    def run(self) -> None:
        self.signals.started.emit()
        try:
            result = self.service.run_full_diagnostics()
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class DiagnosticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = DiagnosticsService()
        self._worker: Optional[_DiagnosticsWorker] = None
        self._dark = True

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Diagnostics")
        title.setObjectName("h1")
        subtitle = QLabel("Real connectivity, DNS, gateway and Wi-Fi checks")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        root.addLayout(header)

        control = QHBoxLayout()
        self.run_btn = QPushButton("Run Diagnostics")
        self.run_btn.setObjectName("primary")
        self.run_btn.setMinimumHeight(44)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setMinimumHeight(44)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        control.addWidget(self.run_btn)
        control.addWidget(self.cancel_btn)
        control.addStretch()
        root.addLayout(control)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("muted")
        root.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.findings_container = QWidget()
        self.findings_layout = QVBoxLayout(self.findings_container)
        self.findings_layout.setSpacing(10)
        self.findings_layout.addStretch()
        scroll.setWidget(self.findings_container)
        root.addWidget(scroll, 1)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("muted")
        root.addWidget(self.summary_label)

        self.run_btn.clicked.connect(self.run_diagnostics)
        self.cancel_btn.clicked.connect(self.cancel_diagnostics)

    def run_diagnostics(self) -> None:
        self._clear_findings()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Running diagnostics…")
        self.summary_label.setText("")

        self._worker = _DiagnosticsWorker(self._service)
        self._worker.signals.started.connect(self._on_started)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.error.connect(self._on_error)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def cancel_diagnostics(self) -> None:
        self.status_label.setText("Cancelling…")
        self.cancel_btn.setEnabled(False)

    def _on_started(self) -> None:
        self.status_label.setText("Running checks…")

    def _on_finished(self, result: dict) -> None:
        self._display_findings(result)
        self._update_controls(running=False)

    def _on_error(self, message: str) -> None:
        self.status_label.setText("Error")
        self.summary_label.setText(f"Diagnostics could not complete: {message}")
        self._update_controls(running=False)

    def _worker_finished(self) -> None:
        self._update_controls(running=False)

    def _update_controls(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)

    def _clear_findings(self) -> None:
        while self.findings_layout.count() - 1:
            item = self.findings_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _display_findings(self, result: dict) -> None:
        findings = result.get("findings", [])
        summary = result.get("summary", "")

        for finding in findings:
            card = make_card()
            status = finding.get("status", "fail")
            color = status_badge_color(status, DARK if self._dark else LIGHT)
            card.setStyleSheet(f"QFrame#card {{ border-left: 4px solid {color}; }}")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(8)

            header = QHBoxLayout()
            icons = {"pass": "✓", "warn": "⚠", "fail": "✗"}
            icon_lbl = QLabel(icons.get(status, "⚪"))
            icon_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
            title_lbl = QLabel(finding.get("title", "Check"))
            title_lbl.setStyleSheet("font-size: 14px; font-weight: 700;")
            status_lbl = QLabel(status.upper())
            status_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 800;")
            header.addWidget(icon_lbl)
            header.addWidget(title_lbl)
            header.addStretch()
            header.addWidget(status_lbl)
            layout.addLayout(header)

            obs = finding.get("observations", [])
            if obs:
                obs_lbl = QLabel("• " + "\n• ".join(obs))
                obs_lbl.setWordWrap(True)
                obs_lbl.setStyleSheet("font-size: 12px; line-height: 1.5;")
                layout.addWidget(obs_lbl)

            causes = finding.get("possible_causes", [])
            if causes:
                causes_lbl = QLabel("Possible causes: " + " ".join(causes))
                causes_lbl.setWordWrap(True)
                causes_lbl.setObjectName("muted")
                causes_lbl.setStyleSheet("font-size: 11px; font-style: italic;")
                layout.addWidget(causes_lbl)

            note = finding.get("note")
            if note:
                note_lbl = QLabel(note)
                note_lbl.setWordWrap(True)
                note_lbl.setObjectName("muted")
                note_lbl.setStyleSheet("font-size: 10px;")
                layout.addWidget(note_lbl)

            self.findings_layout.insertWidget(self.findings_layout.count() - 1, card)

        self.summary_label.setText(summary)
        self.status_label.setText(f"{len(findings)} check(s) complete")

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        colors = DARK if dark else LIGHT
        self.status_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
        self.summary_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")

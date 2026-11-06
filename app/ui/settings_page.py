"""Settings page: theme, monitoring interval, notifications, alerts, database info."""

from __future__ import annotations

import os
import platform
from typing import Optional

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from app.config import get_default_db_path
from app.ui.theme import apply_theme, DARK, LIGHT
from app.ui.widgets import StatCard
from app.utils.settings import Settings


class SettingsPage(QWidget):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._main_window = None
        self._dark = True

        self._build_ui()
        self._load_values()
        # Listen for settings changes from other parts of the app
        self._settings.add_change_listener(self._on_settings_changed)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setObjectName("h1")
        subtitle = QLabel("Preferences and application information")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        root.addLayout(header)

        # Appearance
        appearance = QGroupBox("Appearance")
        al = QVBoxLayout(appearance)
        al.setContentsMargins(16, 16, 16, 16)
        al.setSpacing(12)
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setMinimumWidth(140)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        al.addLayout(theme_row)
        self.btn_apply_theme = QPushButton("Apply theme")
        self.btn_apply_theme.setCursor(Qt.PointingHandCursor)
        al.addWidget(self.btn_apply_theme)
        root.addWidget(appearance)

        # Monitoring
        monitoring = QGroupBox("Monitoring")
        ml = QVBoxLayout(monitoring)
        ml.setContentsMargins(16, 16, 16, 16)
        ml.setSpacing(12)
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Sampling interval:"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.5, 60.0)
        self.interval_spin.setSingleStep(0.5)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setMinimumWidth(120)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        ml.addLayout(interval_row)
        self.notify_chk = QCheckBox("Enable desktop notifications")
        ml.addWidget(self.notify_chk)
        self.tray_chk = QCheckBox("Minimize to system tray")
        ml.addWidget(self.tray_chk)
        self.boot_chk = QCheckBox("Start NetDoctor on Windows boot")
        ml.addWidget(self.boot_chk)
        root.addWidget(monitoring)

        # Alerts
        alerts = QGroupBox("Alert thresholds")
        al2 = QVBoxLayout(alerts)
        al2.setContentsMargins(16, 16, 16, 16)
        al2.setSpacing(12)
        for label, attr in [
            ("Latency alert (ms):", "alert_latency"),
            ("Jitter alert (ms):", "alert_jitter"),
            ("Packet loss alert (%):", "alert_loss"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            spin = QDoubleSpinBox()
            spin.setRange(0, 10000)
            spin.setSuffix(" ms" if "latency" in attr or "jitter" in attr else " %")
            spin.setMinimumWidth(120)
            setattr(self, f"{attr}_spin", spin)
            row.addWidget(spin)
            row.addStretch()
            al2.addLayout(row)
        root.addWidget(alerts)

        # Speed test
        speedtest = QGroupBox("Speed test")
        sl = QVBoxLayout(speedtest)
        sl.setContentsMargins(16, 16, 16, 16)
        sl.setSpacing(12)
        ep_row = QHBoxLayout()
        ep_row.addWidget(QLabel("Preferred endpoint:"))
        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(["speedtest.net (default)"])
        self.endpoint_combo.setEnabled(False)
        ep_row.addWidget(self.endpoint_combo)
        ep_row.addStretch()
        sl.addLayout(ep_row)
        note = QLabel(
            "Custom speed-test endpoints are reserved for future releases. "
            "The app currently uses speedtest.net through speedtest-cli."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 11px;")
        sl.addWidget(note)
        root.addWidget(speedtest)

        # Database / app info
        info = QGroupBox("Database & application")
        il = QVBoxLayout(info)
        il.setContentsMargins(16, 16, 16, 16)
        il.setSpacing(10)
        self.db_path_label = QLabel(get_default_db_path())
        self.db_path_label.setObjectName("muted")
        self.db_path_label.setWordWrap(True)
        self.db_path_label.setStyleSheet("font-size: 11px;")
        self.app_info_label = QLabel(
            f"NetDoctor {__import__('app.config', fromlist=['APP_VERSION']).APP_VERSION}  |  "
            f"Python {platform.python_version()}  |  {platform.system()} {platform.release()}"
        )
        self.app_info_label.setObjectName("muted")
        il.addWidget(QLabel("Database location:"))
        il.addWidget(self.db_path_label)
        il.addSpacing(4)
        il.addWidget(self.app_info_label)

        btn_open_db = QPushButton("Open database folder")
        btn_open_db.setCursor(Qt.PointingHandCursor)
        btn_open_db.setMinimumHeight(36)
        il.addWidget(btn_open_db)

        btn_export_location = QPushButton("Open history export location")
        btn_export_location.setCursor(Qt.PointingHandCursor)
        btn_export_location.setMinimumHeight(36)
        il.addWidget(btn_export_location)

        root.addWidget(info)
        root.addStretch()

        self.btn_apply_theme.clicked.connect(self._apply_theme)
        btn_open_db.clicked.connect(self._open_db_folder)
        btn_export_location.clicked.connect(self._open_export_location)

    def set_main_window(self, main_window) -> None:
        self._main_window = main_window

    def _load_values(self) -> None:
        m = self._settings.model
        self.theme_combo.setCurrentIndex(0 if m.appearance.theme == "dark" else 1)
        self.interval_spin.setValue(m.monitoring.interval_seconds)
        self.notify_chk.setChecked(m.monitoring.notifications_enabled)
        self.tray_chk.setChecked(m.monitoring.minimize_to_tray)
        self.boot_chk.setChecked(m.monitoring.start_on_boot)
        self.alert_latency_spin.setValue(m.alerts.latency_ms)
        self.alert_jitter_spin.setValue(m.alerts.jitter_ms)
        self.alert_loss_spin.setValue(m.alerts.packet_loss_percent)

    def _on_settings_changed(self, model) -> None:
        """Refresh UI when settings change from elsewhere."""
        self.theme_combo.setCurrentIndex(0 if model.appearance.theme == "dark" else 1)
        self.interval_spin.setValue(model.monitoring.interval_seconds)
        self.notify_chk.setChecked(model.monitoring.notifications_enabled)
        self.tray_chk.setChecked(model.monitoring.minimize_to_tray)
        self.boot_chk.setChecked(model.monitoring.start_on_boot)
        self.alert_latency_spin.setValue(model.alerts.latency_ms)
        self.alert_jitter_spin.setValue(model.alerts.jitter_ms)
        self.alert_loss_spin.setValue(model.alerts.packet_loss_percent)

    def _apply_theme(self) -> None:
        dark = self.theme_combo.currentIndex() == 0
        from PySide6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), dark=dark)
        self._settings.theme = "dark" if dark else "light"
        self._settings.sync()
        if self._main_window is not None:
            self._main_window.apply_theme_to_pages(dark)

    def _open_db_folder(self) -> None:
        folder = os.path.dirname(get_default_db_path())
        self._open_folder(folder)

    def _open_export_location(self) -> None:
        folder = self._settings.db_export_dir or os.path.dirname(get_default_db_path())
        self._open_folder(folder)

    def _open_folder(self, folder: str) -> None:
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Not found", f"Folder not found:\n{folder}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

"""Main window for NetDoctor: sidebar navigation, pages, tray, notifications."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QMenu, QPushButton, QStackedWidget, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)

from app.config import APP_NAME, APP_VERSION
from app.database.repository import SpeedTestRepository
from app.services.notifications import NotificationService
from app.services.report_export import ReportService
from app.services.speed_test import SpeedTestResult, SpeedTestService
from app.ui.dashboard import DashboardPage
from app.ui.diagnostics_page import DiagnosticsPage
from app.ui.history_page import HistoryPage
from app.ui.monitor_page import MonitorPage
from app.ui.settings_page import SettingsPage
from app.ui.speed_test_page import SpeedTestPage
from app.ui.theme import apply_theme
from app.utils.logging import configure_logging, get_logger
from app.utils.settings import Settings

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window.

    Coordinates the sidebar navigation, stacked pages, system tray, desktop
    notifications, and background workers. Owns the shared services (settings,
    repository, speed-test service) and ensures clean shutdown.
    """

    def __init__(self):
        super().__init__()
        configure_logging()
        logger.info("NetDoctor %s starting", APP_VERSION)

        self.setWindowTitle(f"{APP_NAME} — Internet Speed Test & Network Health")
        self.setMinimumSize(1050, 720)
        self.resize(1300, 850)

        # Core services
        self._settings = Settings()
        self._repo = SpeedTestRepository()
        self._service = SpeedTestService()
        self._report_service = ReportService(self._repo)

        # UI state
        self._dark = self._settings.theme == "dark"
        self._pages = {}
        self._tray = None
        self._closing = False
        self._notification_service = None

        self._build_ui()
        self._build_tray()

        apply_theme(QApplication.instance(), dark=self._dark)
        self.setWindowIcon(self._create_app_icon())
        self.statusBar().showMessage("Ready")
        logger.info("Main window initialized")

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(
            "QFrame#sidebar { background-color: #161622; border-right: 1px solid #2a2a3c; }"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 14)
        sidebar_layout.setSpacing(8)

        app_label = QLabel(APP_NAME)
        app_label.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #89b4fa; padding-bottom: 14px;"
        )
        sidebar_layout.addWidget(app_label)

        self._nav_buttons = []
        nav_items = [
            ("dashboard", "Dashboard"),
            ("speed_test", "Speed Test"),
            ("monitor", "Network Monitor"),
            ("history", "Test History"),
            ("diagnostics", "Diagnostics"),
            ("settings", "Settings"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("sidebar")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append((key, btn))

        sidebar_layout.addStretch()
        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet("font-size: 10px; color: #64748b;")
        sidebar_layout.addWidget(ver)

        # Pages
        self._stack = QStackedWidget()
        self._pages["dashboard"] = DashboardPage()
        self._pages["speed_test"] = SpeedTestPage(service=self._service)
        self._pages["monitor"] = MonitorPage(
            interval_seconds=self._settings.monitoring_interval
        )
        self._pages["history"] = HistoryPage()
        self._pages["diagnostics"] = DiagnosticsPage()
        self._pages["settings"] = SettingsPage(settings=self._settings)

        for page in self._pages.values():
            self._stack.addWidget(page)

        # Cross-page wiring
        dashboard: DashboardPage = self._pages["dashboard"]
        dashboard.set_run_handler(self.start_speed_test)

        settings: SettingsPage = self._pages["settings"]
        settings.set_main_window(self)

        speed_page: SpeedTestPage = self._pages["speed_test"]
        speed_page.test_completed.connect(self._on_speed_test_completed)

        root.addWidget(sidebar)
        root.addWidget(self._stack, 1)

        self._show_dashboard()
        self._nav_buttons[0][1].setChecked(True)

    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this system")
            return
        self._tray = QSystemTrayIcon(self._create_app_icon(), self)
        self._tray.setToolTip(APP_NAME)
        self._notification_service = NotificationService(self._tray)
        self._notification_service.set_enabled(self._settings.notifications_enabled)

        menu = QMenu()
        act_show = QAction("Show", self)
        act_show.triggered.connect(self._show_from_tray)
        act_test = QAction("Run Speed Test", self)
        act_test.triggered.connect(self._tray_speed_test)
        act_export = QAction("Export Report (HTML)", self)
        act_export.triggered.connect(self._export_report)
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_show)
        menu.addAction(act_test)
        menu.addSeparator()
        menu.addAction(act_export)
        menu.addSeparator()
        menu.addAction(act_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
        logger.info("System tray initialized")

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #
    def _set_active_nav(self, key: str) -> None:
        for k, btn in self._nav_buttons:
            btn.setChecked(k == key)

    def _show_dashboard(self) -> None:
        self._set_active_nav("dashboard")
        self._stack.setCurrentWidget(self._pages["dashboard"])
        self._pages["dashboard"].refresh()

    def _show_speed_test(self) -> None:
        self._set_active_nav("speed_test")
        self._stack.setCurrentWidget(self._pages["speed_test"])

    def _show_monitor(self) -> None:
        self._set_active_nav("monitor")
        self._stack.setCurrentWidget(self._pages["monitor"])

    def _show_history(self) -> None:
        self._set_active_nav("history")
        self._pages["history"].refresh()
        self._stack.setCurrentWidget(self._pages["history"])

    def _show_diagnostics(self) -> None:
        self._set_active_nav("diagnostics")
        self._stack.setCurrentWidget(self._pages["diagnostics"])

    def _show_settings(self) -> None:
        self._set_active_nav("settings")
        self._stack.setCurrentWidget(self._pages["settings"])

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #
    def apply_theme_to_pages(self, dark: bool) -> None:
        self._dark = dark
        for page in self._pages.values():
            if hasattr(page, "apply_theme"):
                page.apply_theme(dark)

    # ------------------------------------------------------------------ #
    # Speed test orchestration
    # ------------------------------------------------------------------ #
    def start_speed_test(self) -> None:
        speed_page: SpeedTestPage = self._pages["speed_test"]
        if speed_page.is_running():
            QMessageBox.information(
                self, "Test already running",
                "A speed test is already in progress. Wait for it to finish or cancel it."
            )
            return
        self.statusBar().showMessage("Starting speed test…")
        speed_page.start_test()
        self._show_speed_test()

    def cancel_speed_test(self) -> None:
        speed_page: SpeedTestPage = self._pages["speed_test"]
        speed_page.cancel_test()

    def _on_speed_test_completed(self, result: SpeedTestResult) -> None:
        status = result.status
        self.statusBar().showMessage(f"Speed test {status}.")

        try:
            self._repo.insert(result.to_dict())
        except Exception as exc:
            logger.exception("Failed to persist speed test result")
            self.statusBar().showMessage(f"Result saved with warning: {exc}")

        self._pages["dashboard"].refresh()
        self._pages["history"].refresh()

        # Threshold-based alerts
        self._check_alerts(result)

        # Desktop notification
        if self._notification_service:
            if status == "completed":
                dl = result.download_mbps
                ul = result.upload_mbps
                msg = (
                    f"Download {dl:.2f} Mbps  •  Upload {ul:.2f} Mbps"
                    if dl is not None and ul is not None
                    else "Test completed."
                )
                self._notification_service.notify("NetDoctor — Speed test complete", msg)
            elif status == "failed":
                self._notification_service.notify(
                    "NetDoctor — Speed test failed",
                    result.error_message or "Unknown error",
                )

    def _check_alerts(self, result: SpeedTestResult) -> None:
        """Emit notifications when measurements cross configured thresholds."""
        ns = self._notification_service
        if not ns:
            return
        settings = self._settings
        alerts = []
        if result.latency_ms is not None and result.latency_ms > settings.alert_latency_ms:
            alerts.append(("latency", result.latency_ms, settings.alert_latency_ms,
                           f"High latency: {result.latency_ms:.0f} ms (threshold {settings.alert_latency_ms:.0f} ms)"))
        if result.jitter_ms is not None and result.jitter_ms > settings.alert_jitter_ms:
            alerts.append(("jitter", result.jitter_ms, settings.alert_jitter_ms,
                           f"High jitter: {result.jitter_ms:.0f} ms (threshold {settings.alert_jitter_ms:.0f} ms)"))
        if result.packet_loss_percent is not None and result.packet_loss_percent > settings.alert_packet_loss_percent:
            alerts.append(("packet_loss", result.packet_loss_percent, settings.alert_packet_loss_percent,
                           f"Packet loss: {result.packet_loss_percent:.1f}% (threshold {settings.alert_packet_loss_percent:.1f}%)"))
        for metric, value, threshold, message in alerts:
            logger.warning("Alert triggered: %s", message)
            ns.notify("NetDoctor alert", message)

    # ------------------------------------------------------------------ #
    # Reports
    # ------------------------------------------------------------------ #
    def _export_report(self) -> None:
        records = self._repo.fetch_all()
        if not records:
            QMessageBox.information(self, "No data", "No speed-test records to export.")
            return
        path, selected = QFileDialog.getSaveFileName(
            self, "Export Report", "netdoctor_report.html",
            "HTML Report (*.html);;PDF Report (*.pdf)",
        )
        if not path:
            return
        try:
            if path.lower().endswith(".pdf"):
                written = self._report_service.export_pdf(path, records)
            else:
                if not path.lower().endswith(".html"):
                    path += ".html"
                written = self._report_service.export_html(path, records)
            QMessageBox.information(
                self, "Report Exported",
                f"Exported {written} record(s) to {path}.",
            )
        except Exception as exc:
            logger.exception("Report export failed")
            QMessageBox.critical(self, "Export Failed", str(exc))

    # ------------------------------------------------------------------ #
    # Tray
    # ------------------------------------------------------------------ #
    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_speed_test(self) -> None:
        self._show_from_tray()
        self.start_speed_test()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_from_tray()

    def _quit_app(self) -> None:
        self.close()

    def _notify_tray(self, title: str, message: str) -> None:
        if self._tray is not None:
            try:
                self._tray.showMessage(title, message, QSystemTrayIcon.Information, 5000)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Shutdown / window events
    # ------------------------------------------------------------------ #
    def _shutdown(self) -> None:
        self._closing = True
        logger.info("Shutting down NetDoctor")
        speed_page = self._pages.get("speed_test")
        if speed_page is not None and speed_page.is_running():
            speed_page.cancel_test()
        monitor_page = self._pages.get("monitor")
        if monitor_page is not None and getattr(monitor_page, "_worker", None) is not None:
            monitor_page.stop_monitoring()

    def closeEvent(self, event) -> None:
        if self._closing:
            event.accept()
            return
        if self._settings.minimize_to_tray and self._tray is not None:
            event.ignore()
            self.hide()
            self._notify_tray("NetDoctor", "Still running in the system tray")
        else:
            self._shutdown()
            event.accept()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if (
            self.isMinimized()
            and self._settings.minimize_to_tray
            and self._tray is not None
            and not self._closing
        ):
            QTimer.singleShot(0, self.hide)

    # ------------------------------------------------------------------ #
    # Icon
    # ------------------------------------------------------------------ #
    def _create_app_icon(self) -> QIcon:
        size = 256
        pix = QPixmap(size, size)
        pix.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#89b4fa"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(18, 18, size - 36, size - 36, 40, 40)

        painter.setBrush(Qt.NoBrush)
        arc_pen = painter.pen()
        arc_pen.setColor(QColor("#ffffff"))
        arc_pen.setWidth(10)
        painter.setPen(arc_pen)
        rect = pix.rect().adjusted(55, 55, -55, -55)
        for i in range(3):
            span = int(270 - i * 25)
            painter.drawArc(rect, 45 * 16, span * 16)
            rect = rect.adjusted(14, 14, -14, -14)

        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(size // 2 - 10, size // 2 - 10, 20, 20)

        painter.end()
        return QIcon(pix)

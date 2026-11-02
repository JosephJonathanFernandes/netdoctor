"""Local application settings persisted with QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings

ORGANIZATION = "NetDoctor"
APPLICATION = "NetDoctor"


class Settings:
    DEFAULTS = {
        "theme": "dark",
        "monitoring_interval": 2.0,
        "speedtest_endpoint": "",
        "chart_time_range": "15min",
        "notifications_enabled": True,
        "minimize_to_tray": False,
        "start_on_windows_boot": False,
        "db_export_dir": "",
        "window_geometry": None,
        "alert_latency_ms": 100.0,
        "alert_jitter_ms": 30.0,
        "alert_packet_loss_percent": 2.0,
        "auto_run_speed_test": False,
        "favorite_server": "",
    }

    def __init__(self):
        self._settings = QSettings(ORGANIZATION, APPLICATION)
        for key, default in self.DEFAULTS.items():
            if not self._settings.contains(key):
                self._settings.setValue(key, default)

    def get(self, key: str):
        return self._settings.value(key, self.DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self._settings.setValue(key, value)

    def remove(self, key: str) -> None:
        self._settings.remove(key)

    def sync(self) -> None:
        self._settings.sync()

    # Typed helpers ---------------------------------------------------- #
    def theme(self) -> str:
        return str(self.get("theme") or "dark")

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    def monitoring_interval(self) -> float:
        try:
            return float(self.get("monitoring_interval") or 2.0)
        except (TypeError, ValueError):
            return 2.0

    def set_monitoring_interval(self, seconds: float) -> None:
        self.set("monitoring_interval", float(seconds))

    def chart_time_range(self) -> str:
        return str(self.get("chart_time_range") or "15min")

    def set_chart_time_range(self, value: str) -> None:
        self.set("chart_time_range", value)

    def notifications_enabled(self) -> bool:
        return bool(self.get("notifications_enabled"))

    def set_notifications_enabled(self, enabled: bool) -> None:
        self.set("notifications_enabled", bool(enabled))

    def minimize_to_tray(self) -> bool:
        return bool(self.get("minimize_to_tray"))

    def set_minimize_to_tray(self, enabled: bool) -> None:
        self.set("minimize_to_tray", bool(enabled))

    def start_on_boot(self) -> bool:
        return bool(self.get("start_on_windows_boot"))

    def set_start_on_boot(self, enabled: bool) -> None:
        self.set("start_on_windows_boot", bool(enabled))

    def db_export_dir(self) -> str:
        return str(self.get("db_export_dir") or "")

    def set_db_export_dir(self, path: str) -> None:
        self.set("db_export_dir", path)

    def alert_latency_ms(self) -> float:
        try:
            return float(self.get("alert_latency_ms") or 100.0)
        except (TypeError, ValueError):
            return 100.0

    def set_alert_latency_ms(self, value: float) -> None:
        self.set("alert_latency_ms", float(value))

    def alert_jitter_ms(self) -> float:
        try:
            return float(self.get("alert_jitter_ms") or 30.0)
        except (TypeError, ValueError):
            return 30.0

    def set_alert_jitter_ms(self, value: float) -> None:
        self.set("alert_jitter_ms", float(value))

    def alert_packet_loss_percent(self) -> float:
        try:
            return float(self.get("alert_packet_loss_percent") or 2.0)
        except (TypeError, ValueError):
            return 2.0

    def set_alert_packet_loss_percent(self, value: float) -> None:
        self.set("alert_packet_loss_percent", float(value))

    def auto_run_speed_test(self) -> bool:
        return bool(self.get("auto_run_speed_test"))

    def set_auto_run_speed_test(self, enabled: bool) -> None:
        self.set("auto_run_speed_test", bool(enabled))

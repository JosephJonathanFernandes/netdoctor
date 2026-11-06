"""Pydantic-based application settings with validation.

Replaces the plain QSettings wrapper with typed, validated configuration.
Persisted to QSettings under the hood but exposed through Pydantic models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from PySide6.QtCore import QSettings

from app.config import APPLICATION, ORGANIZATION
from app.utils.logging import get_logger

logger = get_logger(__name__)

Theme = Literal["dark", "light"]
ChartRange = Literal["5min", "15min", "1h"]


class AppearanceSettings(BaseModel):
    theme: Theme = "dark"
    chart_time_range: ChartRange = "15min"


class MonitoringSettings(BaseModel):
    interval_seconds: float = Field(default=2.0, ge=0.5, le=60.0)
    notifications_enabled: bool = True
    minimize_to_tray: bool = False
    start_on_boot: bool = False

    @field_validator("interval_seconds")
    @classmethod
    def _round_interval(cls, v: float) -> float:
        return round(v, 1)


class AlertSettings(BaseModel):
    latency_ms: float = Field(default=100.0, ge=0.0)
    jitter_ms: float = Field(default=30.0, ge=0.0)
    packet_loss_percent: float = Field(default=2.0, ge=0.0, le=100.0)


class SpeedTestSettings(BaseModel):
    endpoint: str = "speedtest.net (default)"
    auto_run: bool = False
    favorite_server: str = ""


class AppSettings(BaseModel):
    """Top-level settings model."""

    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    alerts: AlertSettings = Field(default_factory=AlertSettings)
    speedtest: SpeedTestSettings = Field(default_factory=SpeedTestSettings)
    db_export_dir: str = ""
    window_geometry: Optional[str] = None

    @model_validator(mode="after")
    def _validate(self) -> "AppSettings":
        # Ensure db_export_dir exists if set
        if self.db_export_dir and not Path(self.db_export_dir).exists():
            logger.warning("Export directory does not exist: %s", self.db_export_dir)
        return self


class Settings:
    """Typed settings wrapper backed by QSettings.

    Provides Pydantic-validated configuration with change callbacks.
    """

    def __init__(self):
        self._qt = QSettings(ORGANIZATION, APPLICATION)
        self._model = self._load()
        self._change_listeners: list[callable] = []

    def _load(self) -> AppSettings:
        data: dict[str, Any] = {
            "appearance": {
                "theme": self._qt.value("appearance/theme", "dark"),
                "chart_time_range": self._qt.value(
                    "appearance/chart_time_range", "15min"
                ),
            },
            "monitoring": {
                "interval_seconds": float(
                    self._qt.value("monitoring/interval_seconds", 2.0)
                ),
                "notifications_enabled": self._qt.value(
                    "monitoring/notifications_enabled", True, type=bool
                ),
                "minimize_to_tray": self._qt.value(
                    "monitoring/minimize_to_tray", False, type=bool
                ),
                "start_on_boot": self._qt.value(
                    "monitoring/start_on_boot", False, type=bool
                ),
            },
            "alerts": {
                "latency_ms": float(self._qt.value("alerts/latency_ms", 100.0)),
                "jitter_ms": float(self._qt.value("alerts/jitter_ms", 30.0)),
                "packet_loss_percent": float(
                    self._qt.value("alerts/packet_loss_percent", 2.0)
                ),
            },
            "speedtest": {
                "endpoint": self._qt.value(
                    "speedtest/endpoint", "speedtest.net (default)"
                ),
                "auto_run": self._qt.value("speedtest/auto_run", False, type=bool),
                "favorite_server": self._qt.value(
                    "speedtest/favorite_server", ""
                ),
            },
            "db_export_dir": self._qt.value("db_export_dir", ""),
            "window_geometry": self._qt.value("window_geometry", None),
        }
        try:
            return AppSettings(**data)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to load settings; using defaults")
            return AppSettings()

    def _save(self) -> None:
        m = self._model
        self._qt.setValue("appearance/theme", m.appearance.theme)
        self._qt.setValue(
            "appearance/chart_time_range", m.appearance.chart_time_range
        )
        self._qt.setValue(
            "monitoring/interval_seconds", m.monitoring.interval_seconds
        )
        self._qt.setValue(
            "monitoring/notifications_enabled", m.monitoring.notifications_enabled
        )
        self._qt.setValue(
            "monitoring/minimize_to_tray", m.monitoring.minimize_to_tray
        )
        self._qt.setValue(
            "monitoring/start_on_boot", m.monitoring.start_on_boot
        )
        self._qt.setValue("alerts/latency_ms", m.alerts.latency_ms)
        self._qt.setValue("alerts/jitter_ms", m.alerts.jitter_ms)
        self._qt.setValue(
            "alerts/packet_loss_percent", m.alerts.packet_loss_percent
        )
        self._qt.setValue("speedtest/endpoint", m.speedtest.endpoint)
        self._qt.setValue("speedtest/auto_run", m.speedtest.auto_run)
        self._qt.setValue("speedtest/favorite_server", m.speedtest.favorite_server)
        self._qt.setValue("db_export_dir", m.db_export_dir)
        if m.window_geometry is not None:
            self._qt.setValue("window_geometry", m.window_geometry)
        self._qt.sync()

    # ------------------------------------------------------------------ #
    # Typed accessors
    # ------------------------------------------------------------------ #
    @property
    def model(self) -> AppSettings:
        return self._model

    @property
    def theme(self) -> Theme:
        return self._model.appearance.theme

    @theme.setter
    def theme(self, value: Theme) -> None:
        self._model.appearance.theme = value
        self._save()
        self._notify()

    @property
    def chart_time_range(self) -> ChartRange:
        return self._model.appearance.chart_time_range

    @chart_time_range.setter
    def chart_time_range(self, value: ChartRange) -> None:
        self._model.appearance.chart_time_range = value
        self._save()
        self._notify()

    @property
    def monitoring_interval(self) -> float:
        return self._model.monitoring.interval_seconds

    @monitoring_interval.setter
    def monitoring_interval(self, value: float) -> None:
        self._model.monitoring.interval_seconds = round(float(value), 1)
        self._save()
        self._notify()

    @property
    def notifications_enabled(self) -> bool:
        return self._model.monitoring.notifications_enabled

    @notifications_enabled.setter
    def notifications_enabled(self, value: bool) -> None:
        self._model.monitoring.notifications_enabled = bool(value)
        self._save()
        self._notify()

    @property
    def minimize_to_tray(self) -> bool:
        return self._model.monitoring.minimize_to_tray

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool) -> None:
        self._model.monitoring.minimize_to_tray = bool(value)
        self._save()
        self._notify()

    @property
    def start_on_boot(self) -> bool:
        return self._model.monitoring.start_on_boot

    @start_on_boot.setter
    def start_on_boot(self, value: bool) -> None:
        self._model.monitoring.start_on_boot = bool(value)
        self._save()
        self._notify()

    @property
    def alert_latency_ms(self) -> float:
        return self._model.alerts.latency_ms

    @alert_latency_ms.setter
    def alert_latency_ms(self, value: float) -> None:
        self._model.alerts.latency_ms = float(value)
        self._save()
        self._notify()

    @property
    def alert_jitter_ms(self) -> float:
        return self._model.alerts.jitter_ms

    @alert_jitter_ms.setter
    def alert_jitter_ms(self, value: float) -> None:
        self._model.alerts.jitter_ms = float(value)
        self._save()
        self._notify()

    @property
    def alert_packet_loss_percent(self) -> float:
        return self._model.alerts.packet_loss_percent

    @alert_packet_loss_percent.setter
    def alert_packet_loss_percent(self, value: float) -> None:
        self._model.alerts.packet_loss_percent = float(value)
        self._save()
        self._notify()

    @property
    def db_export_dir(self) -> str:
        return self._model.db_export_dir or ""

    @db_export_dir.setter
    def db_export_dir(self, value: str) -> None:
        self._model.db_export_dir = value or ""
        self._save()
        self._notify()

    # ------------------------------------------------------------------ #
    # Change notification
    # ------------------------------------------------------------------ #
    def add_change_listener(self, callback: callable) -> None:
        self._change_listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._change_listeners:
            try:
                cb(self._model)
            except Exception:  # pragma: no cover - defensive
                logger.exception("Settings change listener failed")

    def sync(self) -> None:
        self._qt.sync()

"""Dashboard page: at-a-glance network health with animated stat cards."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import CHART_COLOR_PRIMARY
from app.database.repository import SpeedTestRepository
from app.services.health_score import HealthScoreService
from app.services.recommendations import RecommendationsEngine
from app.ui.chart import MplCanvas
from app.ui.theme import (
    DARK,
    LIGHT,
    add_shadow,
    make_card,
    palette_dict,
    status_badge_color,
)
from app.ui.widgets import StatCard


class _GlowLabel(QLabel):
    """Label that pulses gently to indicate live status."""

    def __init__(self, text: str = "●", parent=None):
        super().__init__(text, parent)
        self._alpha = 255
        self._going_down = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.start(120)
        self.setStyleSheet("color: #34d399; font-size: 10px; font-weight: bold;")

    def _pulse(self):
        step = 15
        if self._going_down:
            self._alpha -= step
            if self._alpha <= 120:
                self._going_down = False
        else:
            self._alpha += step
            if self._alpha >= 255:
                self._going_down = True
        color = QColor(52, 211, 153, self._alpha)
        self.setStyleSheet(f"color: {color.name(QColor.HexArgb)}; font-size: 10px; font-weight: bold;")


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = SpeedTestRepository()
        self._health = HealthScoreService()
        self._engine = RecommendationsEngine()
        self._dark = True
        self._monitoring_active = False
        self._session_start = datetime.now(UTC)
        self._previous_score: int | None = None

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("h1")
        subtitle = QLabel("Your network health at a glance")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        self.status_indicator = _GlowLabel("● ONLINE")
        self.status_indicator.setFixedWidth(90)
        header.addWidget(self.status_indicator)
        root.addLayout(header)

        # Stat row
        stats = QGridLayout()
        stats.setSpacing(12)
        self.card_status = StatCard("Connection", "Checking…", "Internet reachability", icon="🌐")
        self.card_download = StatCard("Last download", "n/a", "Most recent speed test", icon="⬇")
        self.card_upload = StatCard("Last upload", "n/a", "Most recent speed test", icon="⬆")
        self.card_latency = StatCard("Latency", "n/a", "Latest measurement", icon="⏱")
        stats.addWidget(self.card_status, 0, 0)
        stats.addWidget(self.card_download, 0, 1)
        stats.addWidget(self.card_upload, 0, 2)
        stats.addWidget(self.card_latency, 0, 3)
        for c in range(4):
            stats.setColumnStretch(c, 1)
        root.addLayout(stats)

        # Middle row: health score + uptime
        mid = QHBoxLayout()
        mid.setSpacing(16)

        self.health_card = make_card()
        self.health_card.setFixedHeight(210)
        health_layout = QVBoxLayout(self.health_card)
        health_layout.setContentsMargins(20, 18, 20, 18)
        health_layout.setSpacing(10)
        self.health_title = QLabel("Internet health score")
        self.health_title.setObjectName("h2")
        self.health_value = QLabel("n/a")
        self.health_value.setStyleSheet("font-size: 40px; font-weight: 800;")
        self.health_message = QLabel("Run a speed test to complete the assessment.")
        self.health_message.setObjectName("muted")
        self.health_message.setWordWrap(True)
        self.health_recs = QLabel("")
        self.health_recs.setObjectName("muted")
        self.health_recs.setWordWrap(True)
        self.health_recs.setStyleSheet("font-size: 11px; margin-top: 6px;")
        health_layout.addWidget(self.health_title)
        health_layout.addWidget(self.health_value)
        health_layout.addWidget(self.health_message)
        health_layout.addWidget(self.health_recs)
        health_layout.addStretch()
        add_shadow(self.health_card)
        mid.addWidget(self.health_card, 1)

        self.uptime_card = make_card()
        self.uptime_card.setFixedHeight(210)
        uptime_layout = QVBoxLayout(self.uptime_card)
        uptime_layout.setContentsMargins(20, 18, 20, 18)
        uptime_layout.setSpacing(10)
        self.uptime_title = QLabel("Session uptime")
        self.uptime_title.setObjectName("h2")
        self.uptime_value = QLabel("00:00:00")
        self.uptime_value.setStyleSheet("font-size: 32px; font-weight: 800;")
        self.uptime_sub = QLabel("Current monitoring session")
        self.uptime_sub.setObjectName("muted")
        uptime_layout.addWidget(self.uptime_title)
        uptime_layout.addWidget(self.uptime_value)
        uptime_layout.addWidget(self.uptime_sub)
        uptime_layout.addStretch()
        add_shadow(self.uptime_card)
        mid.addWidget(self.uptime_card, 1)

        root.addLayout(mid)

        # Run speed test button (prominent)
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Run Speed Test")
        self.run_btn.setObjectName("primary")
        self.run_btn.setMinimumHeight(52)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        add_shadow(self.run_btn, blur=32, offset_y=8)
        btn_row.addWidget(self.run_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # Bottom row: recent history + health trend chart
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        hist_card = make_card()
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(18, 14, 18, 14)
        hist_layout.setSpacing(10)
        htitle = QLabel("Recent speed tests")
        htitle.setObjectName("h2")
        self.history_list = QVBoxLayout()
        self.history_list.setSpacing(8)
        hist_container = QWidget()
        hist_container.setLayout(self.history_list)
        hist_layout.addWidget(htitle)
        hist_layout.addWidget(hist_container)
        hist_layout.addStretch()
        bottom.addWidget(hist_card, 1)

        chart_card = make_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(18, 14, 18, 14)
        chart_layout.setSpacing(10)
        ctitle = QLabel("Health score trend")
        ctitle.setObjectName("h2")
        self.chart = MplCanvas(width=7, height=3.4, dark=True)
        self.chart.setMinimumHeight(240)
        self.chart_empty = QLabel("Run speed tests to see health trends")
        self.chart_empty.setObjectName("muted")
        self.chart_empty.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(ctitle)
        chart_layout.addWidget(self.chart)
        chart_layout.addWidget(self.chart_empty)
        bottom.addWidget(chart_card, 1)

        root.addLayout(bottom, 1)

        # Uptime timer
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)
        self._uptime_timer.start(1000)

    def set_run_handler(self, handler) -> None:
        self.run_btn.clicked.connect(handler)

    def set_monitoring_active(self, active: bool) -> None:
        self._monitoring_active = active

    def refresh(self) -> None:
        self._update_last_test()
        self._update_health()
        self._update_history()
        self._refresh_chart()

    # ------------------------------------------------------------------ #
    def _update_last_test(self) -> None:
        latest = self._repo.latest()
        if not latest:
            self.card_status.set_value("No tests", "Run a speed test")
            self.card_download.set_value("n/a", "No download measurement yet")
            self.card_upload.set_value("n/a", "No upload measurement yet")
            self.card_latency.set_value("n/a", "No latency measurement yet")
            return

        status = latest.get("status") or "unknown"
        if status == "completed":
            self.card_status.set_value("Online", "Last test completed")
        elif status == "failed":
            self.card_status.set_value("Issues", "Last test failed")
        else:
            self.card_status.set_value("Unknown", status.capitalize())

        dl = latest.get("download_mbps")
        ul = latest.get("upload_mbps")
        lat = latest.get("latency_ms")
        self.card_download.set_value(
            f"{dl:.2f} Mbps" if dl is not None else "n/a",
            "Last download speed" if dl is not None else "Unavailable",
        )
        self.card_upload.set_value(
            f"{ul:.2f} Mbps" if ul is not None else "n/a",
            "Last upload speed" if ul is not None else "Unavailable",
        )
        self.card_latency.set_value(
            f"{lat:.1f} ms" if lat is not None else "n/a",
            "Latest latency" if lat is not None else "Unavailable",
        )

    def _update_health(self) -> None:
        latest = self._repo.latest()
        if not latest:
            self.health_value.setText("n/a")
            self.health_message.setText("Run a speed test to complete the assessment.")
            self.health_recs.setText("")
            return

        score = self._health.compute(
            latency_ms=latest.get("latency_ms"),
            jitter_ms=latest.get("jitter_ms"),
            packet_loss_percent=latest.get("packet_loss_percent"),
            download_mbps=latest.get("download_mbps"),
            upload_mbps=latest.get("upload_mbps"),
            previous_score=self._previous_score,
        )
        if score.complete and score.score is not None:
            self.health_value.setText(f"{score.score}/100")
            self._previous_score = score.score
        else:
            self.health_value.setText("incomplete")
        self.health_message.setText(score.message)

        engine = RecommendationsEngine()
        recs = engine.build(
            latency_ms=latest.get("latency_ms"),
            jitter_ms=latest.get("jitter_ms"),
            packet_loss_percent=latest.get("packet_loss_percent"),
            download_mbps=latest.get("download_mbps"),
            upload_mbps=latest.get("upload_mbps"),
            alert_latency_ms=100.0,
            alert_jitter_ms=30.0,
            alert_packet_loss_percent=2.0,
        )
        if recs:
            top = recs[0]
            self.health_recs.setText(f"Recommendation: {top.title} — {top.message}")
        else:
            self.health_recs.setText("")

    def _update_history(self) -> None:
        while self.history_list.count():
            item = self.history_list.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        records = self._repo.fetch_all(limit=5)
        if not records:
            empty = QLabel("No speed-test history yet.")
            empty.setObjectName("muted")
            self.history_list.addWidget(empty)
            return

        for rec in records:
            row = QHBoxLayout()
            row.setSpacing(10)
            ts = rec.get("timestamp") or "n/a"
            try:
                dt = datetime.fromisoformat(ts)
                ts_disp = dt.strftime("%m/%d %H:%M")
            except (ValueError, TypeError):
                ts_disp = str(ts)

            time_lbl = QLabel(ts_disp)
            time_lbl.setStyleSheet("font-weight: 700; min-width: 70px;")
            dl = rec.get("download_mbps")
            ul = rec.get("upload_mbps")
            lat = rec.get("latency_ms")
            status = rec.get("status") or "—"

            dl_lbl = QLabel(f"{dl:.2f} Mbps" if dl is not None else "n/a")
            ul_lbl = QLabel(f"{ul:.2f} Mbps" if ul is not None else "n/a")
            lat_lbl = QLabel(f"{lat:.1f} ms" if lat is not None else "n/a")
            stat_lbl = QLabel(status)
            stat_lbl.setObjectName("muted")
            color = status_badge_color(status, DARK if self._dark else LIGHT)
            stat_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 700; min-width: 70px;")

            row.addWidget(time_lbl)
            row.addWidget(dl_lbl)
            row.addWidget(ul_lbl)
            row.addWidget(lat_lbl)
            row.addStretch()
            row.addWidget(stat_lbl)

            row_widget = QWidget()
            row_widget.setLayout(row)
            row_widget.setObjectName("stat_tile")
            row_widget.setStyleSheet(
                "QWidget#stat_tile { background: transparent; border: none; border-radius: 8px; }"
                "QWidget#stat_tile:hover { background: rgba(137, 180, 250, 0.08); }"
            )
            self.history_list.addWidget(row_widget)

    def _refresh_chart(self) -> None:
        """Plot health score trend from stored history."""
        history = self._health.get_history()
        scores = [r.score for r in history if r.complete and r.score is not None]
        if scores:
            xs = list(range(len(scores)))
            self.chart.plot_line(
                xs, scores, color=CHART_COLOR_PRIMARY,
                ylabel="Score / 100", title="Health score trend",
            )
            self.chart_empty.hide()
            self.chart.show()
        else:
            self.chart.hide()
            self.chart_empty.show()

    def _update_uptime(self) -> None:
        delta = datetime.now(UTC) - self._session_start
        total_seconds = int(delta.total_seconds())
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        self.uptime_value.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        colors = DARK if dark else LIGHT
        self.chart_empty.setStyleSheet(f"color: {colors['text_muted']};")
        self.chart._colors = palette_dict(dark)
        self.chart.draw()

    request_speed_test = None

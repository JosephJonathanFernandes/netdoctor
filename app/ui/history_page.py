"""Test History page: sortable table, date filtering, graphs, stats, export."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repository import (
    SpeedTestRepository,
    export_speed_tests_csv,
    export_speed_tests_json,
)
from app.services.report_export import ReportService
from app.ui.chart import MplCanvas
from app.ui.theme import DARK, add_shadow, make_card, palette_dict


class HistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = SpeedTestRepository()
        self._report_service = ReportService(self._repo)
        self._records = []
        self._dark = True

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Test History")
        title.setObjectName("h1")
        subtitle = QLabel("Saved speed-test results")
        subtitle.setObjectName("muted")
        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        header_col.addWidget(title)
        header_col.addWidget(subtitle)
        header.addLayout(header_col)
        header.addStretch()
        root.addLayout(header)

        # Filters
        filter_card = make_card()
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        self.use_filter = QCheckBox("Filter by date range")
        self.use_filter.setChecked(False)
        self.use_filter.toggled.connect(self._on_filter_toggled)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setEnabled(False)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setEnabled(False)

        self.btn_refresh = QPushButton("Apply")
        self.btn_refresh.setMinimumHeight(34)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)

        filter_layout.addWidget(self.use_filter)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addStretch()
        root.addWidget(filter_card)

        # Stats
        stats_card = make_card()
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        stats_layout.setSpacing(20)
        self.stat_count = QLabel("Tests: 0")
        self.stat_avg_dl = QLabel("Avg download: n/a")
        self.stat_avg_ul = QLabel("Avg upload: n/a")
        self.stat_avg_lat = QLabel("Avg latency: n/a")
        for lbl in (self.stat_count, self.stat_avg_dl, self.stat_avg_ul, self.stat_avg_lat):
            lbl.setObjectName("muted")
            lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        stats_layout.addWidget(self.stat_count)
        stats_layout.addWidget(self.stat_avg_dl)
        stats_layout.addWidget(self.stat_avg_ul)
        stats_layout.addWidget(self.stat_avg_lat)
        stats_layout.addStretch()
        root.addWidget(stats_card)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Download", "Upload", "Latency", "Jitter",
            "Packet loss", "Server", "Status",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        root.addWidget(self.table, 1)

        # Actions
        actions = QHBoxLayout()
        self.btn_delete = QPushButton("Delete selected")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.setMinimumHeight(38)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setEnabled(False)
        self.btn_clear = QPushButton("Clear all history")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.setMinimumHeight(38)
        self.btn_export_csv.setCursor(Qt.PointingHandCursor)
        self.btn_export_json = QPushButton("Export JSON")
        self.btn_export_json.setMinimumHeight(38)
        self.btn_export_json.setCursor(Qt.PointingHandCursor)
        self.btn_export_report = QPushButton("Export Report")
        self.btn_export_report.setMinimumHeight(38)
        self.btn_export_report.setCursor(Qt.PointingHandCursor)
        self.btn_compare = QPushButton("Compare selected")
        self.btn_compare.setMinimumHeight(38)
        self.btn_compare.setCursor(Qt.PointingHandCursor)
        self.btn_compare.setEnabled(False)
        actions.addWidget(self.btn_delete)
        actions.addWidget(self.btn_clear)
        actions.addStretch()
        actions.addWidget(self.btn_export_csv)
        actions.addWidget(self.btn_export_json)
        actions.addWidget(self.btn_export_report)
        actions.addWidget(self.btn_compare)
        root.addLayout(actions)

        # Graphs
        graphs_card = make_card()
        graphs_layout = QVBoxLayout(graphs_card)
        graphs_layout.setContentsMargins(16, 12, 16, 12)
        graphs_layout.setSpacing(10)
        gtitle = QLabel("Historical trends")
        gtitle.setObjectName("h2")
        self.chart_dl = MplCanvas(width=8, height=2.8, dark=True)
        self.chart_ul = MplCanvas(width=8, height=2.8, dark=True)
        graphs_layout.addWidget(gtitle)
        graphs_layout.addWidget(self.chart_dl)
        graphs_layout.addWidget(self.chart_ul)
        add_shadow(graphs_card)
        root.addWidget(graphs_card, 1)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_json.clicked.connect(self._export_json)
        self.btn_export_report.clicked.connect(self._export_report)
        self.btn_compare.clicked.connect(self._compare_selected)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def refresh(self) -> None:
        self._load_records()
        self._populate_table()
        self._update_stats()
        self._refresh_graphs()

    def _load_records(self) -> None:
        if self.use_filter.isChecked():
            from_ = self._qdate_to_utc(self.date_from.date())
            to_ = self._qdate_to_utc(self.date_to.date())
            self._records = self._repo.fetch_date_range(from_, to_)
        else:
            self._records = self._repo.fetch_all()

    def _qdate_to_utc(self, qdate: QDate) -> str:
        dt = datetime(qdate.year(), qdate.month(), qdate.day(), tzinfo=UTC)
        return dt.isoformat()

    def _populate_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for rec in self._records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            ts = rec.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(ts)
                ts_disp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                ts_disp = str(ts)

            dl = rec.get("download_mbps")
            ul = rec.get("upload_mbps")
            lat = rec.get("latency_ms")
            jit = rec.get("jitter_ms")
            loss = rec.get("packet_loss_percent")
            server = rec.get("server_name") or "n/a"
            status = rec.get("status") or "—"

            values = [
                ts_disp,
                f"{dl:.2f} Mbps" if dl is not None else "n/a",
                f"{ul:.2f} Mbps" if ul is not None else "n/a",
                f"{lat:.1f} ms" if lat is not None else "n/a",
                f"{jit:.1f} ms" if jit is not None else "n/a",
                f"{loss:.1f}%" if loss is not None else "n/a",
                server,
                status,
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, rec.get("id"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.DescendingOrder)

    def _update_stats(self) -> None:
        stats = self._repo.stats()
        count = stats.get("count") or 0
        self.stat_count.setText(f"Tests: {count}")
        self.stat_avg_dl.setText(
            f"Avg download: {stats['avg_download']:.2f} Mbps" if stats.get("avg_download") is not None else "Avg download: n/a"
        )
        self.stat_avg_ul.setText(
            f"Avg upload: {stats['avg_upload']:.2f} Mbps" if stats.get("avg_upload") is not None else "Avg upload: n/a"
        )
        self.stat_avg_lat.setText(
            f"Avg latency: {stats['avg_latency']:.1f} ms" if stats.get("avg_latency") is not None else "Avg latency: n/a"
        )

    def _refresh_graphs(self) -> None:
        ordered = sorted(
            [r for r in self._records if r.get("status") == "completed"],
            key=lambda r: r.get("timestamp_utc") or "",
        )
        dl_pts = [r.get("download_mbps") for r in ordered if r.get("download_mbps") is not None]
        ul_pts = [r.get("upload_mbps") for r in ordered if r.get("upload_mbps") is not None]

        if dl_pts:
            self.chart_dl.plot_line(
                list(range(len(dl_pts))), dl_pts,
                color=DARK["accent"], ylabel="Mbps", title="Download speed over time",
            )
            self.chart_dl.show()
        else:
            self.chart_dl.plot_empty("No download data")

        if ul_pts:
            self.chart_ul.plot_line(
                list(range(len(ul_pts))), ul_pts,
                color=DARK["success"], ylabel="Mbps", title="Upload speed over time",
            )
            self.chart_ul.show()
        else:
            self.chart_ul.plot_empty("No upload data")

    def _on_filter_toggled(self, checked: bool) -> None:
        self.date_from.setEnabled(checked)
        self.date_to.setEnabled(checked)

    def _on_selection_changed(self) -> None:
        self.btn_delete.setEnabled(bool(self.table.selectedItems()))
        rows = self.table.selectionModel().selectedRows()
        self.btn_compare.setEnabled(len(rows) == 2)

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _delete_selected(self) -> None:
        test_id = self._selected_id()
        if test_id is None:
            return
        confirm = QMessageBox.question(
            self, "Delete record",
            "Delete this speed-test record? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self._repo.delete(test_id)
            self.refresh()

    def _clear_all(self) -> None:
        if not self._records:
            return
        confirm = QMessageBox.question(
            self, "Clear all history",
            "Delete all saved speed-test records? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self._repo.clear_all()
            self.refresh()

    def _export_csv(self) -> None:
        if not self._records:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export history to CSV",
            "netdoctor_history.csv",
            "CSV files (*.csv)",
        )
        if not path:
            return
        try:
            written = export_speed_tests_csv(path, self._records)
            QMessageBox.information(
                self, "Export complete",
                f"Exported {written} record(s) to {path}.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _export_json(self) -> None:
        if not self._records:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export history to JSON",
            "netdoctor_history.json",
            "JSON files (*.json)",
        )
        if not path:
            return
        try:
            written = export_speed_tests_json(path, self._records)
            QMessageBox.information(
                self, "Export complete",
                f"Exported {written} record(s) to {path}.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _export_report(self) -> None:
        if not self._records:
            return
        path, _selected = QFileDialog.getSaveFileName(
            self, "Export Report", "netdoctor_report.html",
            "HTML Report (*.html);;PDF Report (*.pdf)",
        )
        if not path:
            return
        try:
            if path.lower().endswith(".pdf"):
                written = self._report_service.export_pdf(path, self._records)
            else:
                if not path.lower().endswith(".html"):
                    path += ".html"
                written = self._report_service.export_html(path, self._records)
            QMessageBox.information(
                self, "Report Exported",
                f"Exported {written} record(s) to {path}.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    # ------------------------------------------------------------------ #
    # Comparison mode
    # ------------------------------------------------------------------ #
    def _compare_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if len(rows) != 2:
            return
        ids = []
        for row in rows:
            item = self.table.item(row.row(), 0)
            if item is not None:
                ids.append(item.data(Qt.UserRole))
        if len(ids) != 2:
            return
        recs = [self._repo.fetch_by_id(i) for i in ids]
        recs = [r for r in recs if r is not None]
        if len(recs) != 2:
            return
        dialog = ComparisonDialog(recs, self)
        dialog.exec()

    def apply_theme(self, dark: bool) -> None:
        self._dark = dark
        self.chart_dl._colors = palette_dict(dark)
        self.chart_ul._colors = palette_dict(dark)
        self.chart_dl.draw()
        self.chart_ul.draw()


class ComparisonDialog(QDialog):
    """Side-by-side comparison of two speed-test results."""

    def __init__(self, records: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compare Speed Tests")
        self.setMinimumWidth(600)
        self._records = records
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Test Comparison")
        title.setObjectName("h1")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        headers = ["Metric", "Test 1", "Test 2", "Difference"]
        grid.addWidget(QLabel(headers[0]), 0, 0)
        grid.addWidget(QLabel(headers[1]), 0, 1)
        grid.addWidget(QLabel(headers[2]), 0, 2)
        grid.addWidget(QLabel(headers[3]), 0, 3)

        r1, r2 = self._records[0], self._records[1]
        rows = [
            ("Timestamp", self._fmt_ts(r1), self._fmt_ts(r2), ""),
            ("Server", r1.get("server_name") or "n/a", r2.get("server_name") or "n/a", ""),
            ("Download", self._fmt_mbps(r1.get("download_mbps")),
             self._fmt_mbps(r2.get("download_mbps")), self._diff_mbps(r1, r2)),
            ("Upload", self._fmt_mbps(r1.get("upload_mbps")),
             self._fmt_mbps(r2.get("upload_mbps")), self._diff_mbps(r1, r2, "upload")),
            ("Latency", self._fmt_ms(r1.get("latency_ms")),
             self._fmt_ms(r2.get("latency_ms")), self._diff_ms(r1, r2)),
            ("Jitter", self._fmt_ms(r1.get("jitter_ms")),
             self._fmt_ms(r2.get("jitter_ms")), self._diff_ms(r1, r2, "jitter_ms")),
            ("Packet loss", self._fmt_pct(r1.get("packet_loss_percent")),
             self._fmt_pct(r2.get("packet_loss_percent")), self._diff_pct(r1, r2)),
            ("Status", r1.get("status") or "—", r2.get("status") or "—", ""),
        ]

        for i, (metric, v1, v2, diff) in enumerate(rows, start=1):
            m_lbl = QLabel(metric)
            m_lbl.setStyleSheet("font-weight: 600;")
            v1_lbl = QLabel(v1)
            v2_lbl = QLabel(v2)
            d_lbl = QLabel(diff)
            if diff:
                d_lbl.setStyleSheet("font-weight: 700; color: #2563eb;")
            grid.addWidget(m_lbl, i, 0)
            grid.addWidget(v1_lbl, i, 1)
            grid.addWidget(v2_lbl, i, 2)
            grid.addWidget(d_lbl, i, 3)

        layout.addLayout(grid)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    @staticmethod
    def _fmt_ts(rec: dict) -> str:
        ts = rec.get("timestamp") or ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return str(ts)

    @staticmethod
    def _fmt_mbps(v) -> str:
        return f"{v:.2f} Mbps" if v is not None else "n/a"

    @staticmethod
    def _fmt_ms(v) -> str:
        return f"{v:.1f} ms" if v is not None else "n/a"

    @staticmethod
    def _fmt_pct(v) -> str:
        return f"{v:.1f}%" if v is not None else "n/a"

    def _diff_mbps(self, r1, r2, field="download_mbps") -> str:
        v1, v2 = r1.get(field), r2.get(field)
        if v1 is None or v2 is None:
            return ""
        delta = v2 - v1
        sign = "+" if delta > 0 else ""
        return f"{sign}{delta:.2f} Mbps"

    def _diff_ms(self, r1, r2, field="latency_ms") -> str:
        v1, v2 = r1.get(field), r2.get(field)
        if v1 is None or v2 is None:
            return ""
        delta = v2 - v1
        sign = "+" if delta > 0 else ""
        return f"{sign}{delta:.1f} ms"

    def _diff_pct(self, r1, r2) -> str:
        v1, v2 = r1.get("packet_loss_percent"), r2.get("packet_loss_percent")
        if v1 is None or v2 is None:
            return ""
        delta = v2 - v1
        sign = "+" if delta > 0 else ""
        return f"{sign}{delta:.1f}%"

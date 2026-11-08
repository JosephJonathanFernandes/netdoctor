"""Report export service: PDF and HTML reports for speed-test history.

Generates professional, printable reports from stored speed-test results.
"""

from __future__ import annotations

import html
import os
from datetime import UTC, datetime

from app.database.repository import SpeedTestRepository
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReportService:
    def __init__(self, repo: SpeedTestRepository | None = None):
        self._repo = repo or SpeedTestRepository()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def export_html(
        self, file_path: str, records: list[dict] | None = None, title: str = "NetDoctor Speed Test Report"
    ) -> int:
        """Export speed-test results to a styled HTML report."""
        if records is None:
            records = self._repo.fetch_all()
        stats = self._repo.stats()

        html_content = self._build_html(records, stats, title)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(html_content)
        logger.info("Exported HTML report: %s (%d records)", file_path, len(records))
        return len(records)

    def export_pdf(
        self, file_path: str, records: list[dict] | None = None, title: str = "NetDoctor Speed Test Report"
    ) -> int:
        """Export speed-test results to a PDF report using fpdf2."""
        try:
            from fpdf import FPDF
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "fpdf2 is required for PDF export. Install with: pip install fpdf2"
            ) from exc

        if records is None:
            records = self._repo.fetch_all()
        stats = self._repo.stats()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            0,
            8,
            f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.ln(6)

        # Summary stats
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Summary Statistics", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        count = stats.get("count") or 0
        pdf.cell(0, 7, f"Total tests: {count}", new_x="LMARGIN", new_y="NEXT")
        if stats.get("avg_download") is not None:
            pdf.cell(
                0,
                7,
                f"Avg download: {stats['avg_download']:.2f} Mbps",
                new_x="LMARGIN",
                new_y="NEXT",
            )
        if stats.get("avg_upload") is not None:
            pdf.cell(
                0,
                7,
                f"Avg upload: {stats['avg_upload']:.2f} Mbps",
                new_x="LMARGIN",
                new_y="NEXT",
            )
        if stats.get("avg_latency") is not None:
            pdf.cell(
                0,
                7,
                f"Avg latency: {stats['avg_latency']:.1f} ms",
                new_x="LMARGIN",
                new_y="NEXT",
            )
        pdf.ln(4)

        # Results table
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Test Results", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)

        # Table header
        headers = ["Timestamp", "Download", "Upload", "Latency", "Server", "Status"]
        widths = [35, 25, 25, 22, 45, 25]
        for h, w in zip(headers, widths, strict=False):
            pdf.cell(w, 7, h, border=1, align="C")
        pdf.ln()

        for rec in records[:50]:  # Limit to 50 for PDF readability
            ts = rec.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(ts)
                ts_disp = dt.strftime("%m/%d %H:%M")
            except (ValueError, TypeError):
                ts_disp = str(ts)[:16]

            dl = rec.get("download_mbps")
            ul = rec.get("upload_mbps")
            lat = rec.get("latency_ms")
            server = (rec.get("server_name") or "n/a")[:25]
            status = rec.get("status") or "—"

            row = [
                ts_disp,
                f"{dl:.2f}" if dl is not None else "n/a",
                f"{ul:.2f}" if ul is not None else "n/a",
                f"{lat:.1f}" if lat is not None else "n/a",
                server,
                status,
            ]
            for val, w in zip(row, widths, strict=False):
                pdf.cell(w, 7, str(val), border=1)
            pdf.ln()

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        pdf.output(file_path)
        logger.info("Exported PDF report: %s (%d records)", file_path, len(records[:50]))
        return len(records[:50])

    # ------------------------------------------------------------------ #
    # HTML builder
    # ------------------------------------------------------------------ #
    def _build_html(self, records: list[dict], stats: dict, title: str) -> str:
        rows = []
        for rec in records:
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
            status_class = f"status-{status}"

            rows.append(f"""
            <tr>
                <td>{html.escape(ts_disp)}</td>
                <td>{f"{dl:.2f} Mbps" if dl is not None else "n/a"}</td>
                <td>{f"{ul:.2f} Mbps" if ul is not None else "n/a"}</td>
                <td>{f"{lat:.1f} ms" if lat is not None else "n/a"}</td>
                <td>{f"{jit:.1f} ms" if jit is not None else "n/a"}</td>
                <td>{f"{loss:.1f}%" if loss is not None else "n/a"}</td>
                <td>{html.escape(server)}</td>
                <td class="{status_class}">{html.escape(status)}</td>
            </tr>
            """)

        count = stats.get("count") or 0
        avg_dl = stats.get("avg_download")
        avg_ul = stats.get("avg_upload")
        avg_lat = stats.get("avg_latency")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    h1 {{ color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }}
    .meta {{ color: #6b7280; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #d1d5db; padding: 0.6rem 0.8rem; text-align: left; font-size: 0.9rem; }}
    th {{ background: #f3f4f6; font-weight: 600; color: #374151; }}
    tr:nth-child(even) {{ background: #f9fafb; }}
    .status-completed {{ color: #15803d; font-weight: 600; }}
    .status-failed {{ color: #b91c1c; font-weight: 600; }}
    .status-cancelled {{ color: #6b7280; font-weight: 600; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
    .stat-card {{ background: #f3f4f6; border-radius: 8px; padding: 1rem; }}
    .stat-card .label {{ color: #6b7280; font-size: 0.8rem; text-transform: uppercase; }}
    .stat-card .value {{ font-size: 1.5rem; font-weight: 700; color: #111827; }}
    .footer {{ margin-top: 2rem; color: #9ca3af; font-size: 0.8rem; border-top: 1px solid #e5e7eb; padding-top: 0.5rem; }}
</style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    <div class="meta">Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>

    <div class="stats">
        <div class="stat-card"><div class="label">Total Tests</div><div class="value">{count}</div></div>
        <div class="stat-card"><div class="label">Avg Download</div><div class="value">{f"{avg_dl:.2f} Mbps" if avg_dl is not None else "n/a"}</div></div>
        <div class="stat-card"><div class="label">Avg Upload</div><div class="value">{f"{avg_ul:.2f} Mbps" if avg_ul is not None else "n/a"}</div></div>
        <div class="stat-card"><div class="label">Avg Latency</div><div class="value">{f"{avg_lat:.1f} ms" if avg_lat is not None else "n/a"}</div></div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Timestamp</th><th>Download</th><th>Upload</th>
                <th>Latency</th><th>Jitter</th><th>Packet Loss</th>
                <th>Server</th><th>Status</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows) if rows else '<tr><td colspan="8" style="text-align:center;color:#6b7280;">No test records.</td></tr>'}
        </tbody>
    </table>

    <div class="footer">
        NetDoctor — Internet Speed Test & Network Health Monitor<br>
        Report generated locally. No data sent to external servers.
    </div>
</body>
</html>"""

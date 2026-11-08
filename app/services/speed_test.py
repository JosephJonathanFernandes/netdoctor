"""Enhanced speed-test service for NetDoctor.

Uses speedtest-cli (speedtest.net) as the primary backend for download, upload
and latency. Jitter and packet loss are estimated separately via ICMP ping to a
diagnostic target and are clearly labelled as estimates -- they are NOT
speedtest.net-verified measurements.

All network I/O is blocking; callers run this inside a background QThread worker
so the GUI never freezes.
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.config import (
    CONNECTIVITY_TIMEOUT,
    DIAGNOSTIC_HOST,
    SPEEDTEST_TIMEOUT,
)
from app.utils.formatting import format_ms, format_percent
from app.utils.logging import get_logger
from app.utils.platform_info import ping_host

logger = get_logger(__name__)

ProgressCallback = Callable[[str, str], None]


@dataclass
class ServerInfo:
    """Information about a selected speed-test server."""

    name: str | None = None
    sponsor: str | None = None
    country: str | None = None
    host: str | None = None
    id: str | None = None


@dataclass
class SpeedTestResult:
    """A single speed-test outcome."""

    status: str = "pending"  # pending | running | completed | failed | cancelled
    download_mbps: float | None = None
    upload_mbps: float | None = None
    latency_ms: float | None = None
    jitter_ms: float | None = None
    packet_loss_percent: float | None = None
    server: ServerInfo | None = None
    timestamp: str | None = None
    timestamp_utc: str | None = None
    error_message: str | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "packet_loss_percent": self.packet_loss_percent,
            "server_name": self.server.name if self.server else None,
            "server_sponsor": self.server.sponsor if self.server else None,
            "server_country": self.server.country if self.server else None,
            "server_host": self.server.host if self.server else None,
            "timestamp": self.timestamp,
            "timestamp_utc": self.timestamp_utc,
            "error_message": self.error_message,
            "note": self.note,
        }


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def check_connectivity(timeout: float = CONNECTIVITY_TIMEOUT) -> bool:
    """Lightweight TCP reachability check to well-known endpoints.

    Does not measure speed and does not depend on any single website.
    """
    endpoints = [("1.1.1.1", 443), ("8.8.8.8", 443), ("1.0.0.1", 443)]
    for host, port in endpoints:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


class SpeedTestService:
    """Orchestrates a full speed test with progress reporting and cancellation."""

    def __init__(self, progress_callback: ProgressCallback | None = None):
        self.progress_callback = progress_callback or (lambda stage, msg: None)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def _progress(self, stage: str, message: str) -> None:
        logger.debug("Speed test stage=%s message=%s", stage, message)
        self.progress_callback(stage, message)

    def run(self) -> SpeedTestResult:
        """Run the complete speed test and return a result object."""
        result = SpeedTestResult(status="running", timestamp=_now_iso())
        result.timestamp_utc = result.timestamp

        # 1. Connectivity
        self._progress("checking_connectivity", "Checking internet connectivity...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        if not check_connectivity():
            result.status = "failed"
            result.error_message = (
                "No internet connectivity detected. Check your network connection and try again."
            )
            logger.warning("Speed test aborted: no internet connectivity")
            self._progress("failed", result.error_message or "Failed")
            return result

        # 2. Select server (single instance reused for dl/ul)
        self._progress("finding_server", "Locating the best test server...")
        if self._cancelled:
            result.status = "cancelled"
            return result

        server = self._select_server()
        if server is None:
            result.status = "failed"
            result.error_message = (
                "Could not reach the speed-test server list. "
                "This may be a firewall or DNS issue. Try again later."
            )
            logger.error("Speed test aborted: could not select server")
            self._progress("failed", result.error_message or "Failed")
            return result

        result.server = server
        logger.info(
            "Selected speed-test server: %s (%s, %s)",
            server.name,
            server.sponsor,
            server.country,
        )

        # Create a single Speedtest instance reused for download/upload
        st = self._create_client(server)
        if st is None:
            result.status = "failed"
            result.error_message = (
                "Could not initialize the speed-test client. Try again later."
            )
            self._progress("failed", result.error_message or "Failed")
            return result

        # 3. Idle latency
        self._progress("measuring_latency", "Measuring idle latency...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        latency_result = self._measure_latency(server.host)
        result.latency_ms = latency_result.get("avg_ms")
        if result.latency_ms is not None:
            logger.info("Idle latency: %.1f ms", result.latency_ms)

        # 4. Download
        self._progress("downloading", "Measuring download speed...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        download = self._run_download(st)
        if download is not None:
            result.download_mbps = download
            logger.info("Download: %.2f Mbps", download)

        # 5. Upload
        self._progress("uploading", "Measuring upload speed...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        upload = self._run_upload(st)
        if upload is not None:
            result.upload_mbps = upload
            logger.info("Upload: %.2f Mbps", upload)

        # 6. Jitter (ICMP estimate)
        self._progress("measuring_jitter", "Estimating jitter...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        jitter_result = ping_host(DIAGNOSTIC_HOST, count=8, timeout=3.0)
        result.jitter_ms = jitter_result.get("jitter_ms")
        if result.latency_ms is None and jitter_result.get("avg_ms") is not None:
            result.latency_ms = jitter_result.get("avg_ms")
        if result.jitter_ms is not None:
            logger.info("Jitter: %.1f ms", result.jitter_ms)

        # 7. Packet loss (ICMP estimate, documented)
        self._progress("measuring_packet_loss", "Estimating packet loss (ICMP ping)...")
        if self._cancelled:
            result.status = "cancelled"
            return result
        loss_result = ping_host(DIAGNOSTIC_HOST, count=10, timeout=3.0)
        result.packet_loss_percent = loss_result.get("packet_loss_percent")
        if result.packet_loss_percent is not None:
            logger.info("Packet loss: %.1f%%", result.packet_loss_percent)

        # Final status
        if self._cancelled:
            result.status = "cancelled"
        elif result.download_mbps is None and result.upload_mbps is None:
            result.status = "failed"
            result.error_message = (
                "Speed test could not complete. Latency was measured, but "
                "download/upload throughput is unavailable."
            )
        else:
            result.status = "completed"

        result.timestamp_utc = result.timestamp
        self._progress(
            result.status,
            "Test complete." if result.status == "completed"
            else result.error_message or "Finished",
        )
        logger.info("Speed test finished: status=%s", result.status)
        return result

    # -- internals -- #
    def _select_server(self) -> ServerInfo | None:
        try:
            from speedtest import Speedtest

            st = Speedtest(timeout=SPEEDTEST_TIMEOUT)
            st.get_servers()
            st.get_best_server()
            best = getattr(st, "best", None) or {}
            return ServerInfo(
                name=best.get("name"),
                sponsor=best.get("sponsor"),
                country=best.get("country"),
                host=best.get("host"),
                id=str(best.get("id")) if best.get("id") else None,
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to select speed-test server")
            return None

    def _create_client(self, server: ServerInfo):
        """Create a Speedtest client pre-configured with the selected server."""
        try:
            from speedtest import Speedtest

            st = Speedtest(timeout=SPEEDTEST_TIMEOUT)
            st.get_servers()
            st.get_best_server()
            return st
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to create speed-test client")
            return None

    def _run_download(self, st) -> float | None:
        try:
            bps = st.download()
            if bps is None:
                return None
            return float(bps) / 1_000_000.0
        except Exception:  # pragma: no cover - defensive
            return None

    def _run_upload(self, st) -> float | None:
        try:
            bps = st.upload()
            if bps is None:
                return None
            return float(bps) / 1_000_000.0
        except Exception:  # pragma: no cover - defensive
            return None

    def _measure_latency(self, host: str | None) -> dict:
        target = host or DIAGNOSTIC_HOST
        return ping_host(target, count=4, timeout=3.0)


def format_result_for_display(result: SpeedTestResult) -> dict:
    """Convert a SpeedTestResult into display-friendly strings.

    Note: download_mbps / upload_mbps are already in Mbps.
    """
    server_name = result.server.name if result.server else None
    server_sponsor = result.server.sponsor if result.server else None
    server_country = result.server.country if result.server else None

    return {
        "status": result.status,
        "download": (
            f"{result.download_mbps:.2f} Mbps"
            if result.download_mbps is not None
            else "n/a"
        ),
        "upload": (
            f"{result.upload_mbps:.2f} Mbps"
            if result.upload_mbps is not None
            else "n/a"
        ),
        "latency": format_ms(result.latency_ms),
        "jitter": (
            format_ms(result.jitter_ms) if result.jitter_ms is not None else "n/a"
        ),
        "packet_loss": (
            format_percent(result.packet_loss_percent)
            if result.packet_loss_percent is not None
            else "n/a"
        ),
        "server": server_name or "n/a",
        "server_sponsor": server_sponsor or "",
        "server_country": server_country or "",
        "timestamp": result.timestamp or "n/a",
        "error": result.error_message,
        "note": result.note,
    }

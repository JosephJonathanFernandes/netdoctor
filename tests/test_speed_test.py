"""Unit tests for the speed-test service with mocked network operations."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.speed_test import (
    SpeedTestResult,
    SpeedTestService,
    check_connectivity,
    format_result_for_display,
)


def _make_speedtest_mock(download_bps=50_000_000, upload_bps=20_000_000):
    mock = MagicMock()
    mock.best = {
        "id": "srv-1",
        "name": "Test City",
        "sponsor": "Test ISP",
        "country": "United States",
        "host": "test.example.com:8080",
    }
    mock.download.return_value = download_bps
    mock.upload.return_value = upload_bps
    return mock


class TestCheckConnectivity:
    @patch("app.services.speed_test.socket.create_connection")
    def test_connectivity_true(self, mock_connect):
        mock_connect.return_value.__enter__.return_value = None
        assert check_connectivity() is True

    @patch("app.services.speed_test.socket.create_connection")
    def test_connectivity_false(self, mock_connect):
        mock_connect.side_effect = OSError("unreachable")
        assert check_connectivity() is False


class TestSpeedTestService:
    @patch("app.services.speed_test.check_connectivity", return_value=True)
    @patch("app.services.speed_test.ping_host")
    @patch("speedtest.Speedtest")
    def test_full_test_completed(self, mock_st_cls, mock_ping, mock_conn):
        mock_st = _make_speedtest_mock()
        mock_st_cls.return_value = mock_st
        mock_ping.return_value = {
            "success": True,
            "packets_sent": 4,
            "packets_received": 4,
            "avg_ms": 20.0,
            "min_ms": 18.0,
            "max_ms": 22.0,
            "jitter_ms": 2.0,
            "packet_loss_percent": 0.0,
            "raw": "",
            "error": None,
        }

        svc = SpeedTestService()
        result = svc.run()

        assert result.status == "completed"
        assert result.download_mbps == 50.0
        assert result.upload_mbps == 20.0
        assert result.latency_ms == 20.0
        assert result.jitter_ms == 2.0
        assert result.packet_loss_percent == 0.0
        assert result.server_name == "Test City"
        assert result.server_country == "United States"
        assert result.error_message is None

    @patch("app.services.speed_test.check_connectivity", return_value=False)
    def test_no_connectivity_failed(self, mock_conn):
        svc = SpeedTestService()
        result = svc.run()
        assert result.status == "failed"
        assert "No internet connectivity" in result.error_message

    @patch("app.services.speed_test.check_connectivity", return_value=True)
    @patch("speedtest.Speedtest")
    def test_server_selection_failure(self, mock_st_cls, mock_conn):
        mock_st_cls.side_effect = Exception("network down")
        svc = SpeedTestService()
        result = svc.run()
        assert result.status == "failed"

    def test_format_result_for_display(self):
        result = SpeedTestResult(
            status="completed",
            download_mbps=50.0,
            upload_mbps=20.0,
            latency_ms=20.0,
            jitter_ms=2.0,
            packet_loss_percent=0.0,
            server_name="Test City",
            server_sponsor="Test ISP",
            server_country="US",
            timestamp="2026-01-01T12:00:00+00:00",
        )
        disp = format_result_for_display(result)
        assert disp["download"] == "50.00 Mbps"
        assert disp["upload"] == "20.00 Mbps"
        assert disp["latency"] == "20.0 ms"
        assert disp["packet_loss"] == "0.0%"
        assert disp["server"] == "Test City"
        assert disp["error"] is None

    def test_format_result_missing_values(self):
        result = SpeedTestResult(status="failed", error_message="timeout")
        disp = format_result_for_display(result)
        assert disp["download"] == "n/a"
        assert disp["upload"] == "n/a"
        assert disp["latency"] == "n/a"
        assert disp["error"] == "timeout"

    @patch("app.services.speed_test.check_connectivity", return_value=True)
    @patch("app.services.speed_test.ping_host")
    @patch("speedtest.Speedtest")
    def test_download_none_marks_failed(self, mock_st_cls, mock_ping, mock_conn):
        mock_st = _make_speedtest_mock(download_bps=None, upload_bps=None)
        mock_st_cls.return_value = mock_st
        mock_ping.return_value = {
            "success": True, "packets_sent": 4, "packets_received": 4,
            "avg_ms": 20.0, "min_ms": 18.0, "max_ms": 22.0, "jitter_ms": 2.0,
            "packet_loss_percent": 0.0, "raw": "", "error": None,
        }
        svc = SpeedTestService()
        result = svc.run()
        assert result.status == "failed"
        assert result.download_mbps is None

    def test_to_dict_keys(self):
        result = SpeedTestResult(status="completed", download_mbps=10.0)
        d = result.to_dict()
        assert d["status"] == "completed"
        assert d["download_mbps"] == 10.0
        assert "timestamp" in d

    def test_timestamp_utc_set(self):
        svc = SpeedTestService()
        with patch.object(
            svc, "_create_and_select_server", return_value=None
        ):
            with patch("app.services.speed_test.check_connectivity", return_value=True):
                result = svc.run()
        assert result.timestamp_utc is not None
        datetime.fromisoformat(result.timestamp_utc)

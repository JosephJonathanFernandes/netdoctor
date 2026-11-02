"""Unit tests for platform_info defensive parsing (no real network)."""

from unittest.mock import MagicMock, patch

import subprocess

from app.utils.platform_info import ping_host, resolve_host


class TestPingHost:
    def test_successful_ping_parse(self):
        fake_output = (
            "Pinging 1.1.1.1 with 32 bytes of data:\r\n"
            "Reply from 1.1.1.1: bytes=32 time=12ms TTL=56\r\n"
            "Reply from 1.1.1.1: bytes=32 time=15ms TTL=56\r\n"
            "Reply from 1.1.1.1: bytes=32 time=11ms TTL=56\r\n"
            "Reply from 1.1.1.1: bytes=32 time=14ms TTL=56\r\n"
            "\r\n"
            "Ping statistics for 1.1.1.1:\r\n"
            "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\r\n"
        )
        with patch("app.utils.platform_info.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)
            result = ping_host("1.1.1.1", count=4, timeout=3.0)
        assert result["success"] is True
        assert result["packets_sent"] == 4
        assert result["packets_received"] == 4
        assert result["packet_loss_percent"] == 0.0
        assert result["avg_ms"] == 13.0
        assert result["jitter_ms"] is not None
        assert result["error"] is None

    def test_timeout(self):
        with patch("app.utils.platform_info.run_command") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired("ping", 5)
            result = ping_host("1.1.1.1", count=4, timeout=5.0)
        assert result["success"] is False
        assert result["error"] is not None
        assert "timed out" in result["error"]

    def test_all_timed_out(self):
        fake_output = (
            "Pinging 1.1.1.1 with 32 bytes of data:\r\n"
            "Request timed out.\r\n"
            "Request timed out.\r\n"
            "Request timed out.\r\n"
            "Request timed out.\r\n"
        )
        with patch("app.utils.platform_info.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)
            result = ping_host("1.1.1.1", count=4, timeout=3.0)
        assert result["success"] is False
        assert result["packet_loss_percent"] == 100.0
        assert result["avg_ms"] is None


class TestResolveHost:
    def test_successful_resolution(self):
        fake_output = (
            "Server:  dns.google\r\n"
            "Address:  8.8.8.8\r\n"
            "\r\n"
            "Non-authoritative answer:\r\n"
            "Name:    one.one.one.one\r\n"
            "Addresses:  1.1.1.1\r\n"
        )
        with patch("app.utils.platform_info.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)
            result = resolve_host("one.one.one.one")
        assert result["success"] is True
        assert "1.1.1.1" in result["addresses"]

    def test_failed_resolution(self):
        with patch("app.utils.platform_info.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=1)
            result = resolve_host("nonexistent.invalid")
        assert result["success"] is False
        assert result["error"] is not None

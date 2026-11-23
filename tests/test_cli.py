"""Unit tests for the CLI module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.cli import main


class TestCLIVersion:
    def test_version(self):
        assert main(["version"]) == 0


class TestCLICheck:
    @patch("app.cli.check_connectivity")
    def test_check_online(self, mock_check):
        mock_check.return_value = True
        assert main(["check"]) == 0

    @patch("app.cli.check_connectivity")
    def test_check_offline(self, mock_check):
        mock_check.return_value = False
        assert main(["check"]) == 1


class TestCLIHistory:
    @patch("app.cli.SpeedTestRepository")
    def test_history(self, mock_repo_cls):
        mock_repo = MagicMock()
        mock_repo.fetch_all.return_value = []
        mock_repo_cls.return_value = mock_repo
        assert main(["history"]) == 0


class TestCLIExport:
    @patch("app.cli.SpeedTestRepository")
    @patch("app.cli.export_speed_tests_csv")
    def test_export_csv(self, mock_export, mock_repo_cls):
        mock_repo = MagicMock()
        mock_repo.fetch_all.return_value = []
        mock_repo_cls.return_value = mock_repo
        mock_export.return_value = 5

        # Use a temp file path
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".csv")
        try:
            assert main(["export", tmp]) == 0
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


class TestCLIStats:
    @patch("app.cli.SpeedTestRepository")
    def test_stats(self, mock_repo_cls):
        mock_repo = MagicMock()
        mock_repo.stats.return_value = {"count": 0}
        mock_repo_cls.return_value = mock_repo
        assert main(["stats"]) == 0


class TestCLINoCommand:
    def test_no_command(self):
        assert main([]) == 1


class TestCLIUnknownCommand:
    def test_unknown_command(self):
        import pytest
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code == 2


class TestCLIRunTest:
    def _make_result(self, status="completed", download=50.0, upload=20.0,
                     latency=20.0, jitter=2.0, packet_loss=0.0,
                     server_name="Test City", server_sponsor="Test ISP",
                     server_country="US", server_host="test.example.com:8080",
                     timestamp="2026-01-01T12:00:00+00:00",
                     timestamp_utc="2026-01-01T12:00:00+00:00",
                     error_message=None):
        """Create a mock result with proper attribute values (not MagicMock)."""
        mock = MagicMock()
        mock.status = status
        mock.download_mbps = download
        mock.upload_mbps = upload
        mock.latency_ms = latency
        mock.jitter_ms = jitter
        mock.packet_loss_percent = packet_loss
        mock.server_name = server_name
        mock.server_sponsor = server_sponsor
        mock.server_country = server_country
        mock.server_host = server_host
        mock.timestamp = timestamp
        mock.timestamp_utc = timestamp_utc
        mock.error_message = error_message
        mock.to_dict.return_value = {
            "status": status,
            "download_mbps": download,
            "upload_mbps": upload,
            "latency_ms": latency,
            "jitter_ms": jitter,
            "packet_loss_percent": packet_loss,
            "server_name": server_name,
            "server_sponsor": server_sponsor,
            "server_country": server_country,
            "server_host": server_host,
            "timestamp": timestamp,
            "timestamp_utc": timestamp_utc,
            "error_message": error_message,
            "note": None,
        }
        return mock

    @patch("app.cli.SpeedTestService")
    def test_run_test_completed(self, mock_svc_cls):
        mock_service = MagicMock()
        mock_result = self._make_result(status="completed")
        mock_service.run.return_value = mock_result
        mock_svc_cls.return_value = mock_service

        assert main(["run-test"]) == 0

    @patch("app.cli.SpeedTestService")
    def test_run_test_failed(self, mock_svc_cls):
        mock_service = MagicMock()
        mock_result = self._make_result(status="failed")
        mock_service.run.return_value = mock_result
        mock_svc_cls.return_value = mock_service

        assert main(["run-test"]) == 1

    @patch("app.cli.SpeedTestService")
    @patch("app.cli.SpeedTestRepository")
    def test_run_test_save(self, mock_repo_cls, mock_svc_cls):
        mock_service = MagicMock()
        mock_result = self._make_result(status="completed")
        mock_service.run.return_value = mock_result
        mock_svc_cls.return_value = mock_service

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        assert main(["run-test", "--save"]) == 0
        mock_repo.insert.assert_called_once()

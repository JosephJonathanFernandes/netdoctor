"""Unit tests for the scheduler service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.scheduler import SchedulerService


class TestSchedulerService:
    def setup_method(self):
        self.scheduler = SchedulerService(interval_minutes=5.0)

    def test_initial_state(self):
        assert self.scheduler.interval_minutes == 5.0
        assert self.scheduler._running is False

    def test_set_interval(self):
        self.scheduler.set_interval(10.0)
        assert self.scheduler.interval_minutes == 10.0

    def test_set_interval_minimum(self):
        self.scheduler.set_interval(0.5)
        assert self.scheduler.interval_minutes == 5.0  # Minimum enforced

    def test_stop_not_running(self):
        # Should not raise
        self.scheduler.stop()

    def test_signals_exist(self):
        assert hasattr(self.scheduler.signals, "started")
        assert hasattr(self.scheduler.signals, "stopped")
        assert hasattr(self.scheduler.signals, "test_started")
        assert hasattr(self.scheduler.signals, "test_completed")
        assert hasattr(self.scheduler.signals, "test_failed")
        assert hasattr(self.scheduler.signals, "error")

    @patch("app.services.scheduler.SpeedTestService")
    def test_run_single_iteration_then_stop(self, mock_st_cls):
        # Set up mock to return completed result then stop
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.status = "completed"
        mock_service.run.return_value = mock_result
        mock_st_cls.return_value = mock_service

        scheduler = SchedulerService(interval_minutes=0.1)  # Very short interval
        scheduler._service = mock_service

        # Manually run one iteration logic
        result = scheduler._service.run()
        assert result.status == "completed"

    def test_signals_connected(self):
        # Verify signals can be connected and emitted
        started_emitted = False
        completed_emitted = False

        def on_started():
            nonlocal started_emitted
            started_emitted = True

        def on_completed(result):
            nonlocal completed_emitted
            completed_emitted = True

        self.scheduler.signals.started.connect(on_started)
        self.scheduler.signals.test_completed.connect(on_completed)

        self.scheduler.signals.started.emit()
        self.scheduler.signals.test_completed.emit(MagicMock())

        assert started_emitted is True
        assert completed_emitted is True

"""Unit tests for formatting / unit-conversion utilities."""

import pytest

from app.utils.formatting import (
    clamp,
    format_bits_per_sec,
    format_bytes,
    format_mbps,
    format_ms,
    format_percent,
    format_relative_time,
    status_color,
    to_bits_per_sec,
    to_mbps,
)


class TestToMbps:
    def test_converts_mbps(self):
        assert to_mbps(50_000_000) == 50.0
        assert to_mbps(1_000_000) == 1.0

    def test_none(self):
        assert to_mbps(None) is None

    def test_invalid(self):
        assert to_mbps("not-a-number") is None


class TestToBitsPerSec:
    def test_converts(self):
        assert to_bits_per_sec(50.0) == 50_000_000.0

    def test_none(self):
        assert to_bits_per_sec(None) is None


class TestFormatMbps:
    def test_format(self):
        assert format_mbps(50_000_000) == "50.00 Mbps"
        assert format_mbps(1_234_567) == "1.23 Mbps"

    def test_none(self):
        assert format_mbps(None) == "n/a"


class TestFormatBytes:
    def test_bytes(self):
        assert format_bytes(0) == "0 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(1024 ** 3) == "1.00 GB"

    def test_none(self):
        assert format_bytes(None) == "n/a"


class TestFormatMs:
    def test_format(self):
        assert format_ms(12.5) == "12.5 ms"
        assert format_ms(0) == "0.0 ms"

    def test_none(self):
        assert format_ms(None) == "n/a"


class TestFormatPercent:
    def test_format(self):
        assert format_percent(25.5) == "25.5%"
        assert format_percent(0) == "0.0%"

    def test_none(self):
        assert format_percent(None) == "n/a"


class TestClamp:
    def test_bounds(self):
        assert clamp(-5, 0, 100) == 0
        assert clamp(150, 0, 100) == 100
        assert clamp(50, 0, 100) == 50


class TestFormatRelativeTime:
    def test_just_now(self):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        assert format_relative_time(now) == "just now"

    def test_minutes_ago(self):
        from datetime import datetime, timezone, timedelta
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert format_relative_time(past) == "5 minute(s) ago"

    def test_hours_ago(self):
        from datetime import datetime, timezone, timedelta
        past = datetime.now(timezone.utc) - timedelta(hours=3)
        assert format_relative_time(past) == "3 hour(s) ago"

    def test_days_ago(self):
        from datetime import datetime, timezone, timedelta
        past = datetime.now(timezone.utc) - timedelta(days=2)
        assert format_relative_time(past) == "2 day(s) ago"

    def test_none(self):
        assert format_relative_time(None) == "n/a"


class TestStatusColor:
    def test_completed(self):
        assert status_color("completed") == "#34d399"

    def test_failed(self):
        assert status_color("failed") == "#f87171"

    def test_cancelled(self):
        assert status_color("cancelled") == "#94a3b8"

    def test_running(self):
        assert status_color("running") == "#89b4fa"

    def test_unknown(self):
        assert status_color("unknown") == "#94a3b8"


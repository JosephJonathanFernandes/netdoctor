"""Formatting utilities for NetDoctor.

All helpers are pure functions so they are easy to unit test without a GUI or
network access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def format_bytes(num_bytes: Optional[float]) -> str:
    """Format a byte count into a human readable string (B, KB, MB, GB, TB)."""
    if num_bytes is None:
        return "n/a"
    try:
        value = float(num_bytes)
    except (TypeError, ValueError):
        return "n/a"
    if value < 0:
        value = 0.0
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while value >= 1024.0 and index < len(units) - 1:
        value /= 1024.0
        index += 1
    if index == 0:
        return f"{int(value)} {units[index]}"
    return f"{value:,.2f} {units[index]}"


def format_bits_per_sec(bps: Optional[float]) -> str:
    """Format a bits-per-second value into the largest sensible unit."""
    if bps is None:
        return "n/a"
    try:
        value = float(bps)
    except (TypeError, ValueError):
        return "n/a"
    if value < 0:
        value = 0.0
    units = ["bps", "Kbps", "Mbps", "Gbps"]
    index = 0
    while value >= 1000.0 and index < len(units) - 1:
        value /= 1000.0
        index += 1
    return f"{value:,.2f} {units[index]}"


def format_mbps(bps: Optional[float]) -> str:
    """Format bits per second specifically as Mbps (two decimals)."""
    if bps is None:
        return "n/a"
    try:
        mbps = float(bps) / 1_000_000.0
    except (TypeError, ValueError):
        return "n/a"
    if mbps < 0:
        mbps = 0.0
    return f"{mbps:,.2f} Mbps"


def format_ms(ms: Optional[float]) -> str:
    """Format a latency value in milliseconds."""
    if ms is None:
        return "n/a"
    try:
        value = float(ms)
    except (TypeError, ValueError):
        return "n/a"
    if value < 0:
        value = 0.0
    return f"{value:,.1f} ms"


def format_percent(value: Optional[float], decimals: int = 1) -> str:
    """Format a percentage value."""
    if value is None:
        return "n/a"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{v:,.{decimals}f}%"


def format_timestamp(ts, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime / timestamp value for display."""
    if ts is None:
        return "n/a"
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.fromisoformat(str(ts))
    except (TypeError, ValueError, OverflowError, OSError):
        return "n/a"
    return dt.strftime(fmt)


def format_relative_time(ts) -> str:
    """Format a timestamp as a relative time (e.g., '2 minutes ago')."""
    if ts is None:
        return "n/a"
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.fromisoformat(str(ts))
    except (TypeError, ValueError, OverflowError, OSError):
        return "n/a"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} minute(s) ago"
    if seconds < 86400:
        return f"{seconds // 3600} hour(s) ago"
    return f"{seconds // 86400} day(s) ago"


def to_mbps(bits_per_second: Optional[float]) -> Optional[float]:
    """Convert bits per second to Mbps (float) or None."""
    if bits_per_second is None:
        return None
    try:
        return float(bits_per_second) / 1_000_000.0
    except (TypeError, ValueError):
        return None


def to_bits_per_sec(mbps: Optional[float]) -> Optional[float]:
    """Convert Mbps to bits per second or None."""
    if mbps is None:
        return None
    try:
        return float(mbps) * 1_000_000.0
    except (TypeError, ValueError):
        return None


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value into [minimum, maximum]."""
    return max(minimum, min(maximum, value))


def status_color(status: str) -> str:
    """Return a hex color for a given status string."""
    return {
        "completed": "#34d399",
        "failed": "#f87171",
        "cancelled": "#94a3b8",
        "running": "#89b4fa",
        "pending": "#94a3b8",
        "pass": "#34d399",
        "warn": "#fbbf24",
        "fail": "#f87171",
    }.get(status, "#94a3b8")

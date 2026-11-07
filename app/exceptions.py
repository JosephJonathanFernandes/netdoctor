"""Custom exception hierarchy for NetDoctor.

All application-specific exceptions derive from ``NetDoctorError`` so callers
can catch a single base type while still distinguishing specific failure modes.
"""

from __future__ import annotations


class NetDoctorError(Exception):
    """Base exception for all NetDoctor errors."""


class ConfigurationError(NetDoctorError):
    """Raised when application configuration is invalid or missing."""


class DatabaseError(NetDoctorError):
    """Raised when a database operation fails."""


class NetworkError(NetDoctorError):
    """Raised when a network operation fails."""


class ConnectivityError(NetworkError):
    """Raised when internet connectivity cannot be established."""


class SpeedTestError(NetworkError):
    """Raised when a speed test cannot complete."""


class ServerUnavailableError(SpeedTestError):
    """Raised when the speed-test server list or best server is unavailable."""


class DiagnosticError(NetworkError):
    """Raised when a diagnostic check fails unexpectedly."""


class WorkerError(NetDoctorError):
    """Raised when a background worker fails."""


class UpdaterError(NetDoctorError):
    """Raised when an auto-update check or download fails."""


class CancellationError(NetDoctorError):
    """Raised when an operation is cancelled by the user."""


__all__ = [
    "NetDoctorError",
    "ConfigurationError",
    "DatabaseError",
    "NetworkError",
    "ConnectivityError",
    "SpeedTestError",
    "ServerUnavailableError",
    "DiagnosticError",
    "WorkerError",
    "UpdaterError",
    "CancellationError",
]

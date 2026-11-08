"""Application logging configuration for NetDoctor.

Provides a module-level logger and a helper to configure logging with
rotation, console output, and (optionally) a file handler.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys

from app.config import get_app_data_dir

LOGGER_NAME = "netdoctor"
LOG_FILE_NAME = "netdoctor.log"
MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def configure_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    console: bool = True,
) -> logging.Logger:
    """Configure and return the NetDoctor application logger.

    Args:
        level: Logging level (default INFO).
        log_file: Path to a log file. If None, defaults to
            ``%LOCALAPPDATA%\\NetDoctor\\netdoctor.log`` on Windows.
        console: Whether to emit log records to stdout.

    Returns:
        The configured :class:`logging.Logger`.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times.
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if console:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    if log_file is None:
        app_dir = get_app_data_dir()
        os.makedirs(app_dir, exist_ok=True)
        log_file = os.path.join(app_dir, LOG_FILE_NAME)

    try:
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        # File logging is optional; continue with console only.
        pass

    return logger


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """Return a logger for the given name."""
    return logging.getLogger(name)

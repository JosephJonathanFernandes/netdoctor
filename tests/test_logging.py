"""Unit tests for logging configuration."""

import logging
import os
import tempfile

from app.utils.logging import LOGGER_NAME, configure_logging, get_logger


def _reset_logger():
    """Remove all handlers from the module logger for test isolation."""
    logger = logging.getLogger(LOGGER_NAME)
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)


class TestLogging:
    def setup_method(self):
        _reset_logger()

    def teardown_method(self):
        _reset_logger()

    def test_configure_logging_returns_logger(self):
        logger = configure_logging(level=logging.DEBUG, console=False)
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.DEBUG

    def test_configure_logging_with_file(self):
        log_file = tempfile.mktemp(suffix=".log")
        try:
            logger = configure_logging(level=logging.INFO, log_file=log_file, console=False)
            logger.info("test log message")
            # Force flush and close handlers
            for h in list(logger.handlers):
                h.flush()
                h.close()
                logger.removeHandler(h)
            assert os.path.exists(log_file)
            with open(log_file, encoding="utf-8") as fh:
                content = fh.read()
            assert "test log message" in content
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)

    def test_get_logger(self):
        logger = get_logger("netdoctor.tests")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "netdoctor.tests"

    def test_configure_logging_idempotent(self):
        logger1 = configure_logging(console=False)
        logger2 = configure_logging(console=False)
        assert logger1 is logger2
        # Should not duplicate handlers
        assert len(logger1.handlers) == len(logger2.handlers)

import pytest
from core.logger import setup_logger, system_logger


class TestLogger:
    def test_setup_logger_returns_logger(self):
        logger = setup_logger("test-agent")
        assert logger.name == "test-agent"
        assert logger.level == 20  # INFO

    def test_system_logger_exists(self):
        assert system_logger is not None
        assert system_logger.name == "WORKSTATION"

    def test_logger_has_handlers(self):
        logger = setup_logger("test-handlers")
        assert len(logger.handlers) >= 2

    def test_logger_handlers_not_duplicated(self):
        logger1 = setup_logger("test-no-dupe")
        h1 = len(logger1.handlers)
        logger2 = setup_logger("test-no-dupe")
        assert len(logger2.handlers) == h1

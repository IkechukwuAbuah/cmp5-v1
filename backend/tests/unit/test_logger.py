"""Unit tests for structured logger."""

import json
import logging
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.lib.logger import (
    StructuredFormatter,
    setup_logger,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id
)


class TestStructuredFormatter:
    """Test structured logging formatter."""

    def test_format_basic_log(self):
        """Test basic log formatting as JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        log_obj = json.loads(result)

        assert log_obj["level"] == "INFO"
        assert log_obj["logger"] == "test.logger"
        assert log_obj["message"] == "Test message"
        assert log_obj["module"] == "test"
        assert log_obj["line"] == 10
        assert "timestamp" in log_obj

    def test_format_with_correlation_id(self):
        """Test formatting with correlation ID."""
        formatter = StructuredFormatter()
        set_correlation_id("test-correlation-123")

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)
        log_obj = json.loads(result)

        assert log_obj["correlation_id"] == "test-correlation-123"

        clear_correlation_id()

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Add extra fields
        record.channel_type = "voice"
        record.session_id = "session-123"
        record.user_agent = "TestAgent/1.0"
        record.request_method = "POST"
        record.request_path = "/api/v1/test"
        record.response_status = 200
        record.response_time_ms = 123.45
        record.circuit_breaker_status = "closed"
        record.external_api = "TEST_API"

        result = formatter.format(record)
        log_obj = json.loads(result)

        assert log_obj["channel_type"] == "voice"
        assert log_obj["session_id"] == "session-123"
        assert log_obj["user_agent"] == "TestAgent/1.0"
        assert log_obj["request_method"] == "POST"
        assert log_obj["request_path"] == "/api/v1/test"
        assert log_obj["response_status"] == 200
        assert log_obj["response_time_ms"] == 123.45
        assert log_obj["circuit_breaker_status"] == "closed"
        assert log_obj["external_api"] == "TEST_API"

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )

            result = formatter.format(record)
            log_obj = json.loads(result)

            assert "exception" in log_obj
            assert "ValueError: Test error" in log_obj["exception"]


class TestLoggerSetup:
    """Test logger setup and configuration."""

    def test_setup_logger_console(self):
        """Test logger setup with console handler."""
        logger = setup_logger(name="test_logger", level="INFO")

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    @patch('src.lib.logger.logging.handlers.RotatingFileHandler')
    def test_setup_logger_with_file(self, mock_file_handler):
        """Test logger setup with file handler."""
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler

        logger = setup_logger(
            name="test_logger",
            level="DEBUG",
            log_file="/tmp/test.log"
        )

        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        mock_file_handler.assert_called_once_with(
            "/tmp/test.log",
            maxBytes=10_485_760,
            backupCount=5,
            encoding='utf-8'
        )

    def test_get_logger(self):
        """Test getting logger with consistent naming."""
        logger = get_logger("test.module")
        assert logger.name == "efl_agent.test.module"

    def test_logger_levels(self):
        """Test different log levels."""
        for level_name in ["DEBUG", "INFO", "WARN", "ERROR"]:
            logger = setup_logger(name=f"test_{level_name}", level=level_name)
            expected_level = getattr(logging, level_name.upper())
            assert logger.level == expected_level


class TestCorrelationId:
    """Test correlation ID management."""

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "correlation-test-456"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
        clear_correlation_id()

    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

        clear_correlation_id()
        assert get_correlation_id() is None

    def test_correlation_id_context_isolation(self):
        """Test that correlation ID is context-isolated."""
        # This is a simplified test - in practice, you'd test with async contexts
        set_correlation_id("context-1")
        assert get_correlation_id() == "context-1"

        # Clear and set new ID
        clear_correlation_id()
        set_correlation_id("context-2")
        assert get_correlation_id() == "context-2"

        clear_correlation_id()


class TestAsyncLoggingHandler:
    """Test async logging handler."""

    def test_async_handler_emission(self):
        """Test that async handler emits records."""
        # Create a mock handler
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO

        from src.lib.logger import AsyncLoggingHandler
        async_handler = AsyncLoggingHandler(mock_handler)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )

        async_handler.emit(record)
        mock_handler.emit.assert_called_once_with(record)

    def test_async_handler_error_handling(self):
        """Test async handler error handling."""
        # Create a handler that raises an exception
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO
        mock_handler.emit.side_effect = Exception("Handler error")

        from src.lib.logger import AsyncLoggingHandler
        async_handler = AsyncLoggingHandler(mock_handler)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )

        # Should not raise, but handle error internally
        with patch.object(async_handler, 'handleError') as mock_handle_error:
            async_handler.emit(record)
            mock_handle_error.assert_called_once_with(record)
"""Structured logging configuration for EFL Agent Assistant."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter with correlation ID support."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        correlation_id = correlation_id_context.get()

        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, 'channel_type'):
            log_obj['channel_type'] = record.channel_type

        if hasattr(record, 'session_id'):
            log_obj['session_id'] = record.session_id

        if hasattr(record, 'user_agent'):
            log_obj['user_agent'] = record.user_agent

        if hasattr(record, 'request_method'):
            log_obj['request_method'] = record.request_method

        if hasattr(record, 'request_path'):
            log_obj['request_path'] = record.request_path

        if hasattr(record, 'response_status'):
            log_obj['response_status'] = record.response_status

        if hasattr(record, 'response_time_ms'):
            log_obj['response_time_ms'] = record.response_time_ms

        if hasattr(record, 'circuit_breaker_status'):
            log_obj['circuit_breaker_status'] = record.circuit_breaker_status

        if hasattr(record, 'external_api'):
            log_obj['external_api'] = record.external_api

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


class AsyncLoggingHandler(logging.Handler):
    """Asynchronous logging handler to minimize performance impact."""

    def __init__(self, handler: logging.Handler):
        super().__init__()
        self.handler = handler
        self.setLevel(handler.level)

    def emit(self, record: logging.LogRecord):
        """Emit log record asynchronously."""
        try:
            self.handler.emit(record)
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str = "efl_agent",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up structured logger with JSON formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARN, ERROR)
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    formatter = StructuredFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(AsyncLoggingHandler(console_handler))

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_485_760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(AsyncLoggingHandler(file_handler))

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with consistent configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"efl_agent.{name}")


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context.

    Args:
        correlation_id: Unique request correlation ID
    """
    correlation_id_context.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context.

    Returns:
        Current correlation ID or None
    """
    return correlation_id_context.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from context."""
    correlation_id_context.set(None)
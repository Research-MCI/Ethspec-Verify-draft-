"""Structured logging utilities using structlog.

This module provides consistent logging across the application with
support for both console and JSON output formats.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(
    level: str = "INFO",
    format: str = "console",
    *,
    include_timestamp: bool = True,
) -> None:
    """Set up structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ('console' or 'json')
        include_timestamp: Whether to include timestamps in logs
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Build processor chain
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if include_timestamp:
        shared_processors.insert(0, structlog.processors.TimeStamper(fmt="iso"))

    if format == "json":
        # JSON format for production/logging systems
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.BoundLogger:
    """Get a logger instance with optional initial context.

    Args:
        name: Logger name (usually __name__)
        **initial_context: Initial context to bind to the logger

    Returns:
        Configured BoundLogger instance
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class LoggerMixin:
    """Mixin class that provides a logger property.

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("doing something", key="value")
    """

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get a logger bound with the class name."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_execution_time(logger: structlog.BoundLogger, operation: str):
    """Context manager for logging execution time.

    Args:
        logger: Logger instance to use
        operation: Name of the operation being timed

    Usage:
        with log_execution_time(logger, "database_query"):
            result = await db.query(...)
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def timer():
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            logger.info(
                "operation_completed",
                operation=operation,
                elapsed_seconds=round(elapsed, 3),
            )

    return timer()


async def log_async_execution_time(logger: structlog.BoundLogger, operation: str):
    """Async context manager for logging execution time.

    Args:
        logger: Logger instance to use
        operation: Name of the operation being timed

    Usage:
        async with log_async_execution_time(logger, "api_call"):
            result = await api.call(...)
    """
    import time
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def timer():
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            logger.info(
                "operation_completed",
                operation=operation,
                elapsed_seconds=round(elapsed, 3),
            )

    return timer()

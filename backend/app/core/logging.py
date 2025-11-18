"""Structured logging configuration."""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record.

        Args:
            log_record: Log record dictionary
            record: Original log record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add log level
        log_record["level"] = record.levelname

        # Add logger name
        log_record["logger"] = record.name

        # Add source location
        log_record["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add process and thread info
        log_record["process"] = {
            "id": record.process,
            "name": record.processName,
        }
        log_record["thread"] = {
            "id": record.thread,
            "name": record.threadName,
        }


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
) -> None:
    """Setup application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json or text)
        log_file: Optional log file path
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if format_type == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, logger: logging.Logger, **context: Any):
        """Initialize log context.

        Args:
            logger: Logger instance
            **context: Context fields to add
        """
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self) -> "LogContext":
        """Enter context."""
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


def get_logger(name: str) -> logging.Logger:
    """Get logger with structured logging.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

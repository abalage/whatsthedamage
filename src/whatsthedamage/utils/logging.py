"""
Simplified logging configuration for whatsthedamage application.

This module provides a thin wrapper around Python's native logging
to add structured formatting while keeping the implementation simple and maintainable.
"""
import logging
import sys
import json
import datetime
from typing import Optional, Any, Tuple, MutableMapping, cast


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging output.

    Supports both JSON and text formats based on environment configuration.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as structured data.

        Args:
            record: The log record to format

        Returns:
            Formatted log string (JSON or text)
        """
        # Get log format from the root logger (set by configure_logging)
        root_logger = logging.getLogger()
        use_json = getattr(root_logger, 'use_json_format', False)

        if use_json:
            return self._format_json(record)
        else:
            return self._format_text(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Add contextual information if available
        if hasattr(record, 'context'):
            context = getattr(record, 'context', {})
            # Ensure context is JSON serializable by converting to string if needed
            try:
                json.dumps(context)  # Test if it's JSON serializable
                log_entry["context"] = cast(Any, context)
            except (TypeError, ValueError):
                log_entry["context"] = str(context)
        else:
            # Ensure context key exists even if no context
            log_entry["context"] = str({})

        # Add exception info if available
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)

    def _format_text(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        base_message = f"{datetime.datetime.fromtimestamp(record.created).isoformat()} - " \
                      f"{record.name} - {record.levelname} - {record.getMessage()}"

        # Add context if available
        if hasattr(record, 'context'):
            context = getattr(record, 'context', {})
            if context:
                context_str = " [" + ", ".join(f"{k}={v}" for k, v in context.items()) + "]"
                base_message += context_str

        # Add exception info if available
        if record.exc_info:
            base_message += f"\n{self.formatException(record.exc_info)}"

        return base_message


class LoggerAdapter(logging.LoggerAdapter[Any]):
    """
    Logger adapter that adds contextual information to log records.

    This allows adding context like request IDs, session IDs, etc.
    """

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> Tuple[str, MutableMapping[str, Any]]:
        """
        Process the logging message to add context.

        Args:
            msg: The log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of (message, updated kwargs)
        """
        # Add context to the extra dictionary
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        # Merge our context with any existing context
        kwargs['extra']['context'] = {**getattr(self, 'context', {}),
                                      **kwargs['extra'].get('context', {})}

        # Remove 'context' from kwargs if it exists to avoid passing it as a separate parameter
        kwargs.pop('context', None)

        return msg, kwargs


def configure_logging(log_level: str = "WARN", log_output: str = "stdout", log_format: str = "text") -> None:
    """
    Configure the root logger with structured formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARN, ERROR)
        log_output: Output destination ('stdout' or filename)
        log_format: Log format ('text' or 'json')

    This should be called once at application startup.
    """
    # Lowercase the log level for case-insensitive comparison
    log_level = log_level.upper()

    # Validate and set log level
    try:
        numeric_level = getattr(logging, log_level, logging.WARN)
    except AttributeError:
        # Fallback to WARN if invalid level
        numeric_level = logging.WARN

    # Remove any existing handlers to avoid duplication
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up formatter with log format
    formatter = StructuredFormatter()
    use_json_format = log_format.lower() == "json"

    # Configure output based on log_output parameter
    if log_output.lower() == "stdout":
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # File handler
        try:
            file_handler = logging.FileHandler(log_output)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            print(f"Warning: Could not configure file logging to {log_output}: {e}",
                  file=sys.stderr)
            # Fallback to stdout if file logging fails
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

    root_logger.setLevel(numeric_level)

    # Set the log format on the root logger so it's available to all handlers
    # We need to set this as an attribute on the Logger object
    # This is safe to do - Python allows adding custom attributes to objects
    # Disable mypy error for dynamically added attribute
    setattr(root_logger, 'use_json_format', use_json_format)


def get_logger(name: Optional[str] = None) -> LoggerAdapter:
    """
    Get a logger instance with the specified name.

    Args:
        name: Optional logger name. If None, uses the calling module's name.

    Returns:
        Configured LoggerAdapter instance
    """
    if name is None:
        # Get the calling module's name
        frame = sys._getframe(1)
        module_name: str | None = None
        current_frame: Any = frame
        while current_frame is not None:
            module_name = current_frame.f_globals.get("__name")
            if module_name and not module_name.startswith("logging"):
                break
            current_frame = current_frame.f_back
        name = module_name or "whatsthedamage"

    # Return a LoggerAdapter instead of raw logger
    return LoggerAdapter(logging.getLogger(name), {})


# Configure root logger for any modules that use logging.getLogger() directly
# Default configuration that will be overridden by configure_logging()
logging.basicConfig(
    level=logging.WARN,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

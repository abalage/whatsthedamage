"""
Error handlers for API endpoints.

Converts exceptions to the canonical API error shape: a JSON body
with an ``error`` message (plus ``details`` for validation errors).
Unexpected exceptions never expose their text to the client.
"""
from typing import Any, Protocol
from flask import jsonify, Response, request, Flask
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, HTTPException
from pydantic import ValidationError
from whatsthedamage.utils.logging import get_logger


class ExceptionHandler(Protocol):
    """Protocol for exception handler functions."""
    def __call__(self, error: Any) -> tuple[Response, int]: ...


logger = get_logger(__name__)


API_PREFIX = '/api/'


def handle_bad_request(error: BadRequest) -> tuple[Response, int]:
    """
    Handle 400 Bad Request errors.

    Args:
        error: The BadRequest exception

    Returns:
        tuple: JSON response and status code 400
    """
    message = str(error.description) if error.description else "Invalid request"
    return jsonify({'error': message}), 400


def handle_file_not_found(error: FileNotFoundError) -> tuple[Response, int]:
    """
    Handle FileNotFoundError.

    Args:
        error: The FileNotFoundError exception

    Returns:
        tuple: JSON response and status code 400
    """
    return jsonify({'error': 'File not found'}), 400


def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    """
    Handle Pydantic ValidationError.

    Args:
        error: The ValidationError exception

    Returns:
        tuple: JSON response and status code 400
    """
    validation_errors = []
    for err in error.errors():
        field = ".".join(str(loc) for loc in err['loc'])
        validation_errors.append(f"{field}: {err['msg']}")

    return jsonify({
        'error': 'Validation Error',
        'details': validation_errors
    }), 400


def handle_value_error(error: ValueError) -> tuple[Response, int]:
    """
    Handle ValueError (typically from data processing).

    Args:
        error: The ValueError exception

    Returns:
        tuple: JSON response and status code 422
    """
    return jsonify({'error': str(error)}), 422


def handle_request_entity_too_large(error: RequestEntityTooLarge) -> tuple[Response, int]:
    """
    Handle 413 Request Entity Too Large errors.

    Args:
        error: The RequestEntityTooLarge exception

    Returns:
        tuple: JSON response and status code 413
    """
    message = (
        str(error.description) if error.description
        else "Uploaded file is too large"
    )
    return jsonify({'error': message}), 413


def handle_generic_exception(error: Exception) -> tuple[Response, int]:
    """
    Handle all other exceptions.

    The exception text is never exposed to the client; the full
    exception is logged server-side instead.

    Args:
        error: The generic exception

    Returns:
        tuple: JSON response and status code 500
    """
    request_context = {
        "error_type": type(error).__name__,
        "path": request.path if request else "unknown",
        "method": request.method if request else "unknown",
        "user_agent": request.user_agent.string if request and request.user_agent else "unknown",
        "remote_addr": request.remote_addr if request else "unknown"
    }

    logger.exception("Unhandled exception in API endpoint", extra={"context": request_context})

    return jsonify({'error': 'Internal Server Error'}), 500


def register_error_handlers(app: Flask) -> None:
    """
    Register all error handlers for the Flask application.

    Only applies to /api/* routes to avoid interfering with web UI error handling.

    Args:
        app: The Flask application instance
    """
    def is_api_request() -> bool:
        """Check if the current request is for an API endpoint."""
        return bool(request and request.path.startswith(API_PREFIX))

    def wrap_handler(
        handler_func: ExceptionHandler, is_generic: bool = False
    ) -> ExceptionHandler:
        """Wrap a handler to only apply to API requests."""
        def wrapped(error: Any) -> tuple[Response, int]:
            if not is_api_request():
                if is_generic and isinstance(error, HTTPException):
                    return error.get_response(), error.code  # type: ignore
                raise error
            return handler_func(error)
        return wrapped

    # List of (exception_type, handler_function, is_generic) tuples
    handlers_config = [
        (BadRequest, handle_bad_request, False),
        (FileNotFoundError, handle_file_not_found, False),
        (ValidationError, handle_validation_error, False),
        (ValueError, handle_value_error, False),
        (RequestEntityTooLarge, handle_request_entity_too_large, False),
        (Exception, handle_generic_exception, True),
    ]

    for exc_type, handler, is_generic in handlers_config:
        app.errorhandler(exc_type)(wrap_handler(handler, is_generic))  # type: ignore[arg-type]

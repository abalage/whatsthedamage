"""
Error handlers for API endpoints.

Converts exceptions to standardized ErrorResponse JSON format.
"""
from typing import Any, Protocol
from flask import jsonify, Response, request, Flask
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, HTTPException
from pydantic import ValidationError
from whatsthedamage.models.api_models import ErrorResponse
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
    error_response = ErrorResponse(
        code=400,
        message="Bad Request",
        details={"error": str(error.description) if error.description else "Invalid request"}
    )
    return jsonify(error_response.model_dump()), 400


def handle_file_not_found(error: FileNotFoundError) -> tuple[Response, int]:
    """
    Handle FileNotFoundError.

    Args:
        error: The FileNotFoundError exception

    Returns:
        tuple: JSON response and status code 400
    """
    error_response = ErrorResponse(
        code=400,
        message="File Not Found",
        details={"error": str(error)}
    )
    return jsonify(error_response.model_dump()), 400


def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
    """
    Handle Pydantic ValidationError.

    Args:
        error: The ValidationError exception

    Returns:
        tuple: JSON response and status code 400
    """
    # Extract validation errors from Pydantic
    validation_errors = []
    for err in error.errors():
        field = ".".join(str(loc) for loc in err['loc'])
        validation_errors.append(f"{field}: {err['msg']}")

    error_response = ErrorResponse(
        code=400,
        message="Validation Error",
        details={"errors": validation_errors}
    )
    return jsonify(error_response.model_dump()), 400


def handle_value_error(error: ValueError) -> tuple[Response, int]:
    """
    Handle ValueError (typically from data processing).

    Args:
        error: The ValueError exception

    Returns:
        tuple: JSON response and status code 422
    """
    error_response = ErrorResponse(
        code=422,
        message="Unprocessable Entity",
        details={"error": str(error)}
    )
    return jsonify(error_response.model_dump()), 422


def handle_request_entity_too_large(error: RequestEntityTooLarge) -> tuple[Response, int]:
    """
    Handle 413 Request Entity Too Large errors.

    Args:
        error: The RequestEntityTooLarge exception

    Returns:
        tuple: JSON response and status code 413
    """
    error_response = ErrorResponse(
        code=413,
        message="Request Entity Too Large",
        details={"error": str(error.description) if error.description else "Uploaded file is too large"}
    )
    return jsonify(error_response.model_dump()), 413


def handle_generic_exception(error: Exception) -> tuple[Response, int]:
    """
    Handle all other exceptions.

    Args:
        error: The generic exception

    Returns:
        tuple: JSON response and status code 500
    """
    # Extract request context for logging
    request_context = {
        "error_type": type(error).__name__,
        "path": request.path if request else "unknown",
        "method": request.method if request else "unknown",
        "user_agent": request.user_agent.string if request and request.user_agent else "unknown",
        "remote_addr": request.remote_addr if request else "unknown"
    }

    # Log the full exception for debugging with detailed context
    logger.exception("Unhandled exception in API endpoint", extra={"context": request_context})

    error_response = ErrorResponse(
        code=500,
        message="Internal Server Error",
        details={"error": "An unexpected error occurred"}
    )
    return jsonify(error_response.model_dump()), 500


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

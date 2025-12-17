"""
Error handlers for API endpoints.

Converts exceptions to standardized ErrorResponse JSON format.
"""
from flask import jsonify, Response, request, Flask
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, HTTPException
from pydantic import ValidationError
from whatsthedamage.models.api_models import ErrorResponse


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
    # Log the full exception for debugging (in production, use proper logging)
    import traceback
    traceback.print_exc()
    
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
    
    # Register handlers only for API routes
    @app.errorhandler(BadRequest)
    def _handle_bad_request(error: BadRequest) -> tuple[Response, int]:
        if is_api_request():
            return handle_bad_request(error)
        raise error
    
    @app.errorhandler(FileNotFoundError)
    def _handle_file_not_found(error: FileNotFoundError) -> tuple[Response, int]:
        if is_api_request():
            return handle_file_not_found(error)
        raise error
    
    @app.errorhandler(ValidationError)
    def _handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        if is_api_request():
            return handle_validation_error(error)
        raise error
    
    @app.errorhandler(ValueError)
    def _handle_value_error(error: ValueError) -> tuple[Response, int]:
        if is_api_request():
            return handle_value_error(error)
        raise error
    
    @app.errorhandler(RequestEntityTooLarge)
    def _handle_request_entity_too_large(error: RequestEntityTooLarge) -> tuple[Response, int]:
        if is_api_request():
            return handle_request_entity_too_large(error)
        raise error
    
    @app.errorhandler(Exception)
    def _handle_generic_exception(error: Exception) -> tuple[Response, int]:
        if is_api_request():
            return handle_generic_exception(error)
        # For non-API requests, let HTTP exceptions be handled by Flask's default handlers
        if isinstance(error, HTTPException):
            return error.get_response(), error.code  # type: ignore
        raise error

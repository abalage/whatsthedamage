"""Shared helper functions for API endpoints.

This module provides common functionality used across API versions
to avoid code duplication.
"""
from flask import request, jsonify, current_app, Response
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from pydantic import ValidationError as PydanticValidationError
import os
from typing import Dict, Optional, cast

from whatsthedamage.models.api_models import ProcessingRequest, ErrorResponse
from whatsthedamage.services.validation_service import ValidationService, ValidationError


def _get_validation_service() -> ValidationService:
    """Get validation service from app extensions (dependency injection)."""
    return cast(ValidationService, current_app.extensions['validation_service'])


def validate_csv_file() -> FileStorage:
    """Validate and extract CSV file from request.

    Returns:
        FileStorage: The CSV file object

    Raises:
        BadRequest: If file is missing or invalid
    """
    if 'csv_file' not in request.files:
        raise BadRequest("Missing required file: csv_file")

    csv_file = request.files['csv_file']
    
    # Use ValidationService for validation
    validation_service = _get_validation_service()
    result = validation_service.validate_file_upload(csv_file)
    
    if not result.is_valid:
        raise BadRequest(result.error_message or "Invalid file upload")

    return csv_file


def get_config_file() -> Optional[FileStorage]:
    """Extract optional config file from request.

    Returns:
        FileStorage | None: The config file object or None
    """
    config_file = request.files.get('config_file')
    if not config_file or not config_file.filename:
        return None
    
    # Use ValidationService for validation
    validation_service = _get_validation_service()
    result = validation_service.validate_file_upload(config_file)
    
    if not result.is_valid:
        raise BadRequest(result.error_message or "Invalid config file upload")
    
    return config_file


def parse_request_params() -> ProcessingRequest:
    """Parse and validate request form parameters.

    Returns:
        ProcessingRequest: Validated request parameters

    Raises:
        ValidationError: If parameters are invalid
    """
    return ProcessingRequest(
        start_date=request.form.get('start_date'),
        end_date=request.form.get('end_date'),
        date_format=request.form.get('date_format'),
        ml_enabled=request.form.get('ml_enabled', 'false').lower() == 'true',
        category_filter=request.form.get('category_filter'),
        language=request.form.get('language', 'en')
    )


def save_uploaded_files(csv_file: FileStorage, config_file: Optional[FileStorage]) -> tuple[str, Optional[str]]:
    """Save uploaded files to disk.

    Args:
        csv_file: CSV file object
        config_file: Config file object or None

    Returns:
        tuple: (csv_path, config_path)
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    csv_filename = secure_filename(csv_file.filename or 'upload.csv')
    csv_path = os.path.join(upload_folder, csv_filename)
    csv_file.save(csv_path)

    config_path = None
    if config_file:
        config_filename = secure_filename(config_file.filename or 'config.yml')
        config_path = os.path.join(upload_folder, config_filename)
        config_file.save(config_path)

    return csv_path, config_path


def cleanup_files(csv_path: str, config_path: str | None) -> None:
    """Clean up uploaded files.

    Args:
        csv_path: Path to CSV file
        config_path: Path to config file or None
    """
    if os.path.exists(csv_path):
        os.unlink(csv_path)
    if config_path and os.path.exists(config_path):
        os.unlink(config_path)


def build_date_range(params: ProcessingRequest) -> Optional[Dict[str, str]]:
    """Build date range dictionary from parameters.

    Args:
        params: Processing request parameters

    Returns:
        Dict with start/end dates or None
    """
    if not params.start_date and not params.end_date:
        return None

    date_range = {}
    if params.start_date:
        date_range['start'] = params.start_date
    if params.end_date:
        date_range['end'] = params.end_date

    return date_range


def handle_error(error: Exception) -> tuple[Response, int]:
    """Handle exceptions and return appropriate error response.

    Args:
        error: The exception to handle

    Returns:
        tuple: (jsonified error response, status code)
    """
    if isinstance(error, BadRequest):
        return jsonify(ErrorResponse(
            code=400,
            message=str(error),
            details={"field": "csv_file"}
        ).model_dump()), 400

    if isinstance(error, PydanticValidationError):
        return jsonify(ErrorResponse(
            code=400,
            message="Invalid request parameters",
            details={"errors": [str(err) for err in error.errors()]}
        ).model_dump()), 400
    
    if isinstance(error, ValidationError):
        return jsonify(ErrorResponse(
            code=400,
            message=error.result.error_message or "Validation failed",
            details=error.result.details or {}
        ).model_dump()), 400

    if isinstance(error, FileNotFoundError):
        return jsonify(ErrorResponse(
            code=400,
            message="File not found",
            details={"error": str(error)}
        ).model_dump()), 400

    if isinstance(error, ValueError):
        return jsonify(ErrorResponse(
            code=422,
            message="Processing error",
            details={"error": str(error)}
        ).model_dump()), 422

    return jsonify(ErrorResponse(
        code=500,
        message="Internal server error",
        details={"error": str(error), "type": type(error).__name__}
    ).model_dump()), 500

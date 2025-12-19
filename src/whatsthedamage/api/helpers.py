"""Shared helper functions for API endpoints.

This module provides common functionality used across API versions
to avoid code duplication.
"""
from flask import request, current_app, Response
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import FileStorage
from typing import Dict, Optional, cast

from whatsthedamage.models.api_models import ProcessingRequest
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError


def _get_validation_service() -> ValidationService:
    """Get validation service from app extensions (dependency injection)."""
    return cast(ValidationService, current_app.extensions['validation_service'])


def _get_response_builder_service() -> ResponseBuilderService:
    """Get response builder service from app extensions (dependency injection)."""
    return cast(ResponseBuilderService, current_app.extensions['response_builder_service'])


def _get_file_upload_service() -> FileUploadService:
    """Get file upload service from app extensions (dependency injection)."""
    return cast(FileUploadService, current_app.extensions['file_upload_service'])


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
    """Save uploaded files to disk using FileUploadService.

    Args:
        csv_file: CSV file object
        config_file: Config file object or None

    Returns:
        tuple: (csv_path, config_path)

    Raises:
        BadRequest: If file save or validation fails
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_upload_service = _get_file_upload_service()

    try:
        return file_upload_service.save_files(csv_file, upload_folder, config_file)
    except FileUploadError as e:
        raise BadRequest(str(e))


def cleanup_files(csv_path: str, config_path: str | None) -> None:
    """Clean up uploaded files using FileUploadService.

    Args:
        csv_path: Path to CSV file
        config_path: Path to config file or None
    """
    file_upload_service = _get_file_upload_service()
    file_upload_service.cleanup_files(csv_path, config_path)


def build_date_range(params: ProcessingRequest) -> Optional[Dict[str, str]]:
    """Build date range dictionary from parameters.

    Note: This is kept for backward compatibility but delegates to
    ResponseBuilderService._build_date_range() internally.

    Args:
        params: Processing request parameters

    Returns:
        Dict with start/end dates or None
    """
    return _get_response_builder_service()._build_date_range(params)


def handle_error(error: Exception) -> tuple[Response, int]:
    """Handle exceptions and return appropriate error response.

    Delegates to ResponseBuilderService for consistent error handling
    across API and web endpoints.

    Args:
        error: The exception to handle

    Returns:
        tuple: (jsonified error response, status code)
    """
    # Delegate to ResponseBuilderService for centralized error handling
    return _get_response_builder_service().build_error_response(
        error=error,
        default_code=500,
        default_message="Internal server error",
        context={'field': 'csv_file'} if isinstance(error, BadRequest) else None
    )

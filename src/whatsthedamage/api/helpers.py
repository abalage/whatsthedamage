"""Shared helper functions for API endpoints.

This module provides common functionality used across API versions
to avoid code duplication.
"""
from flask import request, current_app, Response
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import FileStorage
from typing import Optional, cast

from whatsthedamage.models.api.requests import ProcessingRequest
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.response_formatting_service import ResponseFormattingService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.drilldown_response_service import DrilldownResponseService


def _get_response_formatting_service() -> ResponseFormattingService:
    """Get response builder service from app extensions (dependency injection)."""
    return cast(ResponseFormattingService, current_app.extensions['response_formatting_service'])


def _get_file_upload_service() -> FileUploadService:
    """Get file upload service from app extensions (dependency injection)."""
    return cast(FileUploadService, current_app.extensions['file_upload_service'])


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_cache_service() -> CacheService:
    """Get cache service from app extensions (dependency injection)."""
    return cast(CacheService, current_app.extensions['cache_service'])


def _get_id_mapping_service() -> IdMappingService:
    """Get ID mapping service from app extensions (dependency injection)."""
    return cast(IdMappingService, current_app.extensions['id_mapping_service'])


def _get_statistical_service() -> StatisticalAnalysisService:
    """Get statistical analysis service from app extensions (dependency injection)."""
    return cast(StatisticalAnalysisService, current_app.extensions['statistical_analysis_service'])


def _get_drilldown_response_service() -> DrilldownResponseService:
    """Get drilldown response service from app extensions (dependency injection)."""
    return cast(DrilldownResponseService, current_app.extensions['drilldown_response_service'])


def _get_session_service() -> SessionService:
    """Get session service from app extensions (dependency injection)."""
    return cast(SessionService, current_app.extensions['session_service'])


def _get_configuration_service() -> ConfigurationService:
    """Get ConfigurationService from app extensions (dependency injection)."""
    return cast(ConfigurationService, current_app.extensions['configuration_service'])


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

    # Use FileUploadService for validation
    file_upload_service = _get_file_upload_service()
    result = file_upload_service.validate_file_upload(csv_file)

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

    # Use FileUploadService for validation
    file_upload_service = _get_file_upload_service()
    result = file_upload_service.validate_file_upload(config_file)

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


def handle_error(error: Exception, endpoint_name: Optional[str] = None) -> tuple[Response, int]:
    """Handle exceptions and return appropriate error response.

    Delegates to ResponseFormattingService for consistent error handling
    across API and web endpoints. Automatically logs errors and handles
    ValueError as 404, BadRequest as 400, and others as 500.

    Falls back to simple error response if services are not available
    (e.g., during testing or initialization).

    Args:
        error: The exception to handle
        endpoint_name: Optional name of the endpoint for logging context

    Returns:
        tuple: (jsonified error response, status code)
    """
    from flask import jsonify
    from whatsthedamage.utils.logging import get_logger
    logger = get_logger(__name__)

    # Log the error with context
    if endpoint_name:
        logger.error(f"Error in {endpoint_name}: {error}")
    else:
        logger.error(f"API error: {error}")

    # Determine status code and message based on exception type
    if isinstance(error, ValueError):
        status_code = 404
        message = str(error)
    elif isinstance(error, BadRequest):
        status_code = 400
        message = str(error)
    else:
        status_code = 500
        message = "Internal server error"

    # Try to use the response builder service if available
    try:
        response_builder = _get_response_formatting_service()
        return response_builder.build_error_response(
            error=error,
            default_code=status_code,
            default_message=message,
            context={'field': 'csv_file'} if isinstance(error, BadRequest) else None
        )
    except (KeyError, RuntimeError):
        # Service not available (e.g., during testing), fall back to simple response
        return jsonify({'code': status_code, 'message': message}), status_code

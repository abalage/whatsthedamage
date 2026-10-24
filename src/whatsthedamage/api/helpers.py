"""Shared helper functions for API endpoints.

This module provides common functionality used across API versions
to avoid code duplication.
"""
from __future__ import annotations

from flask import request, current_app, Response, jsonify
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import FileStorage
from typing import TYPE_CHECKING, Any, Optional, cast

from whatsthedamage.models.api.requests import ProcessingRequest

if TYPE_CHECKING:
    from whatsthedamage.models.repositories.processing_result_repository import SqlAlchemyProcessingResultRepository
    from whatsthedamage.models.repositories.transaction_repository import SqlAlchemyTransactionRepository
    from whatsthedamage.models.repositories.correction_repository import SqlAlchemyCorrectionRepository
    from whatsthedamage.models.repositories.shared_correction_repository import SqlAlchemySharedCorrectionRepository
from whatsthedamage.services.deduplication_service import DeduplicationService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.correction_service import CorrectionService
from whatsthedamage.services.data_export_service import DataExportService
from whatsthedamage.services.transaction_import_service import (
    TransactionImportService
)




def create_error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    retry_after: Optional[int] = None
) -> tuple[dict[str, Any], int]:
    """Create a standardized error response.

    Single error shape for all API failures: a human-readable
    message, an optional machine-readable code, and an optional
    retry_after hint for rate limiting.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code.
        error_code: Machine-readable error code.
        retry_after: Seconds to wait before retry (for rate limiting).

    Returns:
        Tuple of (error_dict, status_code).
    """
    error_dict: dict[str, Any] = {'error': message}
    if error_code:
        error_dict['code'] = error_code
    if retry_after is not None:
        error_dict['retry_after'] = str(retry_after)
    return error_dict, status_code


def _get_file_upload_service() -> FileUploadService:
    """Get file upload service from app extensions (dependency injection)."""
    return cast(FileUploadService, current_app.extensions['file_upload_service'])


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])






def _get_statistical_service() -> StatisticalAnalysisService:
    """Get statistical analysis service from app extensions (dependency injection)."""
    return cast(StatisticalAnalysisService, current_app.extensions['statistical_analysis_service'])








def _get_deduplication_service() -> DeduplicationService:
    """Get deduplication service from app extensions (dependency injection)."""
    return cast(DeduplicationService, current_app.extensions['deduplication_service'])


def _get_transaction_import_service() -> TransactionImportService:
    """Get transaction import service from app extensions (dependency injection)."""
    return cast(TransactionImportService, current_app.extensions['transaction_import_service'])


def _get_correction_service() -> CorrectionService:
    """Get correction service from app extensions (dependency injection)."""
    return cast(CorrectionService, current_app.extensions['correction_service'])


def _get_data_export_service() -> DataExportService:
    """Get data export service from app extensions (dependency injection)."""
    return cast(DataExportService, current_app.extensions['data_export_service'])


def _get_processing_result_repository() -> SqlAlchemyProcessingResultRepository:
    """Get processing result repository from app extensions (dependency injection)."""
    from whatsthedamage.models.repositories.processing_result_repository import SqlAlchemyProcessingResultRepository
    return cast(SqlAlchemyProcessingResultRepository, current_app.extensions['processing_result_repository'])


def _get_transaction_repository() -> SqlAlchemyTransactionRepository:
    """Get transaction repository from app extensions (dependency injection)."""
    from whatsthedamage.models.repositories.transaction_repository import SqlAlchemyTransactionRepository
    return cast(SqlAlchemyTransactionRepository, current_app.extensions['transaction_repository'])


def _get_correction_repository() -> SqlAlchemyCorrectionRepository:
    """Get correction repository from app extensions (dependency injection)."""
    from whatsthedamage.models.repositories.correction_repository import SqlAlchemyCorrectionRepository
    return cast(SqlAlchemyCorrectionRepository, current_app.extensions['correction_repository'])


def _get_shared_correction_repository() -> SqlAlchemySharedCorrectionRepository:
    """Get shared correction repository from app extensions (dependency injection)."""
    from whatsthedamage.models.repositories.shared_correction_repository import SqlAlchemySharedCorrectionRepository
    return cast(SqlAlchemySharedCorrectionRepository, current_app.extensions['shared_correction_repository'])


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
        csv_profile_id=request.form.get('csv_profile_id')
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
    """Handle exceptions and return the API error response.

    Single error path for API endpoints. BadRequest and ValueError
    carry controlled, client-facing validation messages and map to
    400; the exception text of unexpected errors is never exposed to
    the client (generic 500 message), the full exception is logged
    server-side instead.

    Args:
        error: The exception to handle
        endpoint_name: Optional name of the endpoint for logging context

    Returns:
        tuple: (jsonified error response, status code)
    """
    from flask import jsonify
    from whatsthedamage.utils.logging import get_logger
    logger = get_logger(__name__)

    context = f" in {endpoint_name}" if endpoint_name else ""

    if isinstance(error, BadRequest):
        logger.error(f"API error{context}: {error}")
        return jsonify({'error': str(error)}), 400
    if isinstance(error, FileNotFoundError):
        logger.error(f"API error{context}: {error}")
        return jsonify({'error': 'File not found'}), 400
    if isinstance(error, ValueError):
        logger.error(f"API error{context}: {error}")
        return jsonify({'error': str(error)}), 400

    logger.exception(f"Unhandled API error{context}")
    return jsonify({'error': 'Internal server error'}), 500

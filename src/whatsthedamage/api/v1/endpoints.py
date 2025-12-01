"""API v1 endpoints - Summary processing only.

This module provides REST API endpoints for processing CSV transaction files
and returning summarized totals by category. v1 API returns only aggregated
summary data (naturally small payloads), without transaction-level details.
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from pydantic import ValidationError
import time
import os
from typing import Dict, Any

from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.models.api_models import (
    ProcessingRequest,
    SummaryResponse,
    SummaryMetadata,
    ErrorResponse
)


# Create Blueprint
v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Initialize service
_processing_service = ProcessingService()


def _validate_csv_file():
    """Validate and extract CSV file from request.

    Returns:
        FileStorage: The CSV file object

    Raises:
        BadRequest: If file is missing or invalid
    """
    if 'csv_file' not in request.files:
        raise BadRequest("Missing required file: csv_file")

    csv_file = request.files['csv_file']
    if not csv_file.filename:
        raise BadRequest("No file selected for csv_file")

    return csv_file


def _get_config_file():
    """Extract optional config file from request.

    Returns:
        FileStorage | None: The config file object or None
    """
    config_file = request.files.get('config_file')
    if config_file and not config_file.filename:
        return None
    return config_file


def _parse_request_params() -> ProcessingRequest:
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


def _save_uploaded_files(csv_file, config_file):
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


def _cleanup_files(csv_path: str, config_path: str | None) -> None:
    """Clean up uploaded files.

    Args:
        csv_path: Path to CSV file
        config_path: Path to config file or None
    """
    if os.path.exists(csv_path):
        os.unlink(csv_path)
    if config_path and os.path.exists(config_path):
        os.unlink(config_path)


def _build_date_range(params: ProcessingRequest) -> Dict[str, str] | None:
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


def _build_summary_response(result: Dict, params: ProcessingRequest, processing_time: float) -> SummaryResponse:
    """Build summary response from processing result.

    Args:
        result: Processing result from service
        params: Request parameters
        processing_time: Total processing time

    Returns:
        SummaryResponse object
    """
    return SummaryResponse(
        data=result['data'],
        metadata=SummaryMetadata(
            row_count=result['metadata']['row_count'],
            processing_time=processing_time,
            ml_enabled=params.ml_enabled,
            date_range=_build_date_range(params)
        )
    )


def _handle_error(error: Exception) -> tuple:
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

    if isinstance(error, ValidationError):
        return jsonify(ErrorResponse(
            code=400,
            message="Invalid request parameters",
            details={"errors": [str(err) for err in error.errors()]}
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


@v1_bp.route('/process', methods=['POST'])
def process_transactions():
    """Process CSV transaction file and return summary totals.

    Accepts multipart/form-data with:
    - csv_file (required): CSV file with bank transactions
    - config_file (optional): YAML configuration file
    - start_date (optional): Filter start date
    - end_date (optional): Filter end date
    - date_format (optional): Date format string (default from config)
    - ml_enabled (optional): Enable ML categorization (default: false)
    - category_filter (optional): Filter by specific category
    - language (optional): Output language (default: en)

    Returns:
        JSON response with SummaryResponse structure

    Status Codes:
        200: Successfully processed
        400: Bad request (missing file, invalid parameters)
        422: Unprocessable entity (CSV parsing error, validation failed)
        500: Internal server error
    """
    start_time = time.time()

    try:
        csv_file = _validate_csv_file()
        config_file = _get_config_file()
        params = _parse_request_params()

        csv_path, config_path = _save_uploaded_files(csv_file, config_file)

        try:
            result = _processing_service.process_summary(
                csv_file_path=csv_path,
                config_file_path=config_path,
                start_date=params.start_date,
                end_date=params.end_date,
                ml_enabled=params.ml_enabled,
                category_filter=params.category_filter,
                language=params.language
            )

            processing_time = time.time() - start_time
            response = _build_summary_response(result, params, processing_time)

            return jsonify(response.model_dump()), 200

        finally:
            _cleanup_files(csv_path, config_path)

    except Exception as e:
        return _handle_error(e)

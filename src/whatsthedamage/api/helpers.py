"""Shared helper functions for API endpoints.

This module provides common functionality used across API versions
to avoid code duplication.
"""
from flask import request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from pydantic import ValidationError
import os
from typing import Dict

from whatsthedamage.models.api_models import ProcessingRequest, ErrorResponse


def validate_csv_file():
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


def get_config_file():
    """Extract optional config file from request.

    Returns:
        FileStorage | None: The config file object or None
    """
    config_file = request.files.get('config_file')
    if config_file and not config_file.filename:
        return None
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


def save_uploaded_files(csv_file, config_file):
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


def build_date_range(params: ProcessingRequest) -> Dict[str, str] | None:
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


def handle_error(error: Exception) -> tuple:
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

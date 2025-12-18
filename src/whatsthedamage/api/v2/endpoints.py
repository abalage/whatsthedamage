"""API v2 endpoints - Detailed transaction processing.

This module provides REST API endpoints for processing CSV transaction files
with detailed transaction-level data for DataTables rendering.
"""
from flask import Blueprint, jsonify, Response, current_app
import time

from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.api.helpers import (
    validate_csv_file,
    get_config_file,
    parse_request_params,
    save_uploaded_files,
    cleanup_files,
    handle_error
)


# Create Blueprint
v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    from typing import cast
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_response_builder_service() -> ResponseBuilderService:
    """Get response builder service from app extensions (dependency injection)."""
    from typing import cast
    return cast(ResponseBuilderService, current_app.extensions['response_builder_service'])


@v2_bp.route('/process', methods=['POST'])
def process_transactions() -> tuple[Response, int]:
    """Process CSV transaction file and return detailed transaction data.

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
        JSON response with DetailedResponse structure containing transaction details

    Status Codes:
        200: Successfully processed
        400: Bad request (missing file, invalid parameters)
        422: Unprocessable entity (CSV parsing error, validation failed)
        500: Internal server error
    """
    start_time = time.time()

    try:
        csv_file = validate_csv_file()
        config_file = get_config_file()
        params = parse_request_params()

        csv_path, config_path = save_uploaded_files(csv_file, config_file)

        try:
            result = _get_processing_service().process_with_details(
                csv_file_path=csv_path,
                config_file_path=config_path,
                start_date=params.start_date,
                end_date=params.end_date,
                ml_enabled=params.ml_enabled,
                category_filter=params.category_filter,
                language=params.language
            )

            processing_time = time.time() - start_time
            response = _get_response_builder_service().build_api_detailed_response(
                datatables_response=result['data'],
                metadata=result['metadata'],
                params=params,
                processing_time=processing_time
            )

            return jsonify(response.model_dump()), 200

        finally:
            cleanup_files(csv_path, config_path)

    except Exception as e:
        return handle_error(e)


# Helper functions


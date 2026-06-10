"""API v2 endpoints - Detailed transaction processing.

This module provides REST API endpoints for processing CSV transaction files
with detailed transaction-level data for DataTables rendering.
"""
from flask import Blueprint, jsonify, Response, request
from werkzeug.exceptions import BadRequest
from typing import Tuple
import time

from whatsthedamage.models.domain.dt_models import ProcessingResponse
from whatsthedamage.api.helpers import (
    validate_csv_file,
    get_config_file,
    parse_request_params,
    save_uploaded_files,
    cleanup_files,
    handle_error,
    _get_cache_service,
    _get_response_formatting_service,
    _get_processing_service,
    _get_statistical_service,
    _get_drilldown_response_service,
)


# Create Blueprint
v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')


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
        DetailedResponse: Typed response with processed transaction data

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
            result: ProcessingResponse = _get_processing_service().process_with_details(
                csv_file_path=csv_path,
                config_file_path=config_path,
                start_date=params.start_date,
                end_date=params.end_date,
                ml_enabled=params.ml_enabled,
                category_filter=params.category_filter,
                language=params.language
            )

            # Cache result for drilldown views
            cache_service = _get_cache_service()
            cache_service.set(result.result_id, result)

            processing_time = time.time() - start_time

            # Delegate to service for response construction
            response = _get_response_formatting_service().build_api_detailed_response(
                account_response=result.data,
                metadata=result.metadata,
                params=params,
                processing_time=processing_time,
                result_id=result.result_id
            )

            return jsonify(response.model_dump()), 200

        finally:
            cleanup_files(csv_path, config_path)

    except Exception as e:
        return handle_error(e)


@v2_bp.route('/results/<result_id>', methods=['GET'])
def get_results(result_id: str) -> tuple[Response, int]:
    """Get processed results data for frontend rendering.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        ResultsApiResponse: Typed response with accounts data, highlights, and drilldown URLs

    Status Codes:
        200: Successfully retrieved results
        404: Results not found
        500: Internal server error
    """
    try:
        # Get the cache service to retrieve cached results
        cache_service = _get_cache_service()

        # Retrieve the cached processing result
        cached_result = cache_service.get(result_id)

        if not cached_result:
            return handle_error(ValueError('Results not found'), 'get_results')

        # Delegate to service for response construction
        response = _get_response_formatting_service().format_processing_response_for_frontend(cached_result)

        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e, 'get_results')





# Drilldown endpoints for category, month, and cell-level navigation


@v2_bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months', methods=['GET'])
def get_category_months(result_id: str, account_id: str, category_id: str) -> tuple[Response, int]:
    """Get months and totals for a specific category.

    Delegates to DrilldownResponseService for business logic.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        category_id: Category ID to get months for

    Returns:
        CategoryMonthsApiResponse: Typed response with months data for the category

    Status Codes:
        200: Successfully retrieved category months
        404: Result, account, or category not found
        500: Internal server error
    """
    try:
        drilldown_response_service = _get_drilldown_response_service()
        response = drilldown_response_service.get_category_months_response(
            result_id=result_id,
            account_id=account_id,
            category_id=category_id
        )
        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e, 'get_category_months')


@v2_bp.route('/results/<result_id>/accounts/<account_id>/months/<month_id>/categories', methods=['GET'])
def get_month_categories(result_id: str, account_id: str, month_id: str) -> tuple[Response, int]:
    """Get categories and totals for a specific month.

    Delegates to DrilldownResponseService for business logic.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        month_id: Month ID to get categories for

    Returns:
        MonthCategoriesApiResponse: Typed response with categories data for the month

    Status Codes:
        200: Successfully retrieved month categories
        404: Result, account, or month not found
        500: Internal server error
    """
    try:
        drilldown_response_service = _get_drilldown_response_service()
        response = drilldown_response_service.get_month_categories_response(
            result_id=result_id,
            account_id=account_id,
            month_id=month_id
        )
        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e, 'get_month_categories')


@v2_bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions', methods=['GET'])
def get_category_month_transactions(result_id: str, account_id: str, category_id: str, month_id: str) -> tuple[Response, int]:
    """Get transaction details for a specific category and month.

    Delegates to DrilldownResponseService for business logic.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        category_id: Category ID to filter by
        month_id: Month ID to filter by

    Returns:
        CategoryMonthTransactionsApiResponse: Typed response with transaction details

    Status Codes:
        200: Successfully retrieved transactions
        404: Result, account, category, or month not found
        500: Internal server error
    """
    try:
        drilldown_response_service = _get_drilldown_response_service()
        response = drilldown_response_service.get_category_month_transactions_response(
            result_id=result_id,
            account_id=account_id,
            category_id=category_id,
            month_id=month_id
        )
        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e, 'get_category_month_transactions')


@v2_bp.route('/recalculate-statistics', methods=['POST'])
def recalculate_statistics() -> Tuple[Response, int]:
    """Recalculate statistical highlights with custom algorithm and direction settings.

    Args:
        JSON payload with:
        - result_id (required): UUID of the cached processing result
        - algorithms (required): List of algorithm names (e.g., ['iqr', 'pareto'])
        - direction (required): Direction for analysis ('rows' or 'columns')

    Returns:
        RecalculateApiResponse: Typed response with updated statistical metadata

    Status Codes:
        200: Successfully recalculated statistics
        400: Bad request (missing parameters, invalid values)
        404: Result data not found
        500: Internal server error
    """
    try:
        data = request.get_json()
        if not data:
            return handle_error(BadRequest('No data provided'), 'recalculate_statistics')

        result_id = data.get('result_id')
        algorithms = data.get('algorithms', [])
        direction = data.get('direction', 'columns')

        if not result_id:
            return handle_error(BadRequest('result_id is required'), 'recalculate_statistics')

        if not isinstance(algorithms, list):
            return handle_error(BadRequest('algorithms must be a list'), 'recalculate_statistics')

        if direction not in ['columns', 'rows']:
            return handle_error(BadRequest('direction must be either "columns" or "rows"'), 'recalculate_statistics')

        # Get cached result
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if cached_result is None:
            return handle_error(ValueError('Result data not found or expired'), 'recalculate_statistics')

        # Delegate to service for response construction
        response, updated_metadata = _get_statistical_service().compute_and_format_statistics(
            cached_result, algorithms, direction
        )

        # Update cache with new metadata
        cached_result.statistical_metadata = updated_metadata
        cache_service.set(result_id, cached_result)

        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e, 'recalculate_statistics')

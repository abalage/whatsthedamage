"""API v2 endpoints - Detailed transaction processing.

This module provides REST API endpoints for processing CSV transaction files
with detailed transaction-level data for DataTables rendering.
"""
from flask import Blueprint, jsonify, Response
import time

from whatsthedamage.models.dt_models import ProcessingResponse
from whatsthedamage.api.helpers import (
    validate_csv_file,
    get_config_file,
    parse_request_params,
    save_uploaded_files,
    cleanup_files,
    handle_error,
    _get_cache_service,
    _get_response_builder_service,
    _get_processing_service,
    _get_id_mapping_service
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
            response = _get_response_builder_service().build_api_detailed_response(
                datatables_response=result.data,
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
        JSON response with results data including accounts, highlights, and drilldown URLs

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
            return jsonify({'error': 'Results not found'}), 404

        # Use ResponseFormattingService to format the response
        response_data = _get_response_builder_service().format_processing_response_for_frontend(cached_result)

        # Check if the service returned an error
        if 'error' in response_data:
            return jsonify(response_data), 404

        return jsonify(response_data), 200

    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error in get_results: {e}")
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/results/<result_id>/details', methods=['GET'])
def get_results_details(result_id: str) -> tuple[Response, int]:
    """Get all transaction details for a result in a flattened format.

    This endpoint returns the same data structure as /results/<result_id> but
    is specifically for the Details view which displays all transactions in a
    single flattened table.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        JSON response with all transaction details including accounts, highlights, and drilldown URLs

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
            return jsonify({'error': 'Results not found'}), 404

        # Use ResponseFormattingService to format the response
        # Same format as get_results - includes all details for each aggregated row
        response_data = _get_response_builder_service().format_processing_response_for_frontend(cached_result)

        # Check if the service returned an error
        if 'error' in response_data:
            return jsonify(response_data), 404

        return jsonify(response_data), 200

    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error in get_results_details: {e}")
        return jsonify({'error': str(e)}), 500


# Drilldown endpoints for category, month, and cell-level navigation

def _get_frontend_url(endpoint: str, **values) -> str:
    """Generate URL for frontend Vue router routes.

    These are the routes that the Vue frontend router handles, not Flask routes.
    The frontend will navigate to these paths using the Vue router.
    """
    frontend_routes = {
        'category_months': '/results/{result_id}/accounts/{account_id}/categories/{category_id}/months',
        'month_categories': '/results/{result_id}/accounts/{account_id}/months/{month_id}/categories',
        'category_month_transactions': '/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions'
    }

    if endpoint in frontend_routes:
        return frontend_routes[endpoint].format(**values)
    return "#"


def _find_account_data(cached_result, account_id: str, result_id: str = None):
    """Find account data in cached result by account ID.

    Attempts to match account_id directly first, then tries to resolve
    secure mapped ID to original account number if result_id is provided.
    """
    try:
        if hasattr(cached_result, 'data') and isinstance(cached_result.data, dict):
            # First, try direct match
            for acc_id, account_data in cached_result.data.items():
                if acc_id == account_id:
                    return {
                        'id': acc_id,
                        'name': getattr(account_data, 'name', f'Account {account_id}'),
                        'data': account_data.data if hasattr(account_data, 'data') else []
                    }

            # If no direct match and we have a result_id, try resolving secure ID
            if result_id:
                try:
                    id_mapping_service = _get_id_mapping_service()
                    # Try to resolve account_id as a secure ID to get original account number
                    original_account = id_mapping_service.get_account_number(result_id, account_id)
                    if original_account:
                        for acc_id, account_data in cached_result.data.items():
                            if acc_id == original_account:
                                return {
                                    'id': acc_id,
                                    'name': getattr(account_data, 'name', f'Account {original_account}'),
                                    'data': account_data.data if hasattr(account_data, 'data') else []
                                }
                except Exception:
                    pass  # Fall through to return None
        return None
    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error finding account data for account {account_id}: {e}")
        return None


def _extract_month_key(date_obj) -> str:
    """Extract month key from date object for grouping."""
    try:
        if hasattr(date_obj, 'timestamp'):
            return str(date_obj.timestamp)
        elif hasattr(date_obj, 'display'):
            return date_obj.display
        else:
            return str(date_obj)
    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error extracting month key: {e}")
        return "unknown"


@v2_bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months', methods=['GET'])
def get_category_months(result_id: str, account_id: str, category_id: str) -> tuple[Response, int]:
    """Get months and totals for a specific category.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        category_id: Category ID to get months for

    Returns:
        JSON response with months data for the category

    Status Codes:
        200: Successfully retrieved category months
        404: Result, account, or category not found
        500: Internal server error
    """
    try:
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if not cached_result:
            return jsonify({'error': 'Results not found'}), 404

        account_data = _find_account_data(cached_result, account_id, result_id)

        if not account_data:
            return jsonify({'error': 'Account not found in results'}), 404

        # Resolve secure category_id to original category name
        try:
            id_mapping_service = _get_id_mapping_service()
            original_category = id_mapping_service.get_category_name(result_id, category_id)
        except Exception:
            original_category = category_id  # Fallback to direct use

        category_months = {}

        for row in account_data['data']:
            if hasattr(row, 'category') and row.category == original_category:
                month_key = _extract_month_key(row.date)
                if month_key not in category_months:
                    category_months[month_key] = {
                        'month': row.date.display if hasattr(row.date, 'display') else str(row.date),
                        'month_timestamp': row.date.timestamp if hasattr(row.date, 'timestamp') else month_key,
                        'total': {
                            'display': row.total.display if hasattr(row.total, 'display') else str(row.total),
                            'raw': row.total.raw if hasattr(row.total, 'raw') else 0.0
                        },
                        'row_id': row.row_id if hasattr(row, 'row_id') else '',
                        'details': [detail.model_dump() if hasattr(detail, 'model_dump') else detail for detail in (row.details if hasattr(row, 'details') else [])]
                    }
                else:
                    if hasattr(row.total, 'raw'):
                        category_months[month_key]['total']['raw'] += row.total.raw
                    category_months[month_key]['total']['display'] = f"${category_months[month_key]['total']['raw']:.2f}"

        if not category_months:
            return jsonify({'error': 'Category not found or has no data'}), 404

        months_list = list(category_months.values())
        months_list.sort(key=lambda x: x.get('month', ''))

        for month_data in months_list:
            month_identifier = month_data.get('row_id', '')
            month_data['cell_url'] = _get_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category_id,
                month_id=month_identifier
            )

        category_name = original_category.replace('_', ' ').title()
        for row in account_data['data']:
            if hasattr(row, 'category') and row.category == original_category:
                if hasattr(row, 'category_display'):
                    category_name = row.category_display
                break

        response_data = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'category_id': category_id,
            'category_name': category_name,
            'data': months_list
        }

        return jsonify(response_data), 200

    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error in get_category_months: {e}")
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/results/<result_id>/accounts/<account_id>/months/<month_id>/categories', methods=['GET'])
def get_month_categories(result_id: str, account_id: str, month_id: str) -> tuple[Response, int]:
    """Get categories and totals for a specific month.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        month_id: Month ID to get categories for

    Returns:
        JSON response with categories data for the month

    Status Codes:
        200: Successfully retrieved month categories
        404: Result, account, or month not found
        500: Internal server error
    """
    try:
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if not cached_result:
            return jsonify({'error': 'Results not found'}), 404

        account_data = _find_account_data(cached_result, account_id, result_id)

        if not account_data:
            return jsonify({'error': 'Account not found in results'}), 404

        # Resolve secure month_id to original timestamp
        try:
            id_mapping_service = _get_id_mapping_service()
            original_month_ts = id_mapping_service.get_month_timestamp(month_id)
        except Exception:
            original_month_ts = month_id  # Fallback to direct use

        month_categories = {}

        for row in account_data['data']:
            row_month_key = _extract_month_key(row.date)
            if row_month_key == original_month_ts:
                category = row.category if hasattr(row, 'category') else 'uncategorized'
                if category not in month_categories:
                    month_categories[category] = {
                        'category': category,
                        'total': {
                            'display': row.total.display if hasattr(row.total, 'display') else str(row.total),
                            'raw': row.total.raw if hasattr(row.total, 'raw') else 0.0
                        },
                        'row_id': row.row_id if hasattr(row, 'row_id') else '',
                        'details': [detail.model_dump() if hasattr(detail, 'model_dump') else detail for detail in (row.details if hasattr(row, 'details') else [])]
                    }
                else:
                    if hasattr(row.total, 'raw'):
                        month_categories[category]['total']['raw'] += row.total.raw
                    month_categories[category]['total']['display'] = f"${month_categories[category]['total']['raw']:.2f}"

        if not month_categories:
            return jsonify({'error': 'Month not found or has no data'}), 404

        categories_list = list(month_categories.values())
        categories_list.sort(key=lambda x: x.get('category', ''))

        for category_data in categories_list:
            category_data['category_url'] = _get_frontend_url(
                'category_month_transactions',
                result_id=result_id,
                account_id=account_id,
                category_id=category_data['category'],
                month_id=month_id
            )

        month_name = month_id.replace('-', ' ').title()
        for row in account_data['data']:
            row_month_key = _extract_month_key(row.date)
            if row_month_key == original_month_ts:
                if hasattr(row.date, 'display'):
                    month_name = row.date.display
                break

        response_data = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'month_id': month_id,
            'month_name': month_name,
            'data': categories_list
        }

        return jsonify(response_data), 200

    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error in get_month_categories: {e}")
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions', methods=['GET'])
def get_category_month_transactions(result_id: str, account_id: str, category_id: str, month_id: str) -> tuple[Response, int]:
    """Get transaction details for a specific category and month.

    Args:
        result_id: UUID of the cached processing result
        account_id: Account ID to filter by
        category_id: Category ID to filter by
        month_id: Month ID to filter by

    Returns:
        JSON response with transaction details

    Status Codes:
        200: Successfully retrieved transactions
        404: Result, account, category, or month not found
        500: Internal server error
    """
    try:
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if not cached_result:
            return jsonify({'error': 'Results not found'}), 404

        account_data = _find_account_data(cached_result, account_id, result_id)

        if not account_data:
            return jsonify({'error': 'Account not found in results'}), 404

        # Resolve secure category_id and month_id to original values
        try:
            id_mapping_service = _get_id_mapping_service()
            original_category = id_mapping_service.get_category_name(result_id, category_id)
        except Exception:
            original_category = category_id  # Fallback to direct use

        try:
            original_month_ts = id_mapping_service.get_month_timestamp(month_id)
        except Exception:
            original_month_ts = month_id  # Fallback to direct use

        category_name = original_category.replace('_', ' ').title()
        month_name = original_month_ts.replace('-', ' ').title()

        transactions = []

        for row in account_data['data']:
            row_category = row.category if hasattr(row, 'category') else 'uncategorized'
            row_month_key = _extract_month_key(row.date)

            if row_category == original_category and row_month_key == original_month_ts:
                if hasattr(row, 'category_display'):
                    category_name = row.category_display
                if hasattr(row.date, 'display'):
                    month_name = row.date.display

                if hasattr(row, 'details') and row.details:
                    for detail in row.details:
                        detail_dict = detail.model_dump() if hasattr(detail, 'model_dump') else detail

                        date_obj = detail_dict.get('date', {})
                        amount_obj = detail_dict.get('amount', {})

                        transaction_data = {
                            'date': {
                                'display': date_obj.get('display', '') if isinstance(date_obj, dict) else str(date_obj)
                            },
                            'amount': {
                                'display': amount_obj.get('display', '') if isinstance(amount_obj, dict) else str(amount_obj)
                            },
                            'merchant': detail_dict.get('merchant', ''),
                            'row_id': detail_dict.get('row_id', '')
                        }
                        transactions.append(transaction_data)

        if not transactions:
            return jsonify({'error': 'No transactions found for the specified category and month'}), 404

        response_data = {
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_data['name'],
            'category_id': category_id,
            'category_name': category_name,
            'month_id': month_id,
            'month_name': month_name,
            'data': transactions
        }

        return jsonify(response_data), 200

    except Exception as e:
        from whatsthedamage.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error in get_category_month_transactions: {e}")
        return jsonify({'error': str(e)}), 500


# Helper functions


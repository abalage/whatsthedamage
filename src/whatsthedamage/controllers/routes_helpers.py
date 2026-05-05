"""Helper functions for web route handlers.

This module contains extracted helper functions to reduce complexity in routes.py.
Following the Single Responsibility Principle and DRY patterns.

NOTE: This module has been updated to return JSON responses for the Vue frontend
instead of rendering Jinja2 templates. The old template-based functions have been
replaced with JSON-returning equivalents.

Backwards Compatibility:
- handle_entity_drilldown -> handle_entity_drilldown_json
- show_summary_results -> show_summary_results_json
- show_detail_results -> show_detail_results_json
- handle_category_month_transactions -> handle_category_month_transactions_json
"""
from flask import current_app, Response, jsonify
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.drilldown_service import DrilldownService
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.response_formatting_service import ResponseFormattingService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from typing import Dict, Any, cast, Tuple, List, Union
from whatsthedamage.utils.logging import get_logger

# Backwards compatibility aliases for tests
# These point to the JSON-returning versions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # For type checking, we provide the old names as aliases
    handle_entity_drilldown = handle_entity_drilldown_json
    show_summary_results = show_summary_results_json
    show_detail_results = show_detail_results_json
    handle_category_month_transactions = handle_category_month_transactions_json

logger = get_logger(__name__)


def _get_cache_service() -> CacheService:
    """Get cache service from app extensions (dependency injection)."""
    return cast(CacheService, current_app.extensions['cache_service'])


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_drilldown_service() -> DrilldownService:
    """Get drilldown service from app extensions (dependency injection)."""
    return cast(DrilldownService, current_app.extensions['drilldown_service'])


def _get_data_formatting_service() -> ResponseFormattingService:
    """Get data formatting service from app extensions (dependency injection)."""
    return cast(ResponseFormattingService, current_app.extensions['response_formatting_service'])


def _get_statistical_service() -> StatisticalAnalysisService:
    """Get statistical analysis service from app extensions (dependency injection)."""
    return cast(StatisticalAnalysisService, current_app.extensions['statistical_analysis_service'])


def handle_entity_drilldown_json(
    result_id: str,
    account_id: str,
    entity_id: str,
    entity_type: str,
    template: str = None,
    data_not_found_error: str = 'Data not found',
    index_route: str = None
) -> Union[Response, Tuple[Response, int]]:
    """Unified handler for category and month entity drilldown requests.

    Returns JSON data for Vue frontend instead of rendering templates.

    Note: The 'template' and 'index_route' parameters are accepted for backwards
    compatibility with old code but are not used (the function returns JSON).

    Args:
        result_id: UUID of the cached processing result
        account_id: Secure account ID
        entity_id: Secure entity ID (category_id or month_id)
        entity_type: Type of entity ('category' or 'month')
        template: DEPRECATED - Template name (not used, kept for backwards compatibility)
        data_not_found_error: Error message for missing data
        index_route: DEPRECATED - Route name (not used, kept for backwards compatibility)

    Returns:
        JSON Response with drilldown data or error
    """
    try:
        # Use DrilldownService for all business logic
        drilldown_service = _get_drilldown_service()

        # Resolve IDs to original values using service
        resolution = drilldown_service.resolve_entity_ids(result_id, account_id, entity_id, entity_type)

        if resolution.get('error'):
            return jsonify({'error': resolution['error']}), 404

        account_number = resolution['account_number']
        entity_name = resolution['entity_name']
        filter_value = resolution['filter_value']

        # Get cached data using service
        cache_result = drilldown_service.get_cached_data_for_account(result_id, account_number)

        if cache_result.get('error'):
            return jsonify({'error': cache_result['error']}), 404

        dt_response = cache_result['dt_response']

        # Filter data for the specific entity using service
        filtered_data = drilldown_service.filter_data_for_entity(dt_response, entity_type, filter_value)

        if not filtered_data:
            return jsonify({'error': data_not_found_error}), 404

        # Generate drilldown URLs using service
        drilldown_urls = drilldown_service.generate_drilldown_urls(result_id, account_number, dt_response)

        # Build response context
        formatting_service = _get_data_formatting_service()
        formatted_account = formatting_service.format_account_id(account_number)

        # Build response matching the structure expected by Vue frontend
        return jsonify({
            'status': 'success',
            'result_id': result_id,
            'account_id': account_id,
            'formatted_account': formatted_account,
            'entity_name': entity_name,
            'data': [{
                'date': {'display': row.date.display, 'timestamp': row.date.timestamp},
                'category': row.category,
                'total': {'display': row.total.display, 'raw': row.total.raw},
                'details': row.details,
                'row_id': row.row_id
            } for row in filtered_data],
            'drilldown_urls': {account_id: drilldown_urls},
            'highlights': cache_result.get('highlights', {})
        })

    except Exception as e:
        logger.error(f'Error in handle_entity_drilldown_json: {e}',
                     extra={'context': {'result_id': result_id, 'account_id': account_id,
                                       'entity_id': entity_id, 'entity_type': entity_type}})
        return jsonify({'error': str(e)}), 500


def handle_category_month_transactions_json(
    result_id: str,
    account_id: str,
    category_id: str,
    month_id: str,
    data_not_found_error: str = 'Data not found',
    index_route: str = None
) -> Union[Response, Tuple[Response, int]]:
    """Handler for category-month-transactions drilldown requests.

    Returns JSON data for Vue frontend instead of rendering templates.

    Note: The 'index_route' parameter is accepted for backwards compatibility
    but is not used (the function returns JSON).

    Args:
        result_id: UUID of the cached processing result
        account_id: Secure account ID
        category_id: Secure category ID
        month_id: Secure month ID
        data_not_found_error: Error message for missing data
        index_route: DEPRECATED - Route name (not used, kept for backwards compatibility)

    Returns:
        JSON Response with transaction data or error
    """
    try:
        drilldown_service = _get_drilldown_service()

        # Resolve category ID
        category_resolution = drilldown_service.resolve_entity_ids(result_id, account_id, category_id, 'category')
        if category_resolution.get('error'):
            return jsonify({'error': category_resolution['error']}), 404

        account_number = category_resolution['account_number']
        category_name = category_resolution['entity_name']

        # Resolve month ID
        month_resolution = drilldown_service.resolve_entity_ids(result_id, account_id, month_id, 'month')
        if month_resolution.get('error'):
            return jsonify({'error': month_resolution['error']}), 404
        month_name = month_resolution['entity_name']

        # Get cached data
        cache_result = drilldown_service.get_cached_data_for_account(result_id, account_number)
        if cache_result.get('error'):
            return jsonify({'error': cache_result['error']}), 404

        dt_response = cache_result['dt_response']

        # Filter for specific category and month
        filtered_data = drilldown_service.filter_data_for_category_month(
            dt_response, category_name, month_name
        )

        if not filtered_data:
            return jsonify({'error': data_not_found_error}), 404

        # Build response
        # For category-month-transactions, we need the individual transaction details
        transactions = []
        for row in filtered_data:
            for detail in row.details:
                transactions.append({
                    'date': detail.date.display,
                    'amount': detail.amount.display,
                    'amount_raw': detail.amount.raw if hasattr(detail.amount, 'raw') else None,
                    'merchant': detail.merchant,
                    'currency': detail.currency if hasattr(detail, 'currency') else '',
                    'type': detail.type if hasattr(detail, 'type') else '',
                    'confidence': detail.confidence if hasattr(detail, 'confidence') else None,
                    'row_id': detail.row_id if hasattr(detail, 'row_id') else row.row_id
                })

        formatting_service = _get_data_formatting_service()
        formatted_account = formatting_service.format_account_id(account_number)

        return jsonify({
            'status': 'success',
            'result_id': result_id,
            'account_id': account_id,
            'account_name': account_number,
            'formatted_account': formatted_account,
            'category_id': category_id,
            'category_name': category_name,
            'month_id': month_id,
            'month_name': month_name,
            'data': transactions,
            'highlights': cache_result.get('highlights', {})
        })

    except Exception as e:
        logger.error(f'Error in handle_category_month_transactions_json: {e}',
                     extra={'context': {'result_id': result_id, 'account_id': account_id,
                                       'category_id': category_id, 'month_id': month_id}})
        return jsonify({'error': str(e)}), 500


def show_summary_results_json(result_id: str) -> Union[Response, Tuple[Response, int]]:
    """Show summary results view - returns JSON for Vue frontend.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        JSON Response with results data or error
    """
    try:
        # Get cached result
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if cached_result is None:
            return jsonify({'error': 'Result data not found or expired'}), 404

        # Prepare accounts data for JSON response
        formatting_service = _get_data_formatting_service()
        accounts_data = formatting_service.prepare_accounts_for_template(
            cached_result.data,
            cached_result.statistical_metadata
        )

        # Generate secure drill-down URLs for each account using DrilldownService
        drilldown_urls_by_account = {}
        drilldown_service = _get_drilldown_service()
        for account_id, dt_response in cached_result.data.items():
            drilldown_urls_by_account[account_id] = drilldown_service.generate_drilldown_urls(
                result_id, account_id, dt_response
            )

        return jsonify({
            'status': 'success',
            'result_id': result_id,
            'accounts_data': accounts_data,
            'drilldown_urls_by_account': drilldown_urls_by_account,
            'highlights': cached_result.statistical_metadata.get('highlights', {})
        })

    except Exception as e:
        logger.error(f'Error in show_summary_results_json: {e}',
                     extra={'context': {'result_id': result_id}})
        return jsonify({'error': str(e)}), 500


def show_detail_results_json(result_id: str) -> Union[Response, Tuple[Response, int]]:
    """Show all transaction details in a single DataTable view.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        JSON Response with all transaction details or error
    """
    try:
        # Get cached result
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if cached_result is None:
            return jsonify({'error': 'Result data not found or expired'}), 404

        # Prepare accounts data
        formatting_service = _get_data_formatting_service()
        accounts_data = formatting_service.prepare_accounts_for_template(
            cached_result.data,
            cached_result.statistical_metadata
        )

        # Generate drilldown URLs
        drilldown_urls_by_account = {}
        drilldown_service = _get_drilldown_service()
        for account_id, dt_response in cached_result.data.items():
            drilldown_urls_by_account[account_id] = drilldown_service.generate_drilldown_urls(
                result_id, account_id, dt_response
            )

        return jsonify({
            'status': 'success',
            'result_id': result_id,
            'accounts_data': accounts_data,
            'drilldown_urls_by_account': drilldown_urls_by_account,
            'highlights': cached_result.statistical_metadata.get('highlights', {})
        })

    except Exception as e:
        logger.error(f'Error in show_detail_results_json: {e}',
                     extra={'context': {'result_id': result_id}})
        return jsonify({'error': str(e)}), 500


def handle_recalculate_statistics_request(
    result_id: str,
    algorithms: List[str],
    direction: str
) -> Tuple[Dict[str, Any], int]:
    """Handle recalculate statistics request.

    Args:
        result_id: UUID of the cached processing result
        algorithms: List of algorithm names to apply (e.g., ['iqr', 'pareto'])
        direction: Direction for analysis ('rows' or 'columns')

    Returns:
        Tuple of (response_data, status_code)
    """
    try:
        # Get cached result
        cache_service = _get_cache_service()
        cached_result = cache_service.get(result_id)

        if cached_result is None:
            return {'error': 'Result data not found or expired'}, 404

        # Get statistical service
        statistical_service = _get_statistical_service()

        # Recalculate statistics with the specified algorithms and direction
        updated_metadata = statistical_service.compute_statistical_metadata(
            cached_result.data,
            algorithms=algorithms,
            direction=direction
        )

        # Convert highlights list to dict format: {row_id: [highlight_types]}
        # Merge types for same row_id (when multiple algorithms highlight the same cell)
        highlights_dict = {}
        for cell_highlight in updated_metadata.highlights:
            if cell_highlight.row_id in highlights_dict:
                highlights_dict[cell_highlight.row_id].extend(cell_highlight.highlight_types)
            else:
                highlights_dict[cell_highlight.row_id] = cell_highlight.highlight_types.copy()

        # Update cache with new statistical metadata
        cached_result.statistical_metadata = updated_metadata
        cache_service.set(result_id, cached_result)

        return {
            'status': 'success',
            'result_id': result_id,
            'highlights': highlights_dict,
            'algorithms': algorithms,
            'direction': direction
        }, 200

    except Exception as e:
        logger.error(f'Error recalculating statistics: {e}',
                     extra={'context': {'result_id': result_id, 'algorithms': algorithms,
                                       'direction': direction}})
        return {'error': str(e)}, 500


# Backwards compatibility aliases for existing tests
# These allow old code to continue working while pointing to the new JSON-based implementations
handle_entity_drilldown = handle_entity_drilldown_json
show_summary_results = show_summary_results_json
show_detail_results = show_detail_results_json
handle_category_month_transactions = handle_category_month_transactions_json

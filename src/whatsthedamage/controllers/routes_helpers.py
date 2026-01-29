"""Helper functions for web route handlers.

This module contains extracted helper functions to reduce complexity in routes.py.
Following the Single Responsibility Principle and DRY patterns.
"""
from flask import current_app, Response, flash, redirect, url_for, make_response, render_template
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService, AnalysisDirection
from whatsthedamage.config.dt_models import CachedProcessingResult, DataTablesResponse, StatisticalMetadata, AggregatedRow
from whatsthedamage.utils.flask_locale import get_default_language
from typing import Dict, Callable, Optional, cast, Tuple, List, Any


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_validation_service() -> ValidationService:
    """Get validation service from app extensions (dependency injection)."""
    return cast(ValidationService, current_app.extensions['validation_service'])


def _get_response_builder_service() -> ResponseBuilderService:
    """Get response builder service from app extensions (dependency injection)."""
    return cast(ResponseBuilderService, current_app.extensions['response_builder_service'])


def _get_file_upload_service() -> FileUploadService:
    """Get file upload service from app extensions (dependency injection)."""
    return cast(FileUploadService, current_app.extensions['file_upload_service'])


def _get_session_service() -> SessionService:
    """Get session service from app extensions (dependency injection)."""
    return cast(SessionService, current_app.extensions['session_service'])


def _get_data_formatting_service() -> DataFormattingService:
    """Get data formatting service from app extensions (dependency injection)."""
    return cast(DataFormattingService, current_app.extensions['data_formatting_service'])


def _get_cache_service() -> CacheService:
    """Get cache service from app extensions (dependency injection)."""
    return cast(CacheService, current_app.extensions['cache_service'])

def _get_statistical_analysis_service() -> StatisticalAnalysisService:
    """Get statistical analysis service from app extensions (dependency injection)."""
    return cast(StatisticalAnalysisService, current_app.extensions['statistical_analysis_service'])


def handle_file_uploads(form: UploadForm) -> Dict[str, str]:
    """Handle file uploads using FileUploadService.

    Args:
        form: The validated upload form containing file data

    Returns:
        Dict with 'csv_path' and 'config_path' (empty string if no config)

    Raises:
        ValueError: If file validation or save fails
    """
    upload_folder: str = current_app.config['UPLOAD_FOLDER']
    file_upload_service = _get_file_upload_service()

    try:
        # Extract config file or None
        config_file = form.config.data if form.config.data else None

        # Use FileUploadService to save files
        csv_path, config_path = file_upload_service.save_files(
            form.filename.data,
            upload_folder,
            config_file=config_file
        )

        return {
            'csv_path': csv_path,
            'config_path': config_path or ''
        }
    except FileUploadError as e:
        raise ValueError(str(e))


def get_cached_data_for_drilldown(
    result_id: str,
    account: str
) -> Tuple[Optional[DataTablesResponse], Optional[str]]:
    """Retrieve cached processing result for drill-down routes.

    Centralizes cache retrieval logic to eliminate duplication across
    the three drill-down route handlers.

    Args:
        result_id: UUID of the cached processing result
        account: Account identifier

    Returns:
        Tuple of (DataTablesResponse, error_message)
        If successful: (dt_response, None)
        If failed: (None, error_message)

    Example:
        >>> dt_response, error = get_cached_data_for_drilldown(result_id, account)
        >>> if error:
        >>>     flash(error, 'danger')
        >>>     return redirect(url_for(INDEX_ROUTE))
    """
    try:
        cache_service = _get_cache_service()
        cached = cache_service.get(result_id)

        if not cached:
            return None, 'Result not found or expired.'

        dt_response = cached.responses.get(account)
        if not dt_response:
            return None, f'Account "{account}" not found.'

        return dt_response, None
    except Exception:
        return None, 'Result not found or expired.'


def handle_drilldown_request(
    result_id: str,
    account: str,
    template: str,
    filter_fn: Callable[[AggregatedRow], bool],
    template_context: Dict[str, str],
    data_not_found_error: str = 'Data not found',
    index_route: str = 'main.index'
) -> Response:
    """Generic handler for drill-down requests.

    Eliminates code duplication across category, month, and cell drill-down routes
    by providing a single implementation with customizable filtering and rendering.

    Args:
        result_id: UUID of the cached processing result
        account: Account identifier
        template: Template name to render (e.g., 'category_all_months.html')
        filter_fn: Function to filter aggregated rows
        template_context: Additional context to pass to template (e.g., {'category': 'Grocery'})
        data_not_found_error: Error message for missing data
        index_route: Route to redirect on error

    Returns:
        Flask Response with rendered template or redirect

    Example:
        >>> # For category drill-down:
        >>> handle_drilldown_request(
        >>>     result_id, account,
        >>>     'category_all_months.html',
        >>>     lambda row: row.category == 'Grocery',
        >>>     {'category': 'Grocery', 'account': account}
        >>> )
    """
    dt_response, error = get_cached_data_for_drilldown(result_id, account)
    if error or not dt_response:
        flash(error or data_not_found_error, 'danger')
        return make_response(redirect(url_for(index_route)))

    filtered_data = [row for row in dt_response.data if filter_fn(row)]

    # Check if filtered data is empty and redirect with error
    if not filtered_data:
        flash(data_not_found_error, 'danger')
        return make_response(redirect(url_for(index_route)))

    # Format account ID using backend service for consistency
    formatting_service = _get_data_formatting_service()
    formatted_account = formatting_service.format_account_id(account)

    # Merge account into template context, including formatted version
    context = {
        'data': filtered_data,
        'account': account,
        'formatted_account': formatted_account,
        **template_context
    }
    return make_response(render_template(template, **context))


def process_details_and_build_response(
    form: UploadForm,
    csv_path: str,
    clear_upload_folder_fn: Callable[[], None],
    config_path: Optional[str]
) -> Response:
    """Process CSV for details view and build HTML response.

    Args:
        form: The upload form with processing parameters
        csv_path: Path to CSV file
        clear_upload_folder_fn: Function to clear upload folder after processing

    Returns:
        Flask response with rendered result.html
    """
    # Process using service layer
    session_service = SessionService()
    language = session_service.get_language() or get_default_language()
    result = _get_processing_service().process_with_details(
        csv_file_path=csv_path,
        config_file_path=config_path,
        start_date=form.start_date.data.strftime('%Y-%m-%d') if form.start_date.data else None,
        end_date=form.end_date.data.strftime('%Y-%m-%d') if form.end_date.data else None,
        ml_enabled=form.ml.data,
        category_filter=form.filter.data,
        language=language
    )

    # Extract Dict[str, DataTablesResponse] from result
    dt_responses_by_account = result['data']
    result_id = result['result_id']
    statistical_metadata = result.get('statistical_metadata') or StatisticalMetadata(highlights=[])

    # Cache result at controller layer (separation of concerns)
    # Business logic (ProcessingService) doesn't know about caching
    cache_service = _get_cache_service()
    cached_result = CachedProcessingResult(
        responses=dt_responses_by_account,
        metadata=statistical_metadata
    )
    cache_service.set(result_id, cached_result)

    # Prepare accounts data for template rendering
    formatting_service = _get_data_formatting_service()
    accounts_data = formatting_service.prepare_accounts_for_template(dt_responses_by_account)

    # Pass the prepared data to template for multi-account rendering
    clear_upload_folder_fn()
    return _get_response_builder_service().build_html_response(
        template='results.html',
        accounts_data=accounts_data,
        result_id=result_id,
        timing=result.get('timing')
    )

def handle_recalculate_statistics_request(
    result_id: str,
    algorithms: List[str],
    direction: str,
    use_default_directions: bool = False
) -> Tuple[Dict[str, Any], int]:
    """Handle recalculate statistics request with business logic.

    This helper function contains the business logic for recalculating statistical
    highlights, following the pattern of other helper functions in this module.

    Args:
        result_id: UUID of the cached processing result
        algorithms: List of algorithm names to use (e.g., ['iqr', 'pareto'])
        direction: Analysis direction ('columns' or 'rows')
        use_default_directions: If True, use each algorithm's default direction instead of the provided direction

    Returns:
        Tuple of (response_data, status_code)
        On success: (dict with highlights and metadata, 200)
        On error: (dict with error message, appropriate status code)

    Example:
        >>> response_data, status_code = handle_recalculate_statistics_request(
        >>>     result_id='abc123',
        >>>     algorithms=['iqr', 'pareto'],
        >>>     direction='columns'
        >>> )
    """
    try:
        # Get cached data
        cache_service = _get_cache_service()
        cached = cache_service.get(result_id)
        if not cached:
            return {'error': 'Result not found or expired'}, 404

        # Recalculate highlights using statistical analysis service
        stat_service = _get_statistical_analysis_service()
        new_metadata = stat_service.compute_statistical_metadata(
            cached.responses,
            algorithms=algorithms,
            direction=AnalysisDirection(direction),
            use_default_directions=use_default_directions
        )

        # Update cache with new metadata
        updated_cached = CachedProcessingResult(
            responses=cached.responses,
            metadata=new_metadata
        )
        cache_service.set(result_id, updated_cached)

        # Convert highlights to dictionary format for easier frontend processing
        highlights_dict = {}
        for highlight in new_metadata.highlights:
            key = f"{highlight.column}_{highlight.row}"
            highlights_dict[key] = highlight.highlight_type

        return {
            'status': 'success',
            'highlights': highlights_dict,
            'message': 'Statistics recalculated successfully'
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500

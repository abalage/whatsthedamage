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
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.id_mapping_service import IdMappingService
from whatsthedamage.services.drilldown_service import DrilldownService
from whatsthedamage.models.dt_models import ProcessingResponse, DataTablesResponse, AggregatedRow
from whatsthedamage.utils.flask_locale import get_default_language
from whatsthedamage.services.statistical_analysis_service import AnalysisDirection
from typing import Dict, Callable, Optional, cast, Tuple, List, Any, Union


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_validation_service() -> ValidationService:
    """Get validation service from app extensions (dependency injection)."""
    return cast(ValidationService, current_app.extensions['validation_service'])


def _get_response_builder_service() -> ResponseBuilderService:
    """Get response builder service from app extensions (dependency injection)."""
    return cast(ResponseBuilderService, current_app.extensions['response_builder_service'])

def _get_id_mapping_service() -> 'IdMappingService':
    """Get ID mapping service from app extensions (dependency injection)."""
    from whatsthedamage.services.id_mapping_service import IdMappingService
    return cast(IdMappingService, current_app.extensions['id_mapping_service'])


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

def _get_drilldown_service() -> DrilldownService:
    """Get drilldown service from app extensions (dependency injection)."""
    from whatsthedamage.services.drilldown_service import DrilldownService
    return cast(DrilldownService, current_app.extensions['drilldown_service'])


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

        dt_response = cached.data.get(account)
        if not dt_response:
            return None, f'Account "{account}" not found.'

        return dt_response, None
    except Exception:
        return None, 'Result not found or expired.'


def _process_statistical_metadata(
    cached_result: Optional[ProcessingResponse]
) -> Dict[str, List[str]]:
    """Process statistical metadata and return highlights.

    Extracts highlight information from cached processing result and converts
    it to the format expected by templates. CSS class mapping is now handled
    in the frontend presentation layer.

    Uses DataFormattingService._convert_metadata_to_highlights_dict() to
    eliminate code duplication and centralize the conversion logic.

    Args:
        cached_result: The cached ProcessingResponse object

    Returns:
        Dictionary mapping row_id to list of highlight types

    Example:
        >>> highlights = _process_statistical_metadata(cached)
        >>> # highlights: {'row1': ['outlier'], 'row2': ['pareto']}
    """
    if not cached_result or not cached_result.statistical_metadata:
        return {}

    # Use DataFormattingService to convert metadata to highlights dict
    formatting_service = _get_data_formatting_service()
    return formatting_service._convert_metadata_to_highlights_dict(
        cached_result.statistical_metadata
    )

def process_statistical_metadata_for_context(result_id: str) -> Dict[str, List[str]]:
    """Process statistical metadata for template context.

    Centralizes the pattern of retrieving cached data and processing statistical metadata
    that appears in multiple drilldown handlers. This eliminates code duplication and
    provides consistent error handling.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        Dictionary of highlights for template context, empty dict on error

    Example:
        >>> highlights_dict = process_statistical_metadata_for_context(result_id)
        >>> # highlights_dict: {'row1': ['outlier'], 'row2': ['pareto']}
    """
    try:
        cache_service = _get_cache_service()
        cached = cache_service.get(result_id)
        if cached and cached.statistical_metadata:
            formatting_service = _get_data_formatting_service()
            return formatting_service._convert_metadata_to_highlights_dict(
                cached.statistical_metadata
            )
    except Exception:
        pass
    return {}

def build_drilldown_context(
    filtered_data: List[Any],
    account_number: str,
    result_id: str,
    account_id: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    drilldown_urls: Dict[str, Any],
    template_specific_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build standardized context dictionary for drilldown templates.

    Centralizes the context building pattern that appears in multiple drilldown handlers.
    Provides consistent structure while allowing template-specific additions.

    Args:
        filtered_data: Filtered data rows for the template
        account_number: Original account number
        result_id: Processing result ID
        account_id: Secure account ID
        entity_type: Type of entity ('category' or 'month')
        entity_id: Secure entity ID
        entity_name: Original entity name
        drilldown_urls: Pre-generated drilldown URLs
        template_specific_context: Additional context specific to the template

    Returns:
        Complete context dictionary ready for template rendering

    Example:
        >>> context = build_drilldown_context(
        >>>     filtered_data, account_number, result_id, account_id,
        >>>     'category', category_id, category_name, drilldown_urls
        >>> )
    """
    # Format account ID
    formatting_service = _get_data_formatting_service()
    formatted_account = formatting_service.format_account_id(account_number)

    # Process statistical metadata
    highlights_dict = process_statistical_metadata_for_context(result_id)

    # Build base context
    context = {
        'data': filtered_data,
        'account': account_number,
        'formatted_account': formatted_account,
        'result_id': result_id,
        'account_id': account_id,
        f'{entity_type}_id': entity_id,
        entity_type: entity_name,
        'urls': drilldown_urls,
        'highlights': highlights_dict
    }

    # Add template-specific context if provided
    if template_specific_context:
        context.update(template_specific_context)

    return context

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
    # Get cached data
    dt_response, error = get_cached_data_for_drilldown(result_id, account)
    if error or not dt_response:
        flash(error or data_not_found_error, 'danger')
        return make_response(redirect(url_for(index_route)))

    # Filter data
    filtered_data: List[AggregatedRow] = [row for row in dt_response.data if filter_fn(row)]
    if not filtered_data:
        flash(data_not_found_error, 'danger')
        return make_response(redirect(url_for(index_route)))

    # Format account ID
    formatting_service = _get_data_formatting_service()
    formatted_account = formatting_service.format_account_id(account)

    # Pre-compute IDs for templates that need them (separation of concerns)
    # Create enhanced data objects with pre-computed IDs to avoid template business logic
    try:
        id_mapping_service = _get_id_mapping_service()

        # Add pre-computed IDs to each row for template use
        enhanced_data: List[Dict[str, Any]] = []
        for row in filtered_data:
            # Create a dictionary with all row data plus pre-computed IDs
            row_dict = row.model_dump()  # Convert Pydantic model to dict
            row_dict['month_id'] = id_mapping_service.get_month_id(str(row.date.timestamp))
            row_dict['category_id'] = id_mapping_service.get_category_id(result_id, row.category)
            enhanced_data.append(row_dict)
    except (KeyError, AttributeError):
        # Fallback for when id_mapping_service is not available (e.g., in tests)
        # This maintains backward compatibility
        enhanced_data = [row.model_dump() for row in filtered_data]

    # Process statistical metadata using centralized helper
    highlights_dict = process_statistical_metadata_for_context(result_id)

    # Build context and render
    context = {
        'data': enhanced_data,
        'account': account,
        'formatted_account': formatted_account,
        'result_id': result_id,
        'highlights': highlights_dict,
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
    dt_responses_by_account = result.data
    result_id = result.result_id
    statistical_metadata = result.statistical_metadata

    # Cache result at controller layer (separation of concerns)
    # Business logic (ProcessingService) doesn't know about caching
    cache_service = _get_cache_service()
    cache_service.set(result_id, result)

    # Prepare accounts data for template rendering
    formatting_service = _get_data_formatting_service()
    accounts_data = formatting_service.prepare_accounts_for_template(
        dt_responses_by_account,
        statistical_metadata
    )

    # Generate secure drill-down URLs for each account
    drilldown_urls_by_account = {}
    for account_id, dt_response in dt_responses_by_account.items():
        drilldown_urls_by_account[account_id] = generate_drilldown_urls(
            result_id, account_id, dt_response
        )

    # Pass the prepared data to template for multi-account rendering
    clear_upload_folder_fn()

    return make_response(
        render_template(
            'results.html',
            accounts_data=accounts_data,
            result_id=result_id,
            drilldown_urls_by_account=drilldown_urls_by_account
        )
    )

def generate_drilldown_urls(result_id: str, account: str, dt_response: DataTablesResponse) -> Dict[str, Any]:
    """Generate all drill-down URLs for a result using ID mapping.

    This function handles the business logic of mapping sensitive data to secure IDs
    and generating appropriate URLs for drill-down navigation. Templates should only
    receive pre-generated URLs, not perform ID mapping themselves.

    Args:
        result_id: Processing result ID
        account: Original account number
        dt_response: DataTablesResponse containing the data

    Returns:
        Dictionary containing pre-generated URLs for all drill-down levels
    """
    id_mapping_service = _get_id_mapping_service()

    # Map account to secure ID
    account_id = id_mapping_service.get_account_id(result_id, account)

    # Generate category URLs
    category_urls = {}
    for row in dt_response.data:
        category_name = row.category
        if category_name not in category_urls:
            category_id = id_mapping_service.get_category_id(result_id, category_name)
            category_urls[category_name] = {
                'category_url': f"/results/{result_id}/accounts/{account_id}/categories/{category_id}/months",
                'category_id': category_id
            }

    # Generate month URLs - ensure all months from the data are covered
    month_urls = {}
    for row in dt_response.data:
        month_ts = str(row.date.timestamp)
        if month_ts not in month_urls:
            month_id = id_mapping_service.get_month_id(month_ts)
            month_urls[month_ts] = {
                'month_url': f"/results/{result_id}/accounts/{account_id}/months/{month_id}/categories",
                'month_id': month_id
            }

    # Also generate URLs for any months that might be in the template but not in data
    # This ensures we don't get "dict has no element" errors
    for row in dt_response.data:
        month_ts = str(row.date.timestamp)
        if month_ts not in month_urls:
            month_id = id_mapping_service.get_month_id(month_ts)
            month_urls[month_ts] = {
                'month_url': f"/results/{result_id}/accounts/{account_id}/months/{month_id}/categories",
                'month_id': month_id
            }

    # Generate cell URLs using row_id as key (more robust than string concatenation)
    cell_urls = {}
    for row in dt_response.data:
        category_name = row.category
        month_ts = str(row.date.timestamp)
        category_id = id_mapping_service.get_category_id(result_id, category_name)
        month_id = id_mapping_service.get_month_id(month_ts)
        cell_urls[row.row_id] = {
            'cell_url': f"/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions",
            'category_id': category_id,
            'month_id': month_id
        }

    return {
        'account_id': account_id,
        'category_urls': category_urls,
        'month_urls': month_urls,
        'cell_urls': cell_urls
    }

def handle_entity_drilldown(
    result_id: str,
    account_id: str,
    entity_id: str,
    entity_type: str,
    template: str,
    data_not_found_error: str = 'Data not found',
    index_route: str = 'main.index'
) -> Union[Response, Any]:
    """Unified handler for category and month entity drilldown requests.

    Eliminates code duplication between show_month_categories() and show_category_months()
    by providing a single implementation with configurable entity type and filtering.

    Args:
        result_id: UUID of the cached processing result
        account_id: Secure account ID
        entity_id: Secure entity ID (category_id or month_id)
        entity_type: Type of entity ('category' or 'month')
        template: Template name to render
        filter_key: Key to use for filtering (e.g., 'category' or 'date.timestamp')
        data_not_found_error: Error message for missing data
        index_route: Route to redirect on error

    Returns:
        Flask Response with rendered template or redirect

    Example:
        >>> # For category drilldown:
        >>> handle_entity_drilldown(
        >>>     result_id, account_id, category_id,
        >>>     'category', 'category_months_list.html', 'category'
        >>> )
        >>>
        >>> # For month drilldown:
        >>> handle_entity_drilldown(
        >>>     result_id, account_id, month_id,
        >>>     'month', 'month_categories_list.html', 'date.timestamp'
        >>> )
    """
    # Use DrilldownService for all business logic
    drilldown_service = _get_drilldown_service()

    # Resolve IDs to original values using service
    resolution = drilldown_service.resolve_entity_ids(result_id, account_id, entity_id, entity_type)

    if resolution['error']:
        flash(resolution['error'], 'danger')
        return redirect(url_for(index_route))

    account_number = resolution['account_number']
    entity_name = resolution['entity_name']
    filter_value = resolution['filter_value']

    # Get cached data using service
    cache_result = drilldown_service.get_cached_data_for_account(result_id, account_number)

    if cache_result['error']:
        flash(cache_result['error'], 'danger')
        return redirect(url_for(index_route))

    dt_response = cache_result['dt_response']

    # Filter data for the specific entity using service
    filtered_data = drilldown_service.filter_data_for_entity(dt_response, entity_type, filter_value)

    if not filtered_data:
        flash(data_not_found_error, 'danger')
        return redirect(url_for(index_route))

    # Generate drilldown URLs using service
    drilldown_urls = drilldown_service.generate_drilldown_urls(result_id, account_number, dt_response)

    # Build context using service
    context = drilldown_service.build_drilldown_context(
        filtered_data=filtered_data,
        account_number=account_number,
        result_id=result_id,
        account_id=account_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        drilldown_urls=drilldown_urls
    )

    return make_response(render_template(template, **context))

def handle_recalculate_statistics_request(
    result_id: str,
    algorithms: List[str],
    direction: str,
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
        new_statistical_metadata = stat_service.compute_statistical_metadata(
            cached.data,
            algorithms=algorithms,
            direction=AnalysisDirection(direction)
        )

        # Update cache with new metadata
        updated_cached = ProcessingResponse(
            result_id=cached.result_id,
            data=cached.data,
            metadata=cached.metadata,
            statistical_metadata=new_statistical_metadata
        )
        cache_service.set(result_id, updated_cached)

        # Convert highlights to dictionary format for easier frontend processing
        formatting_service = _get_data_formatting_service()
        highlights_dict = formatting_service._convert_metadata_to_highlights_dict(
            new_statistical_metadata
        )

        return {
            'status': 'success',
            'highlights': highlights_dict,
            'message': 'Statistics recalculated successfully'
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500

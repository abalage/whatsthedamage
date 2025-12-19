"""Helper functions for web route handlers.

This module contains extracted helper functions to reduce complexity in routes.py.
Following the Single Responsibility Principle and DRY patterns.
"""
from flask import current_app, session, Response
from werkzeug.security import safe_join
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.utils.flask_locale import get_default_language
from whatsthedamage.config.dt_models import AggregatedRow
from typing import List, Dict, Optional, Union, DefaultDict, Callable, cast
from collections import defaultdict
from gettext import gettext as _
import os


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    return cast(ProcessingService, current_app.extensions['processing_service'])


def _get_validation_service() -> ValidationService:
    """Get validation service from app extensions (dependency injection)."""
    return cast(ValidationService, current_app.extensions['validation_service'])


def _get_response_builder_service() -> ResponseBuilderService:
    """Get response builder service from app extensions (dependency injection)."""
    return cast(ResponseBuilderService, current_app.extensions['response_builder_service'])


def _get_configuration_service() -> ConfigurationService:
    """Get configuration service from app extensions (dependency injection)."""
    return cast(ConfigurationService, current_app.extensions['configuration_service'])


def _get_file_upload_service() -> FileUploadService:
    """Get file upload service from app extensions (dependency injection)."""
    return cast(FileUploadService, current_app.extensions['file_upload_service'])


def _get_session_service() -> SessionService:
    """Get session service instance."""
    return SessionService()


def _get_data_formatting_service() -> DataFormattingService:
    """Get data formatting service instance."""
    return DataFormattingService()


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


def resolve_config_path(config_path: str, ml_enabled: bool) -> Optional[str]:
    """Resolve config file path, using default if not provided.

    Args:
        config_path: Path to uploaded config file (empty string if none)
        ml_enabled: Whether ML mode is enabled (doesn't require config)

    Returns:
        Resolved config path or None if ML mode or no config needed

    Raises:
        ValueError: If default config is required but not found
    """
    config_service = _get_configuration_service()
    default_config: Optional[str] = None

    # Get default config path from Flask config
    if not ml_enabled:
        default_config = safe_join(
            os.getcwd(), current_app.config['DEFAULT_WHATSTHEDAMAGE_CONFIG']  # type: ignore
        )

    return config_service.resolve_config_path(
        user_path=config_path if config_path else None,
        ml_enabled=ml_enabled,
        default_config_path=default_config
    )


def process_summary_and_build_response(
    form: UploadForm,
    csv_path: str,
    config_path: Optional[str],
    clear_upload_folder_fn: Callable[[], None]
) -> Response:
    """Process CSV for summary view and build HTML response.

    Args:
        form: The upload form with processing parameters
        csv_path: Path to CSV file
        config_path: Path to config file or None
        clear_upload_folder_fn: Function to clear upload folder after processing

    Returns:
        Flask response with rendered result.html
    """
    # Process using service layer
    result = _get_processing_service().process_summary(
        csv_file_path=csv_path,
        config_file_path=config_path,
        start_date=form.start_date.data.strftime('%Y-%m-%d') if form.start_date.data else None,
        end_date=form.end_date.data.strftime('%Y-%m-%d') if form.end_date.data else None,
        ml_enabled=form.ml.data,
        category_filter=form.filter.data,
        language=session.get('lang', get_default_language())
    )

    # Format result using DataFormattingService
    processor = result['processor']
    formatting_service = _get_data_formatting_service()

    # Use monthly breakdown data (not flattened) to preserve month columns
    monthly_data = result['monthly_data']
    html_result = formatting_service.format_as_html_table(
        monthly_data,
        currency=processor.processor.get_currency(),
        no_currency_format=form.no_currency_format.data,
        categories_header=_("Categories")
    )

    # Parse HTML table for rendering
    headers, processed_rows = formatting_service.prepare_table_for_rendering(html_result)

    # Store both original result and structured data using SessionService
    session_service = _get_session_service()
    session_service.store_result(html_result, {'headers': headers, 'rows': processed_rows})

    clear_upload_folder_fn()
    return _get_response_builder_service().build_html_response(
        template='result.html',
        headers=headers,
        rows=processed_rows
    )


def process_details_and_build_response(
    form: UploadForm,
    csv_path: str,
    clear_upload_folder_fn: Callable[[], None]
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
    result = _get_processing_service().process_with_details(
        csv_file_path=csv_path,
        config_file_path=None,  # v2 doesn't use config file
        start_date=form.start_date.data.strftime('%Y-%m-%d') if form.start_date.data else None,
        end_date=form.end_date.data.strftime('%Y-%m-%d') if form.end_date.data else None,
        ml_enabled=form.ml.data,
        category_filter=form.filter.data,
        language=session.get('lang', get_default_language())
    )

    # Extract DataTablesResponse from result
    dt_response = result['data']

    # Convert DataTablesResponse to headers and rows for result.html
    headers: List[str] = ['Categories']
    # Collect months and their timestamps
    month_tuples: set[tuple[str, int]] = set()
    for agg_row in dt_response.data:
        month_tuples.add((agg_row.month.display, agg_row.month.timestamp))
    # Sort by timestamp in descending order (most recent first)
    sorted_months: List[str] = [m[0] for m in sorted(month_tuples, key=lambda x: x[1], reverse=True)]
    headers += sorted_months

    # Build rows: each category, then each month
    cat_month_map: DefaultDict[str, Dict[str, AggregatedRow]] = defaultdict(dict)
    for agg_row in dt_response.data:
        cat_month_map[agg_row.category][agg_row.month.display] = agg_row

    rows: List[List[Dict[str, Union[str, float, None]]]] = []
    for cat, month_dict in cat_month_map.items():
        row: List[Dict[str, Union[str, float, None]]] = []
        row.append({'display': cat, 'order': None})
        for month in headers[1:]:
            agg_row_data = month_dict.get(month)
            if agg_row_data:
                details_str = '\n'.join([
                    f"{d.date.display}: {d.amount.display} - {d.merchant}" for d in agg_row_data.details
                ])
                row.append({
                    'display': agg_row_data.total.display,
                    'order': agg_row_data.total.raw,
                    'details': details_str
                })
            else:
                row.append({'display': '', 'order': 0, 'details': ''})
        rows.append(row)

    clear_upload_folder_fn()
    return _get_response_builder_service().build_html_response(
        template='result.html',
        headers=headers,
        rows=rows
    )

"""Helper functions for web route handlers.

This module contains extracted helper functions to reduce complexity in routes.py.
Following the Single Responsibility Principle and DRY patterns.
"""
from flask import current_app, Response
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.validation_service import ValidationService
from whatsthedamage.services.response_builder_service import ResponseBuilderService
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.services.cache_service import CacheService
from whatsthedamage.config.dt_models import CachedProcessingResult, DataTablesResponse, StatisticalMetadata, AggregatedRow
from whatsthedamage.utils.flask_locale import get_default_language
from typing import Dict, Callable, Optional, cast, Tuple


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

    # Prepare accounts data for template rendering
    formatting_service = _get_data_formatting_service()
    accounts_data = formatting_service.prepare_accounts_for_template(dt_responses_by_account)

    # Pass the prepared data to template for multi-account rendering
    clear_upload_folder_fn()
    return _get_response_builder_service().build_html_response(
        template='v2_results.html',
        accounts_data=accounts_data,
        result_id=result_id,
        timing=result.get('timing')
    )


"""Helper functions for web route handlers.

This module contains extracted helper functions to reduce complexity in routes.py.
Following the Single Responsibility Principle and DRY patterns.
"""
from flask import current_app, session, make_response, render_template, Response
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.models.data_frame_formatter import DataFrameFormatter
from whatsthedamage.utils.html_parser import TableParser
from whatsthedamage.utils.flask_locale import get_default_language
from whatsthedamage.config.dt_models import AggregatedRow
from typing import List, Dict, Optional, Union, DefaultDict, Callable
from collections import defaultdict
from gettext import gettext as _
import os
import magic
import re


def _get_processing_service() -> ProcessingService:
    """Get processing service from app extensions (dependency injection)."""
    from typing import cast
    return cast(ProcessingService, current_app.extensions['processing_service'])


def allowed_file(file_path: str) -> bool:
    """Check if file is allowed based on MIME type.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file is CSV or YAML, False otherwise

    Note:
        Uses libmagic for content-based MIME type detection. Accepts text/plain
        for CSV files as libmagic may return text/plain instead of text/csv when:
        - File has certain character encodings (Windows-1252, ISO-8859-1)
        - File contains BOM (Byte Order Mark)
        - File buffer not fully synced to disk yet
        Validated externally: mimetype command confirms these are valid CSV files.
    """
    mime = magic.Magic(mime=True)
    file_type: str = mime.from_file(file_path)
    return file_type in {'text/csv', 'text/plain', 'application/x-yaml'}


def handle_file_uploads(form: UploadForm) -> Dict[str, str]:
    """Handle file uploads and return file paths.

    Args:
        form: The validated upload form containing file data

    Returns:
        Dict with 'csv_path' and 'config_path' (empty string if no config)

    Raises:
        ValueError: If file validation fails
    """
    upload_folder: str = current_app.config['UPLOAD_FOLDER']

    # Save CSV file
    filename: str = secure_filename(form.filename.data.filename)
    csv_path: str = safe_join(upload_folder, filename)  # type: ignore
    form.filename.data.save(csv_path)

    # Save config file if provided
    config_path: str = ''
    if form.config.data:
        config_filename: str = secure_filename(form.config.data.filename)
        config_path = safe_join(upload_folder, config_filename)  # type: ignore
        form.config.data.save(config_path)

    # Validate file types
    if not allowed_file(csv_path) or (config_path and not allowed_file(config_path)):
        raise ValueError('Invalid file type. Only CSV and YAML files are allowed.')

    return {'csv_path': csv_path, 'config_path': config_path}


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
    if config_path:
        return config_path

    if ml_enabled:
        return None

    # Use default config
    default_config: str = safe_join(
        os.getcwd(), current_app.config['DEFAULT_WHATSTHEDAMAGE_CONFIG']  # type: ignore
    )

    if default_config and not os.path.exists(default_config):
        raise ValueError('Default config file not found. Please upload one.')

    return default_config


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

    # Format result using DataFrameFormatter
    processor = result['processor']
    formatter = DataFrameFormatter()
    formatter.set_no_currency_format(form.no_currency_format.data)

    # Wrap flattened data in "Total" for formatter
    monthly_data = {"Total": result['data']}
    df = formatter.format_dataframe(monthly_data, currency=processor.processor.get_currency())

    # Convert to HTML
    html_result = df.to_html(border=0)
    html_result = html_result.replace('<th></th>', f'<th>{_("Categories")}</th>', 1)

    # Parse HTML table for rendering
    parser: TableParser = TableParser()
    headers, rows = parser.parse_table(html_result)

    # Process rows to extract numeric values for data-order attributes
    processed_rows: List[List[Dict[str, Union[str, float, None]]]] = []
    for row in rows:
        processed_row: List[Dict[str, Union[str, float, None]]] = []
        for i, cell in enumerate(row):
            if i == 0:  # First column (Categories) - no numeric sorting needed
                processed_row.append({'display': cell, 'order': None})
            else:
                # Extract numeric value from currency string for sorting
                match = re.match(r'^(-?\d+(?:\.\d+)?)', str(cell))
                numeric_value: float = float(match.group(1)) if match else 0
                processed_row.append({'display': cell, 'order': numeric_value})
        processed_rows.append(processed_row)

    # Store both original result and structured data
    session['result'] = html_result
    session['table_data'] = {'headers': headers, 'rows': processed_rows}

    clear_upload_folder_fn()
    return make_response(render_template('result.html', headers=headers, rows=processed_rows))


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
    return make_response(render_template('result.html', headers=headers, rows=rows))

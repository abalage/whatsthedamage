from datetime import datetime
from flask import (
    Blueprint, request, make_response, render_template, redirect, url_for,
    flash, current_app, Response, jsonify
)
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.controllers.routes_helpers import (
    handle_file_uploads,
    process_details_and_build_response,
    handle_entity_drilldown,
    show_detail_results,
    show_summary_results
)
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from typing import Optional, Union, Any
import os
import shutil
from whatsthedamage.utils.flask_locale import get_locale, get_languages
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

bp: Blueprint = Blueprint('main', __name__)
INDEX_ROUTE = 'main.index'
DATA_NOT_FOUND_ERROR = 'Data not found'


def _get_session_service() -> SessionService:
    """Get session service from app extensions (dependency injection)."""
    from typing import cast
    return cast(SessionService, current_app.extensions['session_service'])


def _get_configuration_service() -> ConfigurationService:
    """Get ConfigurationService from app extensions (dependency injection)."""
    from typing import cast
    from flask import current_app
    return cast(ConfigurationService, current_app.extensions['configuration_service'])


def _get_formatting_service() -> DataFormattingService:
    """Get DataFormattingService from app extensions (dependency injection)."""
    from typing import cast
    from flask import current_app
    return cast(DataFormattingService, current_app.extensions['data_formatting_service'])


def clear_upload_folder() -> None:
    upload_folder: str = current_app.config['UPLOAD_FOLDER']
    for filename in os.listdir(upload_folder):
        file_path: str = os.path.join(upload_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f'Failed to delete {file_path}. Reason: {e}',
                        extra={'context': {'file_path': file_path, 'error': str(e)}})


def get_lang_template(template_name: str) -> str:
    lang: str = get_locale()
    return f"{lang}/{template_name}"



@bp.route('/')
def index() -> Response:
    form: UploadForm = UploadForm()
    session_service = _get_session_service()
    if session_service.has_form_data():
        form_data_obj = session_service.retrieve_form_data()
        if form_data_obj:
            form.filename.data = form_data_obj.filename
            form.config.data = form_data_obj.config

            for date_field in ['start_date', 'end_date']:
                date_value: Optional[str] = getattr(form_data_obj, date_field)
                if date_value:
                    getattr(form, date_field).data = datetime.strptime(date_value, '%Y-%m-%d')

            form.verbose.data = form_data_obj.verbose
            form.filter.data = form_data_obj.filter
    return make_response(render_template('index.html', form=form))


@bp.route('/process', methods=['POST'])
def process() -> Response:
    """Process CSV and return detailed DataTables HTML page for web UI."""
    form: UploadForm = UploadForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
                logger.error(f"Error in {getattr(form, field).label.text}: {error}")
        return make_response(redirect(url_for(INDEX_ROUTE)))

    try:
        # Handle file uploads
        files = handle_file_uploads(form)

        # Resolve config path using ConfigurationService
        config_service = _get_configuration_service()
        config_path = config_service.resolve_config_path(
            user_path=files['config_path'] if files['config_path'] else None,
            ml_enabled=form.ml.data,
            default_config_path=None  # No default config file, will use built-in defaults
        )

        # Store form data in session
        session_service = _get_session_service()
        session_service.store_form_data(request.form.to_dict())

        # Process and build response
        return process_details_and_build_response(form, files['csv_path'], clear_upload_folder, config_path )

    except ValueError as e:
        flash(str(e), 'danger')
        logger.error(str(e))
        return make_response(redirect(url_for(INDEX_ROUTE)))
    except Exception as e:
        flash(f'Error processing CSV: {e}')
        logger.error(f'Error processing CSV: {e}')
        return make_response(redirect(url_for(INDEX_ROUTE)))


@bp.route('/clear', methods=['POST'])
def clear() -> Response:
    session_service = _get_session_service()
    session_service.clear_session()
    flash('Form data cleared.', 'success')
    return make_response(redirect(url_for(INDEX_ROUTE)))


@bp.route('/legal')
def legal() -> Response:
    return make_response(render_template(get_lang_template('legal.html')))


@bp.route('/privacy')
def privacy() -> Response:
    return make_response(render_template(get_lang_template('privacy.html')))


@bp.route('/about')
def about() -> Response:
    return make_response(render_template(get_lang_template('about.html')))


@bp.route('/set_language/<lang_code>')
def set_language(lang_code: str) -> Response:
    if lang_code in get_languages():
        session_service = _get_session_service()
        session_service.set_language(lang_code)
        flash(f"Language changed to {lang_code.upper()}.", "success")
    else:
        flash("Selected language is not supported.", "danger")
    return make_response(redirect(request.referrer or url_for(INDEX_ROUTE)))


@bp.route('/recalculate-statistics', methods=['POST'])
def recalculate_statistics() -> Union[Response, tuple[Response, int]]:
    """Recalculate statistical highlights with custom algorithm and direction settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        result_id = data.get('result_id')
        algorithms = data.get('algorithms', [])
        direction = data.get('direction', 'columns')

        if not result_id:
            return jsonify({'error': 'result_id is required'}), 400

        if not isinstance(algorithms, list):
            return jsonify({'error': 'algorithms must be a list'}), 400

        if direction not in ['columns', 'rows']:
            return jsonify({'error': 'direction must be either "columns" or "rows"'}), 400

        # Use helper function to handle the business logic
        from whatsthedamage.controllers.routes_helpers import handle_recalculate_statistics_request
        response_data, status_code = handle_recalculate_statistics_request(
            result_id=result_id,
            algorithms=algorithms,
            direction=direction
        )

        return jsonify(response_data), status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/favicon.ico')
def favicon() -> Response:
    """Serve favicon.ico to prevent 404 errors in browser console."""
    return current_app.send_static_file('favicon.ico')

@bp.route('/health')
def health() -> Response:
    try:
        # Simple check to see if the upload folder is writable
        test_file_path: str = os.path.join(current_app.config['UPLOAD_FOLDER'], 'health_check.tmp')
        with open(test_file_path, 'w') as f:
            f.write('health check')
        os.remove(test_file_path)

        return make_response({"status": "healthy"}, 200)

    except Exception as e:
        return make_response(
            {"status": "unhealthy", "reason": f"Unexpected error: {e}"},
            503
        )

# New secure routes with ID mapping
@bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months')
def show_category_months(result_id: str, account_id: str, category_id: str) -> Union[Response, Any]:
    """Show category details across all months using secure IDs."""

    return handle_entity_drilldown(
        result_id=result_id,
        account_id=account_id,
        entity_id=category_id,
        entity_type='category',
        template='category_months_list.html',
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )

@bp.route('/results/<result_id>/accounts/<account_id>/months/<month_id>/categories')
def show_month_categories(result_id: str, account_id: str, month_id: str) -> Union[Response, Any]:
    """Show month details across all categories using secure IDs."""

    return handle_entity_drilldown(
        result_id=result_id,
        account_id=account_id,
        entity_id=month_id,
        entity_type='month',
        template='month_categories_list.html',
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )

@bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions')
def show_category_month_transactions(result_id: str, account_id: str, category_id: str, month_id: str) -> Response:
    """Show specific category and month transaction details using secure IDs."""
    from whatsthedamage.controllers.routes_helpers import handle_category_month_transactions

    return handle_category_month_transactions(
        result_id=result_id,
        account_id=account_id,
        category_id=category_id,
        month_id=month_id,
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )


@bp.route('/results/<result_id>')
def show_results(result_id: str) -> Union[Response, Any]:
    """Show summary results view.

    Route handler for displaying processing results in summary view format.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        Flask Response with rendered results.html template or redirect
    """
    return show_summary_results(result_id)


@bp.route('/results/<result_id>/details')
def show_details(result_id: str) -> Union[Response, Any]:
    """Show all transaction details in a single DataTable view.

    Route handler for displaying all DetailRow objects from a processing result
    in a searchable DataTable format.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        Flask Response with rendered detail_results.html template or redirect
    """
    return show_detail_results(result_id)

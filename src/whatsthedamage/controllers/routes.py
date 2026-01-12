from datetime import datetime
from flask import (
    Blueprint, request, make_response, render_template, redirect, url_for,
    flash, current_app, Response
)
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.controllers.routes_helpers import (
    handle_file_uploads,
    process_details_and_build_response
)
from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from typing import Optional
import os
import shutil
from whatsthedamage.utils.flask_locale import get_locale, get_languages

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
            print(f'Failed to delete {file_path}. Reason: {e}')


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


@bp.route('/process/v2', methods=['POST'])
def process_v2() -> Response:
    """Process CSV and return detailed DataTables HTML page for web UI."""
    form: UploadForm = UploadForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
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
        return make_response(redirect(url_for(INDEX_ROUTE)))
    except Exception as e:
        flash(f'Error processing CSV: {e}')
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


@bp.route('/details/<result_id>/<account>/<category>')
def details_category_all_months(result_id: str, account: str, category: str) -> Response:
    """Show category details across all months."""
    from whatsthedamage.controllers.routes_helpers import handle_drilldown_request

    return handle_drilldown_request(
        result_id=result_id,
        account=account,
        template='category_all_months.html',
        filter_fn=lambda row: row.category == category,
        template_context={'category': category},
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )


@bp.route('/details/<result_id>/<account>/month/<month_ts>')
def details_month_all_categories(result_id: str, account: str, month_ts: str) -> Response:
    """Show month details across all categories."""
    from whatsthedamage.controllers.routes_helpers import handle_drilldown_request

    return handle_drilldown_request(
        result_id=result_id,
        account=account,
        template='month_all_categories.html',
        filter_fn=lambda row: str(row.month.timestamp) == month_ts or str(row.date.timestamp) == month_ts,
        template_context={'month_ts': month_ts},
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )


@bp.route('/details/<result_id>/<account>/<category>/<month_ts>')
def details_category_month(result_id: str, account: str, category: str, month_ts: str) -> Response:
    """Show specific category and month details."""
    from whatsthedamage.controllers.routes_helpers import handle_drilldown_request

    return handle_drilldown_request(
        result_id=result_id,
        account=account,
        template='category_month_detail.html',
        filter_fn=lambda row: (
            row.category == category and
            (str(row.month.timestamp) == month_ts or str(row.date.timestamp) == month_ts)
        ),
        template_context={'category': category, 'month_ts': month_ts},
        data_not_found_error=DATA_NOT_FOUND_ERROR,
        index_route=INDEX_ROUTE
    )


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

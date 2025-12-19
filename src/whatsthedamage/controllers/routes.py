from datetime import datetime
from flask import (
    Blueprint, request, make_response, render_template, redirect, url_for,
    flash, current_app, Response
)
from whatsthedamage.view.forms import UploadForm
from whatsthedamage.controllers.routes_helpers import (
    handle_file_uploads,
    resolve_config_path,
    process_summary_and_build_response,
    process_details_and_build_response
)
from whatsthedamage.services.session_service import SessionService
from typing import Optional
import os
import shutil
import pandas as pd
from io import StringIO
from whatsthedamage.utils.flask_locale import get_locale, get_languages

bp: Blueprint = Blueprint('main', __name__)
INDEX_ROUTE = 'main.index'


def _get_session_service() -> SessionService:
    """Get SessionService instance."""
    return SessionService()


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
            form.no_currency_format.data = form_data_obj.no_currency_format
            form.filter.data = form_data_obj.filter
    return make_response(render_template('index.html', form=form))


@bp.route('/process', methods=['POST'])
def process_v1() -> Response:
    """Process CSV and return summary HTML page for web UI."""
    form: UploadForm = UploadForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
        return make_response(redirect(url_for(INDEX_ROUTE)))

    try:
        # Handle file uploads
        files = handle_file_uploads(form)

        # Resolve config path (use default if needed)
        config_path = resolve_config_path(files['config_path'], form.ml.data)

        # Store form data in session
        session_service = _get_session_service()
        session_service.store_form_data(request.form.to_dict())

        # Process and build response
        return process_summary_and_build_response(form, files['csv_path'], config_path, clear_upload_folder)

    except ValueError as e:
        flash(str(e), 'danger')
        return make_response(redirect(url_for(INDEX_ROUTE)))
    except Exception as e:
        flash(f'Error processing CSV: {e}')
        return make_response(redirect(url_for(INDEX_ROUTE)))

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

        # Store form data in session
        session_service = _get_session_service()
        session_service.store_form_data(request.form.to_dict())

        # Process and build response
        return process_details_and_build_response(form, files['csv_path'], clear_upload_folder)

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


@bp.route('/download', methods=['GET'])
def download() -> Response:
    session_service = _get_session_service()
    result_data = session_service.retrieve_result()
    if not result_data:
        flash('No result available for download.', 'danger')
        return make_response(redirect(url_for(INDEX_ROUTE)))

    result, _ = result_data

    # Convert the HTML table to a DataFrame
    df: pd.DataFrame = pd.read_html(StringIO(result))[0]

    # Convert the DataFrame to CSV
    csv_buffer: StringIO = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data: str = csv_buffer.getvalue()

    # Create a response with the CSV data
    response: Response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=result.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


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

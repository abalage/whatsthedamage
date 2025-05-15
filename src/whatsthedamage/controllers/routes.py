from datetime import datetime
from flask import (
    Blueprint, request, make_response, render_template, redirect, url_for,
    session, flash, current_app, Response
)
from whatsthedamage.view.forms import UploadForm
from typing import Optional
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from whatsthedamage.config.config import AppArgs
from whatsthedamage.controllers.whatsthedamage import main as process_csv
import os
import shutil
import pandas as pd
from io import StringIO
import magic

bp: Blueprint = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'csv', 'yml', 'yaml'}


def allowed_file(file_path: str) -> bool:
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type in {'text/csv', 'text/plain', 'application/x-yaml'}


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


@bp.route('/')
def index() -> Response:
    form: UploadForm = UploadForm()
    if 'form_data' in session:
        form_data: dict[str, str] = session['form_data']
        form.filename.data = form_data.get('filename')
        form.config.data = form_data.get('config')

        for date_field in ['start_date', 'end_date']:
            date_value: Optional[str] = form_data.get(date_field)
            if date_value:
                getattr(form, date_field).data = datetime.strptime(date_value, '%Y-%m-%d')

        form.verbose.data = bool(form_data.get('verbose', False))
        form.no_currency_format.data = bool(form_data.get('no_currency_format', False))
        form.filter.data = form_data.get('filter')
    return make_response(render_template('index.html', form=form))


@bp.route('/process', methods=['POST'])
def process() -> Response:
    form: UploadForm = UploadForm()
    if form.validate_on_submit():
        upload_folder: str = current_app.config['UPLOAD_FOLDER']
        filename: str = secure_filename(form.filename.data.filename)
        filename_path: str = safe_join(upload_folder, filename)  # type: ignore
        form.filename.data.save(filename_path)

        config_path: str = ''
        if form.config.data:
            config: str = secure_filename(form.config.data.filename)
            config_path = safe_join(upload_folder, config)  # type: ignore
            form.config.data.save(config_path)
        else:
            config_path = safe_join(os.getcwd(), current_app.config['DEFAULT_WHATSTHEDAMAGE_CONFIG'])  # type: ignore
            if config_path and not os.path.exists(config_path):
                flash('Default config file not found. Please upload one.', 'danger')
                return make_response(redirect(url_for('main.index')))

        if not allowed_file(filename_path) or (config_path and not allowed_file(config_path)):
            flash('Invalid file type. Only CSV and YAML files are allowed.', 'danger')
            return make_response(redirect(url_for('main.index')))

        args: AppArgs = AppArgs(
            filename=filename_path,
            start_date=form.start_date.data.strftime('%Y-%m-%d') if form.start_date.data else None,
            end_date=form.end_date.data.strftime('%Y-%m-%d') if form.end_date.data else None,
            verbose=form.verbose.data,
            config=config_path,
            category='category',
            no_currency_format=form.no_currency_format.data,
            nowrap=False,
            output='html',
            output_format='html',
            filter=form.filter.data,
            lang="en",
        )

        # Store form data in session
        session['form_data'] = request.form.to_dict()

        try:
            result: str = process_csv(args)
        except Exception as e:
            flash(f'Error processing CSV: {e}')
            return make_response(redirect(url_for('main.index')))

        # Hack to make the table look better with Bootstrap as Pandas' CSS support is limited
        # Also this leaves the choice of output format to the frontend
        result = result.replace('<table class="dataframe">', '<table class="table table-bordered table-striped">')
        result = result.replace('<tbody>', '<tbody class="table-group-divider">')
        result = result.replace('<thead>', '<thead class="table-success">')

        # Store the result in the session
        session['result'] = result

        # Clear the upload folder after processing
        clear_upload_folder()

        return make_response(render_template('result.html', table=result))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
        return make_response(redirect(url_for('main.index')))


@bp.route('/clear', methods=['POST'])
def clear() -> Response:
    session.pop('form_data', None)
    flash('Form data cleared.', 'success')
    return make_response(redirect(url_for('main.index')))


@bp.route('/download', methods=['GET'])
def download() -> Response:
    result = session.get('result')
    if not result:
        flash('No result available for download.', 'danger')
        return make_response(redirect(url_for('main.index')))

    # Convert the HTML table to a DataFrame
    df = pd.read_html(StringIO(result))[0]

    # Convert the DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    # Create a response with the CSV data
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=result.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


@bp.route('/legal')
def legal() -> Response:
    return make_response(render_template('legal.html'))


@bp.route('/privacy')
def privacy() -> Response:
    return make_response(render_template('privacy.html'))


@bp.route('/about')
def about() -> Response:
    return make_response(render_template('about.html'))

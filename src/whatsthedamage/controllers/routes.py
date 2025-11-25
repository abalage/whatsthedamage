from datetime import datetime
from flask import (
    Blueprint, request, make_response, render_template, redirect, url_for,
    session, flash, current_app, Response
)
from whatsthedamage.view.forms import UploadForm
from typing import Optional, Dict, List, Union
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from whatsthedamage.config.config import AppArgs
from whatsthedamage.controllers.whatsthedamage import main as process_csv
import os
import shutil
import pandas as pd
from io import StringIO
import magic
from whatsthedamage.utils.flask_locale import get_locale, get_languages, get_default_language
from whatsthedamage.utils.html_parser import TableParser
from typing import DefaultDict
from whatsthedamage.config.dt_models import AggregatedRow
from collections import defaultdict

bp: Blueprint = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'csv', 'yml', 'yaml'}


def allowed_file(file_path: str) -> bool:
    mime = magic.Magic(mime=True)
    file_type: str = mime.from_file(file_path)
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


def get_lang_template(template_name: str) -> str:
    lang: str = get_locale()
    return f"{lang}/{template_name}"


@bp.route('/')
def index() -> Response:
    form: UploadForm = UploadForm()
    if 'form_data' in session:
        form_data: Dict[str, str] = session['form_data']
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
            if not form.ml.data:
                config_path = safe_join(
                    os.getcwd(), current_app.config['DEFAULT_WHATSTHEDAMAGE_CONFIG']   # type: ignore
                )
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
            lang=session.get('lang', get_default_language()),
            training_data=False,
            ml=form.ml.data,
        )

        # Store form data in session
        session['form_data'] = request.form.to_dict()

        try:
            result: str = process_csv(args)
        except Exception as e:
            flash(f'Error processing CSV: {e}')
            return make_response(redirect(url_for('main.index')))

        # Parse HTML table using native Python parser
        parser: TableParser = TableParser()
        headers: List[str]
        rows: List[List[str]]
        headers, rows = parser.parse_table(result)

        # Process rows to extract numeric values for data-order attributes
        import re
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
        session['result'] = result
        session['table_data'] = {'headers': headers, 'rows': processed_rows}

        # Clear the upload folder after processing
        clear_upload_folder()

        return make_response(render_template('result.html', headers=headers, rows=processed_rows))
    else:
        # Handle validation failure
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
        return make_response(redirect(url_for('main.index')))

@bp.route('/process/v2', methods=['POST'])
def process_v2() -> Response:
    form: UploadForm = UploadForm()
    if form.validate_on_submit():
        upload_folder: str = current_app.config['UPLOAD_FOLDER']
        filename: str = secure_filename(form.filename.data.filename)
        filename_path: str = safe_join(upload_folder, filename)  # type: ignore
        form.filename.data.save(filename_path)


        if not allowed_file(filename_path):
            flash('Invalid file type. Only CSV and YAML files are allowed.', 'danger')
            return make_response(redirect(url_for('main.index')))

        args: AppArgs = AppArgs(
            filename=filename_path,
            start_date=form.start_date.data.strftime('%Y-%m-%d') if form.start_date.data else None,
            end_date=form.end_date.data.strftime('%Y-%m-%d') if form.end_date.data else None,
            verbose=form.verbose.data,
            config='',
            category='category',
            no_currency_format=form.no_currency_format.data,
            nowrap=False,
            output='html',
            output_format='html',
            filter=form.filter.data,
            lang=session.get('lang', get_default_language()),
            training_data=False,
            ml=form.ml.data,
        )

        # Store form data in session
        session['form_data'] = request.form.to_dict()

        try:
            from whatsthedamage.config.config import AppContext, load_config
            from whatsthedamage.models.csv_processor import CSVProcessor
            config_obj = load_config(None)
            context_obj = AppContext(config_obj, args)
            processor = CSVProcessor(context_obj)
            dt_response = processor.process_v2()

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

            clear_upload_folder()
            return make_response(render_template('result.html', headers=headers, rows=rows))
        except Exception as e:
            flash(f'Error processing CSV: {e}')
            return make_response(redirect(url_for('main.index')))
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
    result: Optional[str] = session.get('result')
    if not result:
        flash('No result available for download.', 'danger')
        return make_response(redirect(url_for('main.index')))

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
        session['lang'] = lang_code
        flash(f"Language changed to {lang_code.upper()}.", "success")
    else:
        flash("Selected language is not supported.", "danger")
    return make_response(redirect(request.referrer or url_for('main.index')))


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

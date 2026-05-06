from flask import (
    Blueprint, request, make_response, redirect, url_for, flash,
    current_app, Response, jsonify
)
# from whatsthedamage.view.forms import UploadForm  # Deprecated - API-only backend

from whatsthedamage.services.session_service import SessionService
from whatsthedamage.services.configuration_service import ConfigurationService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.controllers.routes_helpers import (
    handle_entity_drilldown_json,
    handle_category_month_transactions_json,
    show_summary_results_json,
    show_detail_results_json,
    handle_recalculate_statistics_request
)
from typing import Tuple, Union, Any
import os
import shutil
from whatsthedamage.utils.flask_locale import get_languages
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


# def get_lang_template(template_name: str) -> str:  # Removed - no templates
#     lang: str = get_locale()
#     return f"{lang}/{template_name}"



@bp.route('/')
def index() -> Response:
    """
    API-only backend information.
    The web interface has been moved to a separate frontend application.
    """
    return make_response(
        jsonify({
            'status': 'api-only',
            'message': 'This is an API-only backend. The web interface has been moved to a separate frontend application.',
            'frontend': 'See frontend/README.md for the decoupled frontend application',
            'api_documentation': url_for('api_docs.v2_openapi_spec', _external=True),
            'available_endpoints': {
                'api_v2': {
                    'process': url_for('api_v2.process_transactions', _external=True),
                    'recalculate_statistics': url_for('api_v2.recalculate_statistics', _external=True)
                }
            }
        }),
        200
    )


@bp.route('/process', methods=['POST'])
def process() -> Response:
    """
    Process CSV via form submission - DEPRECATED
    This endpoint is deprecated. Please use the API v2 endpoints instead.
    """
    return make_response(
        jsonify({
            'error': 'This endpoint is deprecated. Please use /api/v2/process instead.',
            'status': 'deprecated',
            'api_endpoint': url_for('api_v2.process_transactions', _external=True)
        }),
        410  # Gone
    )


@bp.route('/clear', methods=['POST'])
def clear() -> Response:
    """
    Clear session - DEPRECATED
    This endpoint is deprecated. The frontend now manages its own state.
    """
    return make_response(
        jsonify({
            'error': 'This endpoint is deprecated. The frontend manages its own state.',
            'status': 'deprecated'
        }),
        410  # Gone
    )


@bp.route('/legal')
def legal() -> Response:
    """Legal information - now available in frontend only."""
    return make_response(
        jsonify({
            'error': 'Legal page moved to frontend. This is an API-only backend.',
            'status': 'deprecated',
            'frontend': 'See frontend/README.md for the new frontend application'
        }),
        410  # Gone
    )


@bp.route('/privacy')
def privacy() -> Response:
    """Privacy information - now available in frontend only."""
    return make_response(
        jsonify({
            'error': 'Privacy page moved to frontend. This is an API-only backend.',
            'status': 'deprecated',
            'frontend': 'See frontend/README.md for the new frontend application'
        }),
        410  # Gone
    )


@bp.route('/about')
def about() -> Response:
    """About information - now available in frontend only."""
    return make_response(
        jsonify({
            'error': 'About page moved to frontend. This is an API-only backend.',
            'status': 'deprecated',
            'frontend': 'See frontend/README.md for the new frontend application'
        }),
        410  # Gone
    )


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

# New secure routes with ID mapping - Now return JSON for Vue frontend
@bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months')
def show_category_months(result_id: str, account_id: str, category_id: str) -> Union[Response, Any]:
    """Show category details across all months using secure IDs.

    Returns JSON data for Vue frontend instead of rendering templates.
    """
    return handle_entity_drilldown_json(
        result_id=result_id,
        account_id=account_id,
        entity_id=category_id,
        entity_type='category',
        data_not_found_error=DATA_NOT_FOUND_ERROR
    )

@bp.route('/results/<result_id>/accounts/<account_id>/months/<month_id>/categories')
def show_month_categories(result_id: str, account_id: str, month_id: str) -> Union[Response, Any]:
    """Show month details across all categories using secure IDs.

    Returns JSON data for Vue frontend instead of rendering templates.
    """
    return handle_entity_drilldown_json(
        result_id=result_id,
        account_id=account_id,
        entity_id=month_id,
        entity_type='month',
        data_not_found_error=DATA_NOT_FOUND_ERROR
    )

@bp.route('/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions')
def show_category_month_transactions(result_id: str, account_id: str, category_id: str, month_id: str) -> Union[Response, Tuple[Response, int]]:
    """Show specific category and month transaction details using secure IDs.

    Returns JSON data for Vue frontend instead of rendering templates.
    """
    return handle_category_month_transactions_json(
        result_id=result_id,
        account_id=account_id,
        category_id=category_id,
        month_id=month_id,
        data_not_found_error=DATA_NOT_FOUND_ERROR
    )


@bp.route('/results/<result_id>')
def show_results(result_id: str) -> Union[Response, Any]:
    """Show summary results view.

    Route handler for returning processing results as JSON for Vue frontend.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        JSON Response with results data or error
    """
    return show_summary_results_json(result_id)


@bp.route('/results/<result_id>/details')
def show_details(result_id: str) -> Union[Response, Any]:
    """Show all transaction details in a single DataTable view.

    Route handler for returning all transaction details as JSON for Vue frontend.

    Args:
        result_id: UUID of the cached processing result

    Returns:
        JSON Response with all transaction details or error
    """
    return show_detail_results_json(result_id)

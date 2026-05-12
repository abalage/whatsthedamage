from flask import Blueprint, make_response, url_for, current_app, Response, jsonify
from typing import TYPE_CHECKING
import os
import shutil
from whatsthedamage.utils.logging import get_logger

if TYPE_CHECKING:
    from whatsthedamage.services.session_service import SessionService
    from whatsthedamage.services.configuration_service import ConfigurationService

logger = get_logger(__name__)

bp: Blueprint = Blueprint('main', __name__)
INDEX_ROUTE = 'main.index'
DATA_NOT_FOUND_ERROR = 'Data not found'


def _get_session_service() -> 'SessionService':
    """Get session service from app extensions (dependency injection)."""
    from typing import cast
    from whatsthedamage.services.session_service import SessionService
    return cast(SessionService, current_app.extensions['session_service'])


def _get_configuration_service() -> 'ConfigurationService':
    """Get ConfigurationService from app extensions (dependency injection)."""
    from typing import cast
    from whatsthedamage.services.configuration_service import ConfigurationService
    return cast(ConfigurationService, current_app.extensions['configuration_service'])


def clear_upload_folder() -> None:
    """Clear all files from the upload folder."""
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


@bp.route('/favicon.ico')
def favicon() -> Response:
    """Serve favicon.ico to prevent 404 errors in browser console."""
    return current_app.send_static_file('favicon.ico')


@bp.route('/health')
def health() -> Response:
    """Health check endpoint."""
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

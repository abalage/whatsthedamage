from flask import Blueprint, make_response, current_app, Response
import os
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

bp: Blueprint = Blueprint('main', __name__)
INDEX_ROUTE = 'main.index'
DATA_NOT_FOUND_ERROR = 'Data not found'


@bp.route('/favicon.ico')
def favicon() -> Response:
    """Serve favicon.ico to prevent 404 errors in browser console."""
    return current_app.send_static_file('dist/favicon.ico')


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

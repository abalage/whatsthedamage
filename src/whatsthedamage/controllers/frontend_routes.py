"""
Frontend SPA routes for serving Vue.js single-page application.

This module provides a catch-all route that serves the index.html
for all non-API paths, enabling the Vue SPA to handle client-side routing.
"""

from flask import Blueprint, Response, send_from_directory, current_app
from pathlib import Path

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/')
@frontend_bp.route('/<path:path>')
def serve_frontend(path: str = '') -> Response:
    """
    Catch-all route to serve the Vue SPA.

    Serves index.html for all paths that don't match API routes,
    allowing the Vue router to handle client-side navigation.

    Also serves static assets (js, css, images) from the dist directory.

    Args:
        path: The requested path that didn't match any API route

    Returns:
        The index.html file or the requested static asset
    """
    # List of file extensions that should be served as static assets
    static_extensions = {
        '.js', '.css', '.ico', '.png', '.jpg', '.jpeg', '.gif',
        '.svg', '.woff', '.woff2', '.ttf', '.json'
    }

    # Get the static folder for frontend assets
    static_folder = current_app.config.get(
        'FRONTEND_STATIC_FOLDER',
        str(Path(current_app.root_path) / 'view' / 'static' / 'dist')
    )

    # If path ends with '/' or is empty, serve index.html
    if path.endswith('/') or not path:
        return send_from_directory(static_folder, 'index.html')

    # Check if the path refers to an existing file in the static folder
    file_path = Path(static_folder) / path

    # If the requested path is a file that exists, serve it directly
    if file_path.exists() and file_path.is_file():
        return send_from_directory(static_folder, path)

    # If path looks like a static asset (has extension), try serving it
    if any(path.endswith(ext) for ext in static_extensions):
        try:
            return send_from_directory(static_folder, path)
        except Exception:
            pass

    # Otherwise, serve index.html for SPA routing
    return send_from_directory(static_folder, 'index.html')

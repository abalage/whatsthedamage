"""
Frontend SPA routes for serving the Vue frontend.

This module provides a catch-all route that serves the Vue frontend's index.html
for all non-API routes, enabling direct URL access, new tab opening, and
bookmarking of drilldown pages.

The catch-all route must be registered AFTER all API blueprints to ensure
API routes take precedence.
"""

from flask import Blueprint, current_app, make_response, jsonify, send_from_directory
import os

# Create frontend blueprint
frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_frontend(path: str) -> any:
    """Serve Vue frontend for all frontend routes.

    This catch-all route serves the frontend index.html for all routes
    that are not API endpoints. This enables:
    - Direct URL access (e.g., /results/abc123/...)
    - Opening drilldown links in new tabs
    - Bookmarking drilldown pages
    - Browser refresh on drilldown pages

    The frontend (Vue SPA) handles routing client-side via Vue Router.

    Note: This assumes the frontend has been built and the dist/ directory
    is available. In production, the frontend should be built with:
        cd frontend && npm run build:prod

    Args:
        path: The path requested by the client

    Returns:
        The frontend index.html file, or 404 if frontend not built
    """
    # Don't serve frontend for API routes - they should have been caught by earlier blueprints
    # But just in case, check for API paths
    if path.startswith('api/') or path.startswith('docs/'):
        return make_response(
            jsonify({'error': 'Not found', 'path': path}),
            404
        )

    # Path to the frontend build output (relative to project root)
    # current_app.root_path points to src/whatsthedamage
    frontend_dist_path = os.path.join(current_app.root_path, '..', '..', 'frontend', 'dist')

    # Check if the frontend has been built
    index_path = os.path.join(frontend_dist_path, 'index.html')
    
    if os.path.exists(index_path):
        # First, check if the path is a static file that exists
        # This allows serving CSS, JS, and other static assets directly
        static_file_path = os.path.join(frontend_dist_path, path) if path else index_path
        
        # Check if the requested path is a file in the dist directory
        if path and os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            return send_from_directory(
                directory=frontend_dist_path,
                path=path
            )
        
        # Serve the Vue frontend index.html for all non-API, non-static routes
        return send_from_directory(
            directory=frontend_dist_path,
            path='index.html'
        )
    else:
        # Fallback for development: return a message indicating frontend needs to be built
        return make_response(
            jsonify({
                'error': 'Frontend not built',
                'message': 'The Vue frontend needs to be built. Run: cd frontend && npm run build',
                'requested_path': '/' + path if path else '/'
            }),
            404
        )

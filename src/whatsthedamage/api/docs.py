"""API documentation blueprint with OpenAPI specs and Swagger UI.

This module provides endpoints for accessing OpenAPI specifications
and Swagger UI for interactive API documentation.
"""
from flask import Blueprint, jsonify, render_template, request, Response
from typing import Any

from whatsthedamage.api.v1.schema import get_openapi_schema as get_v1_schema
from whatsthedamage.api.v2.schema import get_openapi_schema as get_v2_schema


# Create blueprint
docs_bp = Blueprint('api_docs', __name__)


@docs_bp.route('/api/v1/openapi.json')
def v1_openapi_spec() -> Response:
    """Return OpenAPI 3.0 specification for v1 API.
    
    Returns:
        JSON response containing OpenAPI spec
    """
    return jsonify(get_v1_schema())


@docs_bp.route('/api/v2/openapi.json')
def v2_openapi_spec() -> Response:
    """Return OpenAPI 3.0 specification for v2 API.
    
    Returns:
        JSON response containing OpenAPI spec
    """
    return jsonify(get_v2_schema())


@docs_bp.route('/api/docs')
def swagger_ui() -> Any:
    """Render Swagger UI for interactive API documentation.
    
    Query Parameters:
        version (str): API version to display (v1 or v2). Defaults to v1.
    
    Returns:
        HTML page with Swagger UI
    """
    version = request.args.get('version', 'v1')
    
    # Validate version parameter
    if version not in ['v1', 'v2']:
        version = 'v1'
    
    return render_template('api_docs.html', version=version)


@docs_bp.route('/api/health')
def health_check() -> tuple[Response, int]:
    """Health check endpoint for monitoring API availability.
    
    Returns:
        JSON response with health status
    """
    return jsonify({"status": "healthy"}), 200

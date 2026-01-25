"""API documentation blueprint with OpenAPI specs.

This module provides endpoints for accessing OpenAPI specifications.
"""
from flask import Blueprint, jsonify, Response

from whatsthedamage.api.v2.schema import get_openapi_schema as get_v2_schema

# Create blueprint
docs_bp = Blueprint('api_docs', __name__)

@docs_bp.route('/api/v2/openapi.json')
def v2_openapi_spec() -> Response:
    """Return OpenAPI 3.0 specification for v2 API.

    Returns:
        JSON response containing OpenAPI spec
    """
    return jsonify(get_v2_schema())

@docs_bp.route('/api/health')
def health_check() -> tuple[Response, int]:
    """Health check endpoint for monitoring API availability.

    Returns:
        JSON response with health status
    """
    return jsonify({"status": "healthy"}), 200
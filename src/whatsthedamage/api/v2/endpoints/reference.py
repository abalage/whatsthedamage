"""Reference data endpoints.

Static reference data (categories, CSV profiles, OpenAPI spec) that
carries no user data and may be needed before login.
"""

from flask import Blueprint, jsonify, Response

from whatsthedamage.services.csv_profile_service import CsvProfileService
from whatsthedamage.utils.logging import get_logger

reference_bp = Blueprint('api_v2_reference', __name__)

logger = get_logger(__name__)


_csv_profile_service = CsvProfileService()


@reference_bp.route('/categories', methods=['GET'])
def get_categories() -> tuple[Response, int]:
    """Get all available category definitions.

    Returns the assignable (non-calculated) CategoryDefinition objects that
    the frontend can use for translating category IDs to display names
    client-side and for offering category choices. Calculated categories
    (Balance, Cost of Living, Total Spendings) are excluded because they
    are computed aggregates and cannot be assigned to transactions.

    This endpoint provides the canonical source of category definitions,
    allowing the frontend to map category_id values to localized display names.

    Returns:
        List of CategoryDefinition objects with id, default_name, and patterns.

    Status Codes:
        200: Successfully retrieved categories
    """
    from whatsthedamage.config.config import get_assignable_categories
    return jsonify([
        cat.model_dump(exclude={'calculated'}) for cat in get_assignable_categories()
    ]), 200


@reference_bp.route('/categories/cost-of-living', methods=['GET'])
def get_cost_of_living_categories() -> tuple[Response, int]:
    """Get cost of living category definitions.

    Returns:
        List of CategoryDefinition objects for categories counted in cost of living calculations.

    Status Codes:
        200: Successfully retrieved list of categories
    """
    from whatsthedamage.config.config import AVAILABLE_CATEGORIES, COST_OF_LIVING_CATEGORY_IDS
    return jsonify([
        cat.model_dump(exclude={'calculated'})
        for cat in AVAILABLE_CATEGORIES
        if cat.id in COST_OF_LIVING_CATEGORY_IDS
    ]), 200


@reference_bp.route('/csv-profiles', methods=['GET'])
def get_csv_profiles() -> tuple[Response, int]:
    """GET /api/v2/csv-profiles - List all profiles.

    Returns a list of all available CSV profiles with their metadata.

    Returns:
        List of CSV profile objects with id, name, description, version, and csv_config.

    Status Codes:
        200: Successfully retrieved CSV profiles
        500: Failed to retrieve CSV profiles
    """
    try:
        profiles = _csv_profile_service.get_all_profiles()
        return jsonify([p.model_dump() for p in profiles]), 200
    except Exception:
        logger.exception("CSV profile listing failed with unexpected exception")
        return jsonify({"error": "Failed to retrieve CSV profiles"}), 500


@reference_bp.route('/csv-profiles/<profile_id>', methods=['GET'])
def get_csv_profile(profile_id: str) -> tuple[Response, int]:
    """GET /api/v2/csv-profiles/<id> - Get specific profile.

    Returns the details of a specific CSV profile by its ID.

    Args:
        profile_id: The unique identifier of the CSV profile to retrieve.

    Returns:
        CSV profile object with all configuration details.

    Status Codes:
        200: Successfully retrieved CSV profile
        404: CSV profile not found
    """
    profile = _csv_profile_service.get_profile_by_id(profile_id)
    if not profile:
        return jsonify({"error": f"CSV profile not found: {profile_id}"}), 404
    return jsonify(profile.model_dump()), 200


@reference_bp.route('/openapi.json', methods=['GET'])
def get_openapi_spec() -> tuple[Response, int]:
    """GET /api/v2/openapi.json - Get OpenAPI specification.

    Returns the complete OpenAPI 3.0.3 specification for this API.
    This can be used with OpenAPI-compatible tools for documentation
    generation, client code generation, or testing.

    Returns:
        OpenAPI 3.0.3 specification as JSON

    Status Codes:
        200: Successfully returned OpenAPI specification
    """
    from whatsthedamage.api.v2.schema import get_openapi_schema
    return jsonify(get_openapi_schema()), 200

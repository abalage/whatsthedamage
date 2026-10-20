"""API v2 endpoints package.

Provides the v2 REST API grouped by domain in sub-blueprints:
reference data, processing results, transactions, corrections, and
statistics. The parent blueprint applies the authentication, rate
limiting, and security-header middleware to every child route.
"""

from flask import Blueprint

from whatsthedamage.api.middleware import (
    PUBLIC_V2_ROUTES,
    register_api_middleware,
)

# Create parent Blueprint
v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# Guard every v2 route with authentication and rate limiting;
# reference-data routes listed in PUBLIC_V2_ROUTES stay public.
register_api_middleware(v2_bp, PUBLIC_V2_ROUTES)

from whatsthedamage.api.v2.endpoints.reference import reference_bp  # noqa: E402
from whatsthedamage.api.v2.endpoints.processing_results import (  # noqa: E402
    processing_results_bp
)
from whatsthedamage.api.v2.endpoints.transactions import transactions_bp  # noqa: E402
from whatsthedamage.api.v2.endpoints.corrections import corrections_bp  # noqa: E402
from whatsthedamage.api.v2.endpoints.statistics import statistics_bp  # noqa: E402

v2_bp.register_blueprint(reference_bp)
v2_bp.register_blueprint(processing_results_bp)
v2_bp.register_blueprint(transactions_bp)
v2_bp.register_blueprint(corrections_bp)
v2_bp.register_blueprint(statistics_bp)

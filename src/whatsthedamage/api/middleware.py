"""Blueprint-level API middleware for authentication, rate limiting,
and security headers.

Implements US-9 of the user-driven transaction categorization epic:

- Authentication middleware on all /api/v2/* endpoints except an
  explicit public allowlist.
- General and per-endpoint rate limiting for API requests.
- Security headers (CSP, HSTS, etc.) on all responses.
"""

from typing import Any, Optional

from flask import Blueprint, Flask, Response, current_app, jsonify, request

# v2 routes that intentionally remain public. They expose static
# reference data (categories, CSV profiles, OpenAPI spec) that carries
# no user data and may be needed before login.
PUBLIC_V2_ROUTES: frozenset[str] = frozenset({
    '/api/v2/categories',
    '/api/v2/categories/cost-of-living',
    '/api/v2/csv-profiles',
    '/api/v2/csv-profiles/<profile_id>',
    '/api/v2/openapi.json',
})

# Auth routes that must be reachable without a session.
PUBLIC_AUTH_ROUTES: frozenset[str] = frozenset({
    '/api/v2/auth/register',
    '/api/v2/auth/login',
    '/api/v2/auth/reset-password',
    '/api/v2/auth/csrf-token',
})

# Expensive endpoints (file upload + ML processing, statistics
# recalculation) get a stricter rate-limit bucket.
HEAVY_ROUTES: frozenset[str] = frozenset({
    '/api/v2/processing-results',
    '/api/v2/recalculate-statistics',
})

API_CSP: str = "default-src 'none'; frame-ancestors 'none'"

SPA_CSP: str = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def get_client_ip() -> str:
    """Get the client IP address for the current request.

    Honors the X-Forwarded-For header set by reverse proxies and load
    balancers, taking the first (original client) address in the list.

    Returns:
        Client IP address string.
    """
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return str(forwarded_for.split(',')[0].strip())
    return str(request.remote_addr or '0.0.0.0')


def _rate_limit_response(retry_after: int) -> Response:
    """Build a 429 response with a Retry-After header.

    Args:
        retry_after: Seconds until the rate limit resets.

    Returns:
        JSON 429 response.
    """
    response = jsonify({
        'error': f'Too many requests. Try again in {retry_after} seconds.',
        'code': 'RATE_LIMIT_EXCEEDED',
    })
    response.status_code = 429
    response.headers['Retry-After'] = str(retry_after)
    return response


def _check_api_rate_limit() -> Optional[Response]:
    """Apply general and heavy-endpoint API rate limits.

    Every API request counts against the general limit; POST requests
    to heavy endpoints count against a stricter limit as well. Both
    are keyed on the client IP address.

    Returns:
        A 429 response when a limit is exceeded, otherwise None.
    """
    rate_limit_service = current_app.extensions.get('rate_limit_service')
    if rate_limit_service is None:
        return None

    client_ip = get_client_ip()
    exceeded, retry_after = rate_limit_service.check_api_rate_limit(
        client_ip,
        current_app.config['RATE_LIMIT_API_MAX'],
        current_app.config['RATE_LIMIT_API_WINDOW'],
    )
    if exceeded:
        return _rate_limit_response(retry_after)

    rule = request.url_rule.rule if request.url_rule is not None else ''
    if request.method == 'POST' and rule in HEAVY_ROUTES:
        exceeded, retry_after = rate_limit_service.check_api_rate_limit(
            f'heavy:{client_ip}',
            current_app.config['RATE_LIMIT_HEAVY_MAX'],
            current_app.config['RATE_LIMIT_HEAVY_WINDOW'],
        )
        if exceeded:
            return _rate_limit_response(retry_after)

    return None


def register_api_middleware(
    bp: Blueprint,
    public_routes: frozenset[str],
) -> None:
    """Attach authentication and rate-limit guards to a blueprint.

    Every request to a blueprint route is rate limited and, unless its
    URL rule is listed in public_routes, required to carry a valid
    session cookie. CORS preflight (OPTIONS) requests are exempt so
    they pass without credentials.

    Per-route authentication and CSRF decorators remain in place as
    defense in depth; this guard makes it impossible for a new endpoint
    to ship without authentication.

    Args:
        bp: Blueprint to guard (v2_bp or auth_bp).
        public_routes: URL rules that stay publicly accessible.
    """

    @bp.before_request
    def enforce_api_security() -> Any:
        if request.method == 'OPTIONS':
            return None

        rate_limit_response = _check_api_rate_limit()
        if rate_limit_response is not None:
            return rate_limit_response

        rule = (
            request.url_rule.rule
            if request.url_rule is not None
            else request.path
        )
        if rule in public_routes:
            return None

        auth_service = current_app.extensions.get('auth_service')
        if not auth_service:
            return jsonify(
                {'error': 'Authentication service not available'}
            ), 500

        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401

        result = auth_service.validate_session(session_token)
        if not result:
            return jsonify({'error': 'Authentication required'}), 401

        user, session = result
        request.user = user  # type: ignore[attr-defined]
        request.session = session  # type: ignore[attr-defined]
        return None


def register_security_headers(app: Flask) -> None:
    """Register an after_request hook setting security headers.

    Adds CSP, HSTS, X-Frame-Options, X-Content-Type-Options, and
    Referrer-Policy to every response. API responses additionally get
    Cache-Control: no-store because they carry per-user data. HSTS is
    controlled by config; browsers ignore it over plain HTTP, so it is
    safe to enable by default.

    Args:
        app: Flask application.
    """

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Content-Security-Policy'] = API_CSP
        else:
            response.headers['Content-Security-Policy'] = SPA_CSP

        if app.config.get('HSTS_ENABLED'):
            max_age = app.config.get('HSTS_MAX_AGE', 31536000)
            response.headers['Strict-Transport-Security'] = f'max-age={max_age}'
        return response

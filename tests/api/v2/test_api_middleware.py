"""Tests for the API middleware layer (US-9).

Covers the blueprint-level authentication guard, the general and
per-endpoint rate limits, registration rate limiting, and the
security headers applied to every response.
"""

import re

from flask import Flask

from whatsthedamage.services.rate_limit_service import RateLimitService


# URL rules that intentionally remain public: static reference data
# under /api/v2 and the pre-session auth endpoints.
PUBLIC_RULES = {
    '/api/v2/categories',
    '/api/v2/categories/cost-of-living',
    '/api/v2/csv-profiles',
    '/api/v2/csv-profiles/<profile_id>',
    '/api/v2/openapi.json',
    '/api/v2/auth/register',
    '/api/v2/auth/login',
    '/api/v2/auth/reset-password',
    '/api/v2/auth/csrf-token',
}

# Sample values substituted for URL converters when building concrete
# request paths from URL rules.
CONVERTER_SAMPLES = {
    'int': '1',
    'float': '1.0',
    'uuid': '00000000-0000-0000-0000-000000000000',
}


def _build_request_path(rule) -> str:
    """Convert a URL rule into a concrete requestable path.

    Args:
        rule: Werkzeug Rule from the url_map.

    Returns:
        Path with converter placeholders replaced by sample values.
    """

    def replace(match: re.Match) -> str:
        return CONVERTER_SAMPLES.get(match.group(1) or '', 'x')

    return re.sub(r'<(?:([^:<>]+):)?[^>]+>', replace, rule.rule)


class TestAuthenticationGuard:
    """Blueprint middleware requires a session on every non-public route."""

    def test_every_non_public_v2_route_returns_401_without_session(
        self, api_app: Flask
    ) -> None:
        """All /api/v2 routes outside the public allowlist reject
        unauthenticated requests regardless of HTTP method."""
        client = api_app.test_client()
        checked = []
        for rule in api_app.url_map.iter_rules():
            if not rule.rule.startswith('/api/v2'):
                continue
            if rule.rule in PUBLIC_RULES:
                continue
            methods = (rule.methods or set()) - {'HEAD', 'OPTIONS'}
            assert methods, f'{rule.rule} has no testable methods'
            method = sorted(methods)[0].lower()
            path = _build_request_path(rule)
            response = getattr(client, method)(path)
            assert response.status_code == 401, (
                f'{method.upper()} {path} returned '
                f'{response.status_code}, expected 401'
            )
            checked.append(f'{method.upper()} {path}')
        assert checked, 'no /api/v2 routes were inspected'

    def test_public_v2_routes_are_accessible_without_session(
        self, api_app: Flask
    ) -> None:
        """Reference-data endpoints stay public per the allowlist."""
        client = api_app.test_client()
        for path in (
            '/api/v2/categories',
            '/api/v2/categories/cost-of-living',
            '/api/v2/openapi.json',
        ):
            response = client.get(path)
            assert response.status_code == 200, path

        response = client.get('/api/v2/csv-profiles')
        assert response.status_code == 200
        profiles = response.get_json()
        assert profiles, 'no CSV profiles configured'
        profile_id = profiles[0]['id']
        response = client.get(f'/api/v2/csv-profiles/{profile_id}')
        assert response.status_code == 200

    def test_cors_preflight_passes_without_session(
        self, api_app: Flask
    ) -> None:
        """OPTIONS preflight requests are exempt from the auth guard
        so cross-origin API usage keeps working."""
        client = api_app.test_client()
        response = client.open(
            '/api/v2/transactions',
            method='OPTIONS',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
            },
        )
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_invalid_session_cookie_returns_401(
        self, api_app: Flask
    ) -> None:
        """A present but invalid session cookie is rejected."""
        client = api_app.test_client()
        client.set_cookie('session_token', 'invalid-token')
        response = client.get('/api/v2/transactions')
        assert response.status_code == 401
        assert response.get_json()['error'] == 'Authentication required'


class TestApiRateLimit:
    """General and heavy-endpoint rate limits enforced by the middleware."""

    def test_general_rate_limit_returns_429(self, api_app: Flask) -> None:
        """Requests beyond the configured general limit get a 429 with
        a Retry-After header."""
        api_app.config['RATE_LIMIT_API_MAX'] = 3
        client = api_app.test_client()
        for _ in range(3):
            assert client.get('/api/v2/categories').status_code == 200
        response = client.get('/api/v2/categories')
        assert response.status_code == 429
        assert response.get_json()['code'] == 'RATE_LIMIT_EXCEEDED'
        assert int(response.headers['Retry-After']) >= 0

    def test_heavy_endpoint_rate_limit_returns_429(
        self, api_app: Flask
    ) -> None:
        """POST /processing-results gets a stricter bucket than the
        general limit, independent of authentication."""
        api_app.config['RATE_LIMIT_API_MAX'] = 100
        api_app.config['RATE_LIMIT_HEAVY_MAX'] = 2
        client = api_app.test_client()
        for _ in range(2):
            response = client.post('/api/v2/processing-results')
            assert response.status_code == 401
        response = client.post('/api/v2/processing-results')
        assert response.status_code == 429
        assert 'Retry-After' in response.headers

    def test_heavy_rate_limit_does_not_block_other_endpoints(
        self, api_app: Flask
    ) -> None:
        """The heavy bucket only throttles its own endpoints."""
        api_app.config['RATE_LIMIT_API_MAX'] = 100
        api_app.config['RATE_LIMIT_HEAVY_MAX'] = 1
        client = api_app.test_client()
        client.post('/api/v2/processing-results')
        response = client.post('/api/v2/processing-results')
        assert response.status_code == 429
        assert client.get('/api/v2/categories').status_code == 200

    def test_registration_rate_limit_returns_429(
        self, api_app: Flask
    ) -> None:
        """POST /auth/register is throttled per IP once the attempt
        count is exhausted."""
        api_app.extensions['rate_limit_service'] = RateLimitService(
            max_attempts=2, window_seconds=900
        )
        client = api_app.test_client()
        for i in range(2):
            response = client.post(
                '/api/v2/auth/register',
                json={
                    'username': f'ratelimit-user-{i}',
                    'password': 'password-123456',
                },
            )
            assert response.status_code == 201, response.get_json()
        response = client.post(
            '/api/v2/auth/register',
            json={
                'username': 'ratelimit-user-3',
                'password': 'password-123456',
            },
        )
        assert response.status_code == 429
        assert response.get_json()['code'] == 'RATE_LIMIT_EXCEEDED'
        assert int(response.headers['Retry-After']) > 0


class TestSecurityHeaders:
    """Security headers applied to API and SPA responses."""

    def test_api_response_security_headers(self, api_app: Flask) -> None:
        """API responses carry the full header set and are never
        cached because they contain per-user data."""
        client = api_app.test_client()
        response = client.get('/api/v2/categories')
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert response.headers['Referrer-Policy'] == (
            'strict-origin-when-cross-origin'
        )
        assert response.headers['Cache-Control'] == 'no-store'
        assert "default-src 'none'" in response.headers[
            'Content-Security-Policy'
        ]
        assert 'max-age=' in response.headers[
            'Strict-Transport-Security'
        ]

    def test_spa_response_security_headers(self, api_app: Flask) -> None:
        """Non-API responses use the SPA content security policy and
        are not marked no-store."""
        client = api_app.test_client()
        response = client.get('/')
        csp = response.headers['Content-Security-Policy']
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert response.headers.get('Cache-Control') != 'no-store'
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

    def test_hsts_can_be_disabled_via_config(
        self, api_app: Flask
    ) -> None:
        """HSTS is not sent when HSTS_ENABLED is false (e.g. local
        HTTP development)."""
        api_app.config['HSTS_ENABLED'] = False
        client = api_app.test_client()
        response = client.get('/api/v2/categories')
        assert 'Strict-Transport-Security' not in response.headers

    def test_hsts_max_age_from_config(self, api_app: Flask) -> None:
        """The HSTS max-age honors the configured value."""
        api_app.config['HSTS_MAX_AGE'] = 60
        client = api_app.test_client()
        response = client.get('/api/v2/categories')
        assert response.headers['Strict-Transport-Security'] == (
            'max-age=60'
        )


class TestCorsConfiguration:
    """CORS origins are configuration-driven."""

    def test_default_dev_origins_loaded(self, api_app: Flask) -> None:
        """The Vite dev server origins are configured by default."""
        assert 'http://localhost:3000' in api_app.config['CORS_ORIGINS']
        assert 'http://127.0.0.1:3000' in api_app.config['CORS_ORIGINS']

    def test_cors_uses_configured_origins(self) -> None:
        """_configure_cors allows exactly the origins from app config."""
        from whatsthedamage.app import _configure_cors

        app = Flask(__name__)

        @app.route('/api/ping')
        def ping() -> str:
            return 'ok'

        app.config['CORS_ORIGINS'] = ['https://example.com']
        _configure_cors(app)
        client = app.test_client()
        allowed = client.get(
            '/api/ping', headers={'Origin': 'https://example.com'}
        )
        assert allowed.headers.get('Access-Control-Allow-Origin') == (
            'https://example.com'
        )
        denied = client.get(
            '/api/ping', headers={'Origin': 'https://evil.example'}
        )
        assert denied.headers.get('Access-Control-Allow-Origin') is None

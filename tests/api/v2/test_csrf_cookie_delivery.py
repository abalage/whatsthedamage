"""Functional tests for CSRF token cookie delivery.

The CSRF token is delivered as a readable (not HttpOnly) cookie on
register, login, /auth/me (when the session has no token yet), and
/auth/csrf-token; logout clears it. Response bodies no longer carry
a csrf_token field.

The test client's host is 'localhost', where cookie attributes are
deliberately relaxed (SameSite=Lax, not Secure) to work across the
dev ports; the non-localhost policy (Secure, SameSite from config)
is covered by a dedicated test.
"""

from flask import Flask

from tests.api.v2.conftest import csrf_token_from_response


PASSWORD = 'password-123456'


def _csrf_cookie_header(response) -> str:
    """Return the raw Set-Cookie header for the csrf_token cookie.

    Args:
        response: Flask response that may carry a csrf_token cookie.

    Returns:
        The full Set-Cookie header value.

    Raises:
        AssertionError: When the response carries no csrf_token cookie.
    """
    for header in response.headers.getlist('Set-Cookie'):
        if header.startswith('csrf_token='):
            return header
    raise AssertionError('No csrf_token cookie in response headers')


def _assert_no_csrf_cookie(response) -> None:
    """Assert the response carries no csrf_token cookie.

    Args:
        response: Flask response.

    Raises:
        AssertionError: When a csrf_token cookie is present.
    """
    for header in response.headers.getlist('Set-Cookie'):
        if header.startswith('csrf_token='):
            raise AssertionError(
                f'Unexpected csrf_token cookie: {header}'
            )


def _register(api_app: Flask):
    """Register a user and return (client, csrf_token).

    Args:
        api_app: Flask application with a temporary database.

    Returns:
        Tuple of (test client, CSRF token from the cookie).
    """
    client = api_app.test_client()
    response = client.post(
        '/api/v2/auth/register',
        json={'username': 'alice', 'password': PASSWORD}
    )
    assert response.status_code == 201, response.get_json()
    return client, csrf_token_from_response(response)


class TestCsrfCookieDelivery:
    """Tests for the csrf_token cookie on the auth endpoints."""

    def test_register_sets_readable_cookie(self, api_app: Flask):
        """Register sets a readable csrf_token cookie, not a body field."""
        client = api_app.test_client()
        response = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 201

        header = _csrf_cookie_header(response)
        assert 'HttpOnly' not in header
        assert 'Path=/' in header
        assert 'SameSite=Lax' in header
        assert 'Secure' not in header

        assert 'csrf_token' not in response.get_json()
        assert csrf_token_from_response(response)

    def test_login_sets_readable_cookie(self, api_app: Flask):
        """Login sets a readable csrf_token cookie, not a body field."""
        _register(api_app)
        client = api_app.test_client()
        response = client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 200

        header = _csrf_cookie_header(response)
        assert 'HttpOnly' not in header
        assert 'Path=/' in header
        assert 'SameSite=Lax' in header
        assert 'Secure' not in header

        assert 'csrf_token' not in response.get_json()

    def test_csrf_token_endpoint_sets_cookie(self, api_app: Flask):
        """/auth/csrf-token sets a fresh readable cookie."""
        client, _ = _register(api_app)
        response = client.get('/api/v2/auth/csrf-token')
        assert response.status_code == 200

        header = _csrf_cookie_header(response)
        assert 'HttpOnly' not in header
        assert 'Path=/' in header
        assert 'SameSite=Lax' in header

        assert response.get_json() == {}

    def test_me_sets_cookie_when_session_has_no_token(
        self, api_app: Flask
    ):
        """/auth/me mints a cookie when the session has no token yet."""
        client, _ = _register(api_app)

        from whatsthedamage.models.database.session import Session as SessionDB
        db = api_app.extensions['db_session_factory']()
        try:
            sessions = (
                db.query(SessionDB)
                .filter_by(user_id=1, is_revoked=False)
                .all()
            )
            assert sessions
            for session in sessions:
                session.csrf_token_hash = None
            db.commit()
        finally:
            db.close()

        response = client.get('/api/v2/auth/me')
        assert response.status_code == 200

        header = _csrf_cookie_header(response)
        assert 'HttpOnly' not in header
        assert 'Path=/' in header
        assert 'csrf_token' not in response.get_json()

    def test_me_does_not_set_cookie_when_session_has_token(
        self, api_app: Flask
    ):
        """/auth/me leaves the token alone when the session already has one."""
        client, _ = _register(api_app)
        response = client.get('/api/v2/auth/me')
        assert response.status_code == 200
        _assert_no_csrf_cookie(response)

    def test_logout_clears_cookie(self, api_app: Flask):
        """Logout clears the csrf_token cookie."""
        client, csrf_token = _register(api_app)
        response = client.post(
            '/api/v2/auth/logout',
            headers={'X-CSRF-Token': csrf_token}
        )
        assert response.status_code == 200

        header = _csrf_cookie_header(response)
        assert header.startswith('csrf_token=;')
        assert 'Max-Age=0' in header

    def test_non_localhost_host_uses_secure_cookie(self, api_app: Flask):
        """Away from localhost the cookie is Secure with the configured policy."""
        client = api_app.test_client()
        response = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD},
            headers={'Host': 'example.com'}
        )
        assert response.status_code == 201

        header = _csrf_cookie_header(response)
        assert 'HttpOnly' not in header
        assert 'Path=/' in header
        assert 'Secure' in header
        assert 'SameSite=Lax' in header

    def test_minted_cookie_is_usable_for_state_changes(
        self, api_app: Flask
    ):
        """The cookie token validates on a subsequent state-changing request."""
        client, csrf_token = _register(api_app)

        response = client.post(
            '/api/v2/auth/logout',
            headers={'X-CSRF-Token': csrf_token}
        )
        assert response.status_code == 200

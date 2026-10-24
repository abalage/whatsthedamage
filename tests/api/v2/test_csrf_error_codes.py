"""Tests for machine-readable error codes on CSRF 403 responses.

The frontend's automatic CSRF retry depends on the `code` field of
the 403 responses emitted by the require_csrf decorator; these tests
pin the contract so it cannot regress silently.
"""

from types import SimpleNamespace
from typing import Any

from flask import Flask, request

from tests.api.v2.conftest import AuthContext, csrf_token_from_response


PASSWORD = 'password-123456'


class TestCsrfErrorCodesFunctional:
    """Functional coverage of the CSRF 403 codes via the API."""

    def test_missing_token_header_returns_403_with_code(
        self, auth_context: AuthContext
    ):
        """A state-changing request without a token reports CSRF_TOKEN_MISSING."""
        response = auth_context.client.post(
            '/api/v2/transactions',
            json={'date': '2026-01-15'},
            headers={}
        )
        assert response.status_code == 403
        assert response.get_json()['code'] == 'CSRF_TOKEN_MISSING'
        assert response.get_json()['error'] == (
            'CSRF token required for state-changing requests'
        )

    def test_wrong_token_returns_403_with_code(
        self, auth_context: AuthContext
    ):
        """A wrong token reports CSRF_TOKEN_INVALID."""
        response = auth_context.client.post(
            '/api/v2/transactions',
            json={'date': '2026-01-15'},
            headers={'X-CSRF-Token': 'wrong-token'}
        )
        assert response.status_code == 403
        assert response.get_json()['code'] == 'CSRF_TOKEN_INVALID'
        assert response.get_json()['error'] == 'Invalid CSRF token'

    def test_session_without_token_returns_403_with_code(
        self, api_app: Flask
    ):
        """A session whose stored hash was cleared reports CSRF_TOKEN_NOT_SET."""
        client = api_app.test_client()
        register = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert register.status_code == 201
        csrf_token = csrf_token_from_response(register)

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

        response = client.post(
            '/api/v2/transactions',
            json={'date': '2026-01-15'},
            headers={'X-CSRF-Token': csrf_token}
        )
        assert response.status_code == 403
        assert response.get_json()['code'] == 'CSRF_TOKEN_NOT_SET'
        assert response.get_json()['error'] == 'Session has no CSRF token'


class TestCsrfErrorCodeUnit:
    """Unit coverage of the decorator path not reachable via HTTP."""

    def test_missing_session_returns_403_with_code(self):
        """A state-changing request without a session context reports
        CSRF_SESSION_REQUIRED."""
        from whatsthedamage.api.auth_decorators import require_csrf

        app = Flask(__name__)
        app.extensions['auth_service'] = SimpleNamespace()

        @require_csrf
        def handler() -> Any:
            return {'ok': True}

        with app.test_request_context('/x', method='POST'):
            response, status = handler()

        assert status == 403
        assert response.get_json()['code'] == 'CSRF_SESSION_REQUIRED'
        assert response.get_json()['error'] == (
            'CSRF token requires authenticated session'
        )

    def test_non_state_changing_methods_skip_validation(self):
        """GET requests pass through the CSRF decorator untouched."""
        from whatsthedamage.api.auth_decorators import require_csrf

        app = Flask(__name__)
        app.extensions['auth_service'] = SimpleNamespace()

        @require_csrf
        def handler() -> Any:
            return {'ok': True}

        with app.test_request_context('/x', method='GET'):
            assert handler() == {'ok': True}
            assert request.method == 'GET'

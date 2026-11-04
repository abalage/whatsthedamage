"""Functional tests for two-phase registration.

Phase 1 (POST /api/v2/auth/register) creates a pending registration
row and returns a one-time pending token plus the one-time recovery
code, without creating an account or a session. Phase 2
(POST /api/v2/auth/register/confirm) commits the account only when the
client echoes the recovery code, proving it was saved, and then issues
the session. Pending rows expire and are purged by the retention job.
"""

from datetime import datetime, timedelta, UTC

from flask import Flask

from tests.api.v2.conftest import (
    confirm_registration,
    csrf_token_from_response,
    register_pending,
    register_user,
)

PASSWORD = 'password-123456'


def _pending_user_row(api_app: Flask, username: str):
    """Load the raw users row for username, pending or confirmed."""
    from whatsthedamage.models.database.user import User as UserDB
    db = api_app.extensions['db_session_factory']()
    try:
        return db.query(UserDB).filter_by(username=username).first()
    finally:
        db.close()


class TestPhaseOne:
    """POST /auth/register creates only a pending registration."""

    def test_returns_pending_token_and_recovery_code(self, api_app: Flask):
        client = api_app.test_client()
        response = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['pending_token']
        assert data['recovery_code']
        assert data['expires_at']
        assert 'user' not in data
        assert 'session_expires_at' not in data

    def test_sets_no_cookies(self, api_app: Flask):
        client = api_app.test_client()
        response = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 201
        assert response.headers.getlist('Set-Cookie') == []

    def test_creates_pending_row_not_a_confirmed_account(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        row = _pending_user_row(api_app, 'alice')
        assert row is not None
        assert row.registration_confirmed_at is None
        assert row.pending_token_hash is not None
        assert row.pending_expires_at is not None

    def test_pending_user_cannot_log_in(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        response = client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 401

    def test_pending_user_cannot_reset_password(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        response = client.post(
            '/api/v2/auth/reset-password',
            json={
                'username': 'alice',
                'recoveryCode': pending['recovery_code'],
                'newPassword': 'brand-new-password-1'
            }
        )
        assert response.status_code == 401

    def test_pending_user_has_no_session(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        response = client.get('/api/v2/auth/me')
        assert response.status_code == 401

    def test_duplicate_username_while_pending(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        response = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert response.status_code == 409
        assert response.get_json()['code'] == 'USERNAME_EXISTS'

    def test_validation_errors(self, api_app: Flask):
        client = api_app.test_client()
        assert client.post(
            '/api/v2/auth/register', json={'password': PASSWORD}
        ).status_code == 400
        assert client.post(
            '/api/v2/auth/register', json={'username': 'alice'}
        ).status_code == 400
        assert client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': 'short'}
        ).status_code == 422


class TestPhaseTwo:
    """POST /auth/register/confirm commits the account."""

    def test_confirm_with_correct_echo_succeeds(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        response = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'alice'
        assert data['session_expires_at']
        assert 'recovery_code' not in data
        # session + csrf cookies are set only now
        assert csrf_token_from_response(response)
        cookie_names = [
            h.split(';', 1)[0].split('=', 1)[0]
            for h in response.headers.getlist('Set-Cookie')
        ]
        assert 'session_token' in cookie_names

    def test_confirmed_account_row(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        row = _pending_user_row(api_app, 'alice')
        assert row.registration_confirmed_at is not None
        assert row.pending_token_hash is None
        assert row.pending_expires_at is None

    def test_confirmed_user_can_log_in_and_use_api(self, api_app: Flask):
        client = api_app.test_client()
        register_user(client, 'alice', PASSWORD)
        me = client.get('/api/v2/auth/me')
        assert me.status_code == 200
        assert me.get_json()['user']['username'] == 'alice'

    def test_confirm_with_wrong_code_is_rejected(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        response = confirm_registration(
            client, pending['pending_token'], 'XXXX-XXXX-XXXX-XXXX'
        )
        assert response.status_code == 401
        assert response.get_json()['code'] == 'REGISTRATION_INVALID'
        # nothing committed, no cookies
        assert response.headers.getlist('Set-Cookie') == []
        row = _pending_user_row(api_app, 'alice')
        assert row.registration_confirmed_at is None

    def test_confirm_with_unknown_token_is_rejected(self, api_app: Flask):
        client = api_app.test_client()
        response = confirm_registration(client, 'no-such-token', 'ABCD-EFGH-JKLM-NPQR')
        assert response.status_code == 401
        assert response.get_json()['code'] == 'REGISTRATION_INVALID'

    def test_confirm_twice_second_fails(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        first = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert first.status_code == 200
        second = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert second.status_code == 401

    def test_confirm_missing_fields(self, api_app: Flask):
        client = api_app.test_client()
        assert client.post(
            '/api/v2/auth/register/confirm', json={}
        ).status_code == 400
        assert client.post(
            '/api/v2/auth/register/confirm',
            json={'pending_token': 'x'}
        ).status_code == 400

    def test_confirm_is_public_but_rate_limited(self, api_app: Flask):
        """Confirm needs no session (public) but is throttled per IP."""
        from whatsthedamage.services.rate_limit_service import RateLimitService
        api_app.extensions['rate_limit_service'] = RateLimitService(
            max_attempts=2, window_seconds=900
        )
        client = api_app.test_client()
        for i in range(2):
            pending = register_pending(client, f'user-{i}', PASSWORD)
            assert pending
        # register bucket exhausted: even confirm is throttled
        response = confirm_registration(client, 'whatever', 'whatever')
        assert response.status_code == 429


class TestPendingExpiry:
    """Expired pending registrations are rejected and purged."""

    def _expire_pending(self, api_app: Flask, username: str) -> None:
        from whatsthedamage.models.database.user import User as UserDB
        db = api_app.extensions['db_session_factory']()
        try:
            row = db.query(UserDB).filter_by(username=username).first()
            row.pending_expires_at = datetime.now(UTC) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

    def test_confirm_expired_pending_is_rejected(self, api_app: Flask):
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        self._expire_pending(api_app, 'alice')
        response = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert response.status_code == 401

    def test_expired_pending_username_can_be_reused(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        self._expire_pending(api_app, 'alice')
        # Re-registering the same username succeeds (lazy cleanup)
        pending = register_pending(client, 'alice', PASSWORD)
        response = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert response.status_code == 200

    def test_retention_purge_deletes_expired_pending(self, api_app: Flask):
        from whatsthedamage.models.database.user import User as UserDB
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        self._expire_pending(api_app, 'alice')

        retention = api_app.extensions['retention_service']
        result = retention.purge()
        assert result['pending_registrations_deleted'] == 1
        assert _pending_user_row(api_app, 'alice') is None

    def test_retention_purge_keeps_unexpired_pending(self, api_app: Flask):
        client = api_app.test_client()
        register_pending(client, 'alice', PASSWORD)
        retention = api_app.extensions['retention_service']
        result = retention.purge()
        assert result['pending_registrations_deleted'] == 0
        assert _pending_user_row(api_app, 'alice') is not None

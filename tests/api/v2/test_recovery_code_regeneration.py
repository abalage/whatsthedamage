"""Functional tests for POST /api/v2/auth/me/recovery-code.

Covers recovery code regeneration while logged in: password
confirmation, old code invalidation, new code usability, session
revocation, CSRF protection, and rate limiting.
"""

from flask import Flask

from tests.api.v2.conftest import (
    AuthContext,
    confirm_registration,
    csrf_token_from_response,
    register_pending,
    register_user,
)


PASSWORD = 'password-123456'


class TestRegenerateRecoveryCode:
    """Tests for POST /api/v2/auth/me/recovery-code."""

    def test_regenerates_recovery_code(self, auth_context: AuthContext):
        """A valid request returns a new formatted recovery code."""
        response = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'new_recovery_code' in data
        assert len(data['new_recovery_code']) == 19  # 16 chars + 3 hyphens

    def test_new_code_works_for_password_reset(self, auth_context: AuthContext):
        """The new recovery code can be used to reset the password."""
        regen = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers=auth_context.csrf_headers
        )
        assert regen.status_code == 200
        new_code = regen.get_json()['new_recovery_code']

        reset = auth_context.client.post(
            '/api/v2/auth/reset-password',
            json={
                'username': auth_context.username,
                'recoveryCode': new_code,
                'newPassword': 'brand-new-password-123'
            }
        )
        assert reset.status_code == 200

    def test_old_code_invalidated(self, api_app: Flask):
        """The original recovery code no longer works after regeneration."""
        client = api_app.test_client()
        pending = register_pending(client, 'alice', PASSWORD)
        original_code = pending['recovery_code']
        register = confirm_registration(
            client, pending['pending_token'], pending['recovery_code']
        )
        assert register.status_code == 200
        csrf_token = csrf_token_from_response(register)

        regen = client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers={'X-CSRF-Token': csrf_token}
        )
        assert regen.status_code == 200

        reset = client.post(
            '/api/v2/auth/reset-password',
            json={
                'username': 'alice',
                'recoveryCode': original_code,
                'newPassword': 'another-password-456'
            }
        )
        assert reset.status_code == 401

    def test_rejects_wrong_password(self, auth_context: AuthContext):
        """A wrong password is rejected with 401."""
        response = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': 'wrong-password'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 401
        assert response.get_json()['code'] == 'INVALID_CREDENTIALS'

    def test_rejects_missing_password(self, auth_context: AuthContext):
        """A body without a password field is rejected with 400."""
        response = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400
        assert response.get_json()['code'] == 'MISSING_PASSWORD'

    def test_requires_authentication(self, api_app: Flask):
        """Without a session cookie the request is rejected."""
        response = api_app.test_client().post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD}
        )

        assert response.status_code == 401

    def test_requires_csrf_token(self, api_app: Flask):
        """A valid session without a CSRF header is rejected."""
        client = api_app.test_client()
        register_user(client, 'alice', PASSWORD)

        response = client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD}
        )

        assert response.status_code == 403

    def test_current_session_stays_valid(self, auth_context: AuthContext):
        """After regeneration the current session still works."""
        response = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers=auth_context.csrf_headers
        )
        assert response.status_code == 200

        me = auth_context.client.get('/api/v2/auth/me')
        assert me.status_code == 200

    def test_other_sessions_revoked(self, api_app: Flask):
        """All other sessions of the user are revoked on regeneration."""
        client = api_app.test_client()
        register = register_user(client, 'alice', PASSWORD)
        csrf_token = csrf_token_from_response(register)

        other_client = api_app.test_client()
        login = other_client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login.status_code == 200

        response = client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers={'X-CSRF-Token': csrf_token}
        )
        assert response.status_code == 200

        me = other_client.get('/api/v2/auth/me')
        assert me.status_code == 401

    def test_rate_limited_after_5_attempts(self, auth_context: AuthContext):
        """The 6th attempt within the window is rate limited."""
        for _ in range(5):
            response = auth_context.client.post(
                '/api/v2/auth/me/recovery-code',
                json={'password': 'wrong-password'},
                headers=auth_context.csrf_headers
            )
            assert response.status_code == 401

        response = auth_context.client.post(
            '/api/v2/auth/me/recovery-code',
            json={'password': PASSWORD},
            headers=auth_context.csrf_headers
        )
        assert response.status_code == 429

"""Functional tests for account rectification endpoints (GDPR
Art. 7, 16).

Covers PUT /api/v2/auth/me (username change, consent timestamps)
and PUT /api/v2/auth/me/password (password change with session
revocation).
"""

from flask import Flask

from tests.api.v2.conftest import AuthContext, csrf_token_from_response


PASSWORD = 'password-123456'


class TestUsernameChange:
    """Tests for the username field of PUT /api/v2/auth/me."""

    def test_changes_username(self, auth_context: AuthContext):
        """A valid request updates the username."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'username': 'alice-renamed'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        assert response.get_json()['user']['username'] == (
            'alice-renamed'
        )

        # The new username works for login
        login = auth_context.client.post(
            '/api/v2/auth/login',
            json={'username': 'alice-renamed', 'password': PASSWORD}
        )
        assert login.status_code == 200

    def test_rejects_taken_username(
        self, auth_context: AuthContext, second_auth_context: AuthContext
    ):
        """A username owned by another user is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'username': 'bob'},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 409
        assert response.get_json()['code'] == 'USERNAME_EXISTS'

    def test_rejects_empty_username(self, auth_context: AuthContext):
        """An empty (whitespace-only) username is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'username': '   '},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_rejects_empty_body(self, auth_context: AuthContext):
        """A body without any known field is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 400

    def test_requires_csrf_token(self, api_app: Flask):
        """A valid session without a CSRF header is rejected."""
        client = api_app.test_client()
        register = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert register.status_code == 201

        response = client.put(
            '/api/v2/auth/me',
            json={'username': 'alice-renamed'}
        )

        assert response.status_code == 403


class TestConsentTimestamps:
    """Tests for the consent timestamps of the sharing opt-in."""

    def test_opt_in_records_timestamps(
        self, auth_context: AuthContext
    ):
        """Opting in records opted_in_at and clears opted_out_at."""
        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': True},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        user = response.get_json()['user']
        assert user['opt_in_sharing'] is True
        assert user['opted_in_at'] is not None
        assert user['opted_out_at'] is None

    def test_opt_out_records_timestamp(
        self, auth_context: AuthContext
    ):
        """Opting out records opted_out_at."""
        auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': True},
            headers=auth_context.csrf_headers
        )

        response = auth_context.client.put(
            '/api/v2/auth/me',
            json={'opt_in_sharing': False},
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200
        user = response.get_json()['user']
        assert user['opt_in_sharing'] is False
        assert user['opted_out_at'] is not None


class TestChangePassword:
    """Tests for PUT /api/v2/auth/me/password."""

    def test_changes_password_and_keeps_current_session(
        self, auth_context: AuthContext
    ):
        """A valid change updates the password; this session stays."""
        response = auth_context.client.put(
            '/api/v2/auth/me/password',
            json={
                'current_password': PASSWORD,
                'new_password': 'new-password-456789'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 200

        # The current session still works
        me = auth_context.client.get('/api/v2/auth/me')
        assert me.status_code == 200

        # The new password works for login
        login = auth_context.client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': 'new-password-456789'}
        )
        assert login.status_code == 200

    def test_revokes_other_sessions(self, api_app: Flask):
        """All other sessions of the user are revoked."""
        client = api_app.test_client()
        register = client.post(
            '/api/v2/auth/register',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert register.status_code == 201
        csrf_token = csrf_token_from_response(register)

        # A second session from another client
        other_client = api_app.test_client()
        login = other_client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login.status_code == 200

        response = client.put(
            '/api/v2/auth/me/password',
            json={
                'current_password': PASSWORD,
                'new_password': 'new-password-456789'
            },
            headers={'X-CSRF-Token': csrf_token}
        )
        assert response.status_code == 200

        # The other session was revoked
        me = other_client.get('/api/v2/auth/me')
        assert me.status_code == 401

    def test_rejects_wrong_current_password(
        self, auth_context: AuthContext
    ):
        """A wrong current password is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me/password',
            json={
                'current_password': 'wrong-password',
                'new_password': 'new-password-456789'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 401
        assert response.get_json()['code'] == 'INVALID_CREDENTIALS'

    def test_rejects_weak_new_password(
        self, auth_context: AuthContext
    ):
        """A too short new password is rejected."""
        response = auth_context.client.put(
            '/api/v2/auth/me/password',
            json={
                'current_password': PASSWORD,
                'new_password': 'short'
            },
            headers=auth_context.csrf_headers
        )

        assert response.status_code == 422
        assert response.get_json()['code'] == 'PASSWORD_TOO_WEAK'

    def test_requires_authentication(self, api_app: Flask):
        """Without a session cookie the request is rejected."""
        response = api_app.test_client().put(
            '/api/v2/auth/me/password',
            json={
                'current_password': PASSWORD,
                'new_password': 'new-password-456789'
            }
        )

        assert response.status_code == 401

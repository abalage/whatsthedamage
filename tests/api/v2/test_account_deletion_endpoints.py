"""Functional tests for the account deletion and retention endpoints.

Covers DELETE /api/v2/auth/account (US-10): password confirmation,
session revocation, the login-cancels-deletion grace behavior, and
the retention purge job.
"""

from datetime import datetime, timedelta, UTC

from flask import Flask


PASSWORD = 'password-123456'


def _register(app: Flask, username: str, password: str = PASSWORD):
    """Register a user and return its authenticated client context.

    The registration happens on the returned client, so its session
    cookie and CSRF token are valid for subsequent requests.

    Args:
        app: Flask application to create the test client from.
        username: Username to register.
        password: Password for the new account.

    Returns:
        Tuple of (client, csrf_token, user_id).
    """
    client = app.test_client()
    response = client.post(
        '/api/v2/auth/register',
        json={'username': username, 'password': password}
    )
    assert response.status_code == 201, response.get_json()
    data = response.get_json()
    return client, data['csrf_token'], data['user']['id']


def _request_deletion(client, csrf_token: str, password: str = PASSWORD):
    """Send the account deletion request.

    Args:
        client: Flask test client with a session cookie.
        csrf_token: Valid CSRF token for the session.
        password: Password to confirm the request with.

    Returns:
        The response object.
    """
    return client.delete(
        '/api/v2/auth/account',
        json={'password': password},
        headers={'X-CSRF-Token': csrf_token}
    )


def _create_transaction(client, csrf_token: str) -> dict:
    """Create a transaction for the client's user via the API.

    Args:
        client: Authenticated Flask test client.
        csrf_token: Valid CSRF token for the session.

    Returns:
        The created transaction entity as returned by the API.
    """
    response = client.post(
        '/api/v2/transactions',
        json={
            'date': '2026-01-15',
            'transaction_type': 'debit',
            'original_partner': 'TEST MERCHANT',
            'amount': -42.5,
            'currency': 'EUR',
            'account': 'main',
            'category_id': 'grocery',
            'confidence': 0.9
        },
        headers={'X-CSRF-Token': csrf_token}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


class TestAccountDeletionEndpoint:
    """Tests for DELETE /api/v2/auth/account."""

    def test_requires_authentication(self, api_app):
        """Without a session cookie the request is rejected."""
        response = api_app.test_client().delete('/api/v2/auth/account')

        assert response.status_code == 401

    def test_requires_csrf_token(self, api_app):
        """A valid session without a CSRF header is rejected."""
        _register(api_app, 'alice')
        client = api_app.test_client()
        login = client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login.status_code == 200

        response = client.delete(
            '/api/v2/auth/account',
            json={'password': PASSWORD}
        )

        assert response.status_code == 403

    def test_requires_password(self, api_app):
        """A missing password is a validation error."""
        client, csrf_token, _ = _register(api_app, 'alice')

        response = client.delete(
            '/api/v2/auth/account',
            json={},
            headers={'X-CSRF-Token': csrf_token}
        )

        assert response.status_code == 400
        assert response.get_json()['code'] == 'MISSING_PASSWORD'

    def test_rejects_wrong_password(self, api_app):
        """A wrong password does not schedule the deletion."""
        client, csrf_token, _ = _register(api_app, 'alice')

        response = _request_deletion(
            client, csrf_token, password='wrong-password'
        )

        assert response.status_code == 401
        assert response.get_json()['code'] == 'INVALID_CREDENTIALS'

    def test_schedules_deletion_and_revokes_sessions(self, api_app):
        """A valid request schedules deletion and logs out."""
        client, csrf_token, _ = _register(api_app, 'alice')

        response = _request_deletion(client, csrf_token)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['message'] == 'Account deletion scheduled'
        scheduled_at = datetime.fromisoformat(
            payload['scheduled_deletion_at']
        )
        assert scheduled_at > datetime.now(UTC)

        # The session cookie is cleared and no longer valid
        me_response = client.get('/api/v2/auth/me')
        assert me_response.status_code == 401

        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            user = user_repo.find_by_username('alice')
            assert user is not None
            assert user.scheduled_deletion_at is not None


class TestAccountDeletionGracePeriod:
    """Tests for the grace period behavior."""

    def test_login_cancels_pending_deletion(self, api_app):
        """Logging in during the grace period cancels the deletion."""
        client, csrf_token, _ = _register(api_app, 'alice')
        assert _request_deletion(
            client, csrf_token
        ).status_code == 200

        login_response = client.post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )

        assert login_response.status_code == 200
        # The deletion marker is cleared; the account is intact
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            user = user_repo.find_by_username('alice')
            assert user is not None
            assert user.scheduled_deletion_at is None

    def test_login_refused_after_grace_period(self, api_app):
        """Past the scheduled timestamp login is refused."""
        _, _, user_id = _register(api_app, 'alice')
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            user_repo.schedule_deletion(
                user_id, datetime.now(UTC) - timedelta(days=1)
            )

        login_response = api_app.test_client().post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )

        assert login_response.status_code == 403
        assert login_response.get_json()['code'] == (
            'ACCOUNT_DELETION_PENDING'
        )


class TestRetentionPurge:
    """Tests for the retention purge job (flask retention-purge)."""

    def test_purge_deletes_due_account_with_data(self, api_app):
        """Accounts past the grace period are fully deleted."""
        client, csrf_token, user_id = _register(api_app, 'alice')
        _create_transaction(client, csrf_token)
        assert _request_deletion(
            client, csrf_token
        ).status_code == 200

        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            user_repo.schedule_deletion(
                user_id, datetime.now(UTC) - timedelta(days=1)
            )
            retention = api_app.extensions['retention_service']
            result = retention.purge()

        assert result['accounts_deleted'] == 1
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            assert user_repo.find_by_username('alice') is None
            transaction_repo = api_app.extensions['transaction_repository']
            assert transaction_repo.find_by_user_id(user_id) == []
        login_response = api_app.test_client().post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login_response.status_code == 401

    def test_purge_keeps_account_inside_grace_period(self, api_app):
        """Accounts still inside the grace period are untouched."""
        client, csrf_token, _ = _register(api_app, 'alice')
        assert _request_deletion(
            client, csrf_token
        ).status_code == 200

        with api_app.app_context():
            retention = api_app.extensions['retention_service']
            result = retention.purge()

        assert result['accounts_deleted'] == 0
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            assert user_repo.find_by_username('alice') is not None

    def test_purge_deletes_inactive_users_account(self, api_app):
        """Inactive users' accounts are permanently deleted."""
        client, csrf_token, user_id = _register(api_app, 'alice')
        _create_transaction(client, csrf_token)

        with api_app.app_context():
            from whatsthedamage.models.database.user import User as UserDB
            session = api_app.extensions['db_session_factory']()
            session.query(UserDB).filter(
                UserDB.id == user_id
            ).update({
                'last_login_at': datetime.now(UTC) - timedelta(days=181)
            })
            session.commit()
            session.close()

            transaction_repo = api_app.extensions['transaction_repository']
            assert transaction_repo.find_by_user_id(user_id) != []

            retention = api_app.extensions['retention_service']
            result = retention.purge()

        assert result['accounts_deleted'] == 0
        assert result['inactive_accounts_deleted'] == 1
        with api_app.app_context():
            user_repo = api_app.extensions['user_repository']
            assert user_repo.find_by_username('alice') is None
            transaction_repo = api_app.extensions['transaction_repository']
            assert transaction_repo.find_by_user_id(user_id) == []
        login_response = api_app.test_client().post(
            '/api/v2/auth/login',
            json={'username': 'alice', 'password': PASSWORD}
        )
        assert login_response.status_code == 401

    def test_cli_command_runs_purge(self, api_app):
        """The flask retention-purge CLI command executes the job."""
        from click.testing import CliRunner
        from flask.cli import ScriptInfo

        runner = CliRunner()
        result = runner.invoke(
            api_app.cli,
            ['retention-purge'],
            obj=ScriptInfo(create_app=lambda: api_app)
        )

        assert result.exit_code == 0, result.output
        assert 'Retention purge completed' in result.output

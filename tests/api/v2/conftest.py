"""Shared fixtures for functional API v2 endpoint tests.

Builds a real application backed by a temporary SQLite database and
provides authenticated test clients with valid session cookies and
CSRF tokens, mirroring the production authentication flow.
"""

import os
import tempfile
from dataclasses import dataclass
from typing import Any

import pytest
from flask import Flask


@dataclass
class AuthContext:
    """Authenticated API client context.

    Attributes:
        client: Flask test client with a valid session cookie.
        csrf_token: CSRF token issued at registration.
        user_id: Identifier of the registered user.
        username: Username of the registered user.
    """

    client: Any
    csrf_token: str
    user_id: int
    username: str

    @property
    def csrf_headers(self) -> dict[str, str]:
        """Headers required for state-changing requests."""
        return {'X-CSRF-Token': self.csrf_token}


@pytest.fixture
def api_app() -> Any:
    """Create a full application with a temporary SQLite database.

    Yields:
        Flask application with all services and blueprints registered.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test_api.db')
        previous_uri = os.environ.get('WHATSTHEDAMAGE_DATABASE_URI')
        os.environ['WHATSTHEDAMAGE_DATABASE_URI'] = f'sqlite:///{db_path}'
        try:
            from whatsthedamage.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            yield app
        finally:
            if previous_uri is None:
                os.environ.pop('WHATSTHEDAMAGE_DATABASE_URI', None)
            else:
                os.environ['WHATSTHEDAMAGE_DATABASE_URI'] = previous_uri


def csrf_token_from_response(response: Any) -> str:
    """Extract the CSRF token from a response's Set-Cookie header.

    The CSRF token is delivered as a readable cookie (not in the
    response body), mirroring what the SPA's cookie reader does.

    Args:
        response: Flask response of an endpoint that mints a CSRF
            token (register, login, getMe, /auth/csrf-token).

    Returns:
        The CSRF token value.

    Raises:
        AssertionError: When the response carries no csrf_token cookie.
    """
    for header in response.headers.getlist('Set-Cookie'):
        if header.startswith('csrf_token='):
            return header.split(';', 1)[0].split('=', 1)[1]
    raise AssertionError('No csrf_token cookie in response headers')


def register_pending(
    client: Any, username: str, password: str = 'password-123456'
) -> dict[str, Any]:
    """Phase 1 of registration: create a pending registration.

    Args:
        client: Flask test client.
        username: Username to register.
        password: Password for the new account.

    Returns:
        The pending registration payload (pending_token,
        recovery_code, expires_at).
    """
    response = client.post(
        '/api/v2/auth/register',
        json={'username': username, 'password': password}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def confirm_registration(
    client: Any, pending_token: str, recovery_code: str, **kwargs: Any
) -> Any:
    """Phase 2 of registration: confirm a pending registration.

    Args:
        client: Flask test client.
        pending_token: The pending token from phase 1.
        recovery_code: The recovery code echoed back (proof of saving).
        **kwargs: Extra keyword arguments forwarded to client.post
            (e.g. headers).

    Returns:
        The Flask response of the confirm call.
    """
    return client.post(
        '/api/v2/auth/register/confirm',
        json={'pending_token': pending_token, 'recovery_code': recovery_code},
        **kwargs
    )


def register_user(
    client: Any, username: str, password: str = 'password-123456'
) -> Any:
    """Run the full two-phase registration and return the confirm response.

    Args:
        client: Flask test client.
        username: Username to register.
        password: Password for the new account.

    Returns:
        The 200 confirm response (user + session cookies set).
    """
    pending = register_pending(client, username, password)
    response = confirm_registration(
        client, pending['pending_token'], pending['recovery_code']
    )
    assert response.status_code == 200, response.get_json()
    return response


def _register_user(
    app: Flask, username: str, password: str = 'password-123456'
) -> AuthContext:
    """Register a user and return an authenticated client context.

    Args:
        app: Flask application to create the test client from.
        username: Username to register.
        password: Password for the new account.

    Returns:
        AuthContext with the authenticated client and CSRF token.
    """
    client = app.test_client()
    response = register_user(client, username, password)
    data = response.get_json()
    return AuthContext(
        client=client,
        csrf_token=csrf_token_from_response(response),
        user_id=data['user']['id'],
        username=username
    )


@pytest.fixture
def auth_context(api_app: Flask) -> AuthContext:
    """Authenticated client for the primary test user 'alice'."""
    return _register_user(api_app, 'alice')


@pytest.fixture
def second_auth_context(api_app: Flask) -> AuthContext:
    """Authenticated client for a second user 'bob'."""
    return _register_user(api_app, 'bob')


def create_transaction(context: AuthContext, **overrides: Any) -> dict[str, Any]:
    """Create a transaction for the context user via the API.

    Args:
        context: Authenticated client context.
        **overrides: Fields overriding the default transaction payload.

    Returns:
        The created transaction entity as returned by the API.
    """
    payload: dict[str, Any] = {
        'date': '2026-01-15',
        'transaction_type': 'debit',
        'original_partner': 'TEST MERCHANT',
        'amount': -42.5,
        'currency': 'EUR',
        'account': 'main',
        'category_id': 'grocery',
        'confidence': 0.9,
    }
    payload.update(overrides)
    response = context.client.post(
        '/api/v2/transactions',
        json=payload,
        headers=context.csrf_headers
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()

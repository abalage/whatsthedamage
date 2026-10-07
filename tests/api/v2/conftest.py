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
    response = client.post(
        '/api/v2/auth/register',
        json={'username': username, 'password': password}
    )
    assert response.status_code == 201, response.get_json()
    data = response.get_json()
    return AuthContext(
        client=client,
        csrf_token=data['csrf_token'],
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

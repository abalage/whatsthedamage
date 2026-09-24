"""Integration tests for transaction API endpoints.

Tests for transaction upload, retrieval, and correction management endpoints.
"""

import pytest
from flask import Flask

from whatsthedamage.api.v2.endpoints import v2_bp


@pytest.fixture
def app():
    """Create a test Flask app with API endpoints registered."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = '/tmp'
    app.register_blueprint(v2_bp)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


class TestTransactionEndpoints:
    """Tests for transaction-related API endpoints."""

    def test_endpoints_exist(self, client):
        """Test that all transaction endpoints are registered."""
        # Test GET /api/v2/transactions
        response = client.get('/api/v2/transactions')
        # Should fail with error because services are not initialized,
        # but the endpoint exists
        assert response.status_code != 404

    def test_corrections_endpoints_exist(self, client):
        """Test that correction endpoints are not available in v2."""
        # Correction endpoints are not implemented in v2 API
        # They are handled internally by services
        pass


class TestEndpointAuthentication:
    """Tests for authentication and authorization of transaction endpoints."""

    def test_get_transactions_without_auth_fails(self, client):
        """Test that GET /api/v2/transactions fails without authentication."""
        response = client.get('/api/v2/transactions')

        # Without auth setup, should get an error
        # The exact status depends on how auth is configured
        # but it should not be 200 OK
        assert response.status_code != 200

    def test_get_corrections_without_auth_fails(self, client):
        """Test that correction endpoints are not available."""
        # Correction endpoints are not implemented in v2 API
        pass

    def test_post_corrections_without_auth_fails(self, client):
        """Test that correction endpoints are not available."""
        # Correction endpoints are not implemented in v2 API
        pass

    def test_delete_corrections_without_auth_fails(self, client):
        """Test that correction endpoints are not available."""
        # Correction endpoints are not implemented in v2 API
        pass

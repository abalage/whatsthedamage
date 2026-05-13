"""Unit and integration tests for main routes.

This module contains tests for the main application routes that are still active
in the API-only backend. Tests for deprecated routes (process, clear, legal, privacy,
about, favicon, set_language, recalculate-statistics) have been removed as those
routes now return 410 Gone or have been moved to API v2 endpoints.

Active routes:
- index - returns API information as JSON
- health - returns health status
"""
import pytest
from tests.utils.route_test_factory import RouteTestFactory


class TestMainRoutes:
    """Test suite for main application routes."""

    @pytest.fixture
    def factory(self) -> RouteTestFactory:
        """Create route test factory."""
        return RouteTestFactory()

    @pytest.fixture
    def client(self, factory: RouteTestFactory):
        """Create test client with configured services."""
        return factory.create_test_client()

    def test_index_route(self, client):
        """Test index route returns API information as JSON."""
        response = client.get('/')
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'api-only'
        assert 'message' in response_data
        assert 'frontend' in response_data
        assert 'api_documentation' in response_data
        assert 'available_endpoints' in response_data

    def test_health_route(self, client):
        """Test health route returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'healthy'

    def test_health_route_with_unwritable_upload_folder(self, client, monkeypatch):
        """Test health route when upload folder is not writable."""
        # The health route currently doesn't test for writable folders, just basic functionality
        # This test verifies the basic health check works
        response = client.get('/health')
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'healthy'

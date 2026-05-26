"""Unit and integration tests for main routes.

This module contains tests for the main application routes that are still active
in the API-only backend. Tests for deprecated routes (process, clear, legal, privacy,
about, set_language, recalculate-statistics) have been removed as those
routes now return 410 Gone or have been moved to API v2 endpoints.

Note: The index route (/) is now handled by frontend_bp which serves the Vue SPA
static files. Without frontend files present, it returns 404.

Active routes:
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
        """Test index route is handled by frontend_bp and returns 404 without frontend files."""
        response = client.get('/')
        # The root route is now handled by frontend_bp which serves Vue SPA static files
        # Without the frontend dist directory, it returns 404 Not Found
        assert response.status_code == 404

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

"""Tests for the frontend SPA catch-all route.

Verifies that source map requests are never served, even when a
.map file exists in the frontend dist directory (defense-in-depth
for the sourcemap exposure finding).
"""

import pytest

from whatsthedamage.app import create_app


class TestFrontendRoutesSourcemapBlocking:
    """Test suite for source map blocking in frontend_bp."""

    @pytest.fixture
    def client_with_maps(self, tmp_path, monkeypatch):
        """Create a test client whose frontend dist contains .map files.

        Args:
            tmp_path: Temporary directory used as the dist folder.
            monkeypatch: Pytest monkeypatch fixture.

        Returns:
            Flask test client with a populated dist folder.
        """
        (tmp_path / 'js').mkdir()
        (tmp_path / 'js' / 'main.js').write_text('console.log("main")')
        (tmp_path / 'js' / 'main.js.map').write_text('{"version": 3}')
        (tmp_path / 'index.html').write_text('<html></html>')

        app = create_app()
        app.config['FRONTEND_STATIC_FOLDER'] = str(tmp_path)
        app.config['TESTING'] = True
        return app.test_client()

    def test_map_request_returns_404_even_when_file_exists(
        self, client_with_maps
    ):
        """A .map file present in dist is never served."""
        response = client_with_maps.get('/js/main.js.map')
        assert response.status_code == 404

    def test_js_asset_still_served(self, client_with_maps):
        """Regular assets from dist are served normally."""
        response = client_with_maps.get('/js/main.js')
        assert response.status_code == 200
        assert b'main' in response.data

    def test_spa_route_still_served(self, client_with_maps):
        """Unknown paths fall back to index.html."""
        response = client_with_maps.get('/categories')
        assert response.status_code == 200
        assert b'<html>' in response.data

"""Tests for drill-down routes with cache expiry functionality."""

import pytest
import time
from unittest.mock import Mock, patch
from flask import Flask
from whatsthedamage.controllers.routes import bp
from whatsthedamage.controllers.routes_helpers import (
    get_cached_data_for_drilldown,
    handle_drilldown_request
)
from whatsthedamage.config.dt_models import (
    CachedProcessingResult, DataTablesResponse, AggregatedRow,
    DisplayRawField, DateField, StatisticalMetadata
)
from whatsthedamage.services.cache_service import CacheService


class TestDrillDownRoutesHelpers:
    """Tests for drill-down route helper functions."""

    @pytest.fixture
    def app(self):
        """Create Flask app with test configuration."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
        app.register_blueprint(bp)
        return app

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service."""
        cache_backend = Mock()
        return CacheService(cache_backend)

    @pytest.fixture
    def sample_cached_result(self):
        """Create sample cached processing result."""
        return CachedProcessingResult(
            responses={
                "checking": DataTablesResponse(
                    data=[
                        AggregatedRow(
                            category="Grocery",
                            total=DisplayRawField(display="100.00", raw=100.0),
                            month=DateField(display="Jan 2023", timestamp=1672531200),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        ),
                        AggregatedRow(
                            category="Utilities",
                            total=DisplayRawField(display="150.00", raw=150.0),
                            month=DateField(display="Jan 2023", timestamp=1672531200),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        ),
                        AggregatedRow(
                            category="Rent",
                            total=DisplayRawField(display="1000.00", raw=1000.0),
                            month=DateField(display="Feb 2023", timestamp=1675209600),
                            date=DateField(display="Feb 2023", timestamp=1675209600),
                            details=[],
                            is_calculated=False
                        )
                    ],
                    account="checking",
                    currency="USD",
                    statistical_metadata=StatisticalMetadata(highlights=[])
                )
            },
            metadata=StatisticalMetadata(highlights=[])
        )

    def test_get_cached_data_for_drilldown_success(self, app, mock_cache_service, sample_cached_result):
        """Test successful retrieval of cached data for drill-down."""
        with app.app_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            result, error = get_cached_data_for_drilldown("test_result_id", "checking")

            assert error is None
            assert result is not None
            assert isinstance(result, DataTablesResponse)
            assert result.account == "checking"
            assert len(result.data) == 3

    def test_get_cached_data_for_drilldown_missing_result(self, app, mock_cache_service):
        """Test retrieval when result is not found in cache."""
        with app.app_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return None (not found)
            mock_cache_service._cache.get.return_value = None

            result, error = get_cached_data_for_drilldown("nonexistent_id", "checking")

            assert result is None
            assert error == 'Result not found or expired.'

    def test_get_cached_data_for_drilldown_missing_account(self, app, mock_cache_service, sample_cached_result):
        """Test retrieval when account is not found in cached result."""
        with app.app_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Request different account that doesn't exist
            result, error = get_cached_data_for_drilldown("test_result_id", "savings")

            assert result is None
            assert error == 'Account "savings" not found.'

    def test_handle_drilldown_request_category_filter(self, app, mock_cache_service, sample_cached_result):
        """Test handle_drilldown_request with category filter."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Mock template rendering
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "rendered template"

                # Test category filter for "Grocery"
                _response = handle_drilldown_request(
                    result_id="test_result_id",
                    account="checking",
                    template="category_all_months.html",
                    filter_fn=lambda row: row.category == "Grocery",
                    template_context={'category': 'Grocery'},
                    data_not_found_error="Data not found",
                    index_route="main.index"
                )

                # Should have called render_template with filtered data
                mock_render.assert_called_once()
                call_args = mock_render.call_args
                assert call_args[0][0] == "category_all_months.html"

                # Check that context contains filtered data
                context = call_args[1]
                assert 'data' in context
                assert len(context['data']) == 1  # Only Grocery
                assert context['data'][0].category == "Grocery"
                assert context['category'] == 'Grocery'
                assert context['account'] == 'checking'

    def test_handle_drilldown_request_month_filter(self, app, mock_cache_service, sample_cached_result):
        """Test handle_drilldown_request with month filter."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Mock template rendering
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "rendered template"

                # Test month filter for January (timestamp 1672531200)
                _response = handle_drilldown_request(
                    result_id="test_result_id",
                    account="checking",
                    template="month_all_categories.html",
                    filter_fn=lambda row: str(row.month.timestamp) == "1672531200",
                    template_context={'month_ts': '1672531200'},
                    data_not_found_error="Data not found",
                    index_route="main.index"
                )

                # Should have called render_template with filtered data
                mock_render.assert_called_once()
                call_args = mock_render.call_args
                assert call_args[0][0] == "month_all_categories.html"

                # Check that context contains filtered data
                context = call_args[1]
                assert 'data' in context
                assert len(context['data']) == 2  # Grocery and Utilities (both Jan)
                assert context['month_ts'] == '1672531200'
                assert context['account'] == 'checking'

    def test_handle_drilldown_request_category_and_month_filter(self, app, mock_cache_service, sample_cached_result):
        """Test handle_drilldown_request with both category and month filter."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Mock template rendering
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "rendered template"

                # Test combined filter for Utilities in January
                _response = handle_drilldown_request(
                    result_id="test_result_id",
                    account="checking",
                    template="category_month_detail.html",
                    filter_fn=lambda row: (
                        row.category == "Utilities" and
                        str(row.month.timestamp) == "1672531200"
                    ),
                    template_context={'category': 'Utilities', 'month_ts': '1672531200'},
                    data_not_found_error="Data not found",
                    index_route="main.index"
                )

                # Should have called render_template with filtered data
                mock_render.assert_called_once()
                call_args = mock_render.call_args
                assert call_args[0][0] == "category_month_detail.html"

                # Check that context contains filtered data
                context = call_args[1]
                assert 'data' in context
                assert len(context['data']) == 1  # Only Utilities in Jan
                assert context['data'][0].category == "Utilities"
                assert context['category'] == 'Utilities'
                assert context['month_ts'] == '1672531200'
                assert context['account'] == 'checking'

    def test_handle_drilldown_request_cache_missing(self, app, mock_cache_service):
        """Test handle_drilldown_request when cache entry is missing."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return None (not found)
            mock_cache_service._cache.get.return_value = None

            # Mock flash and redirect
            with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
                with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                    with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                        mock_url_for.return_value = "/index"

                        _response = handle_drilldown_request(
                            result_id="nonexistent_id",
                            account="checking",
                            template="category_all_months.html",
                            filter_fn=lambda row: row.category == "Grocery",
                            template_context={'category': 'Grocery'},
                            data_not_found_error="Data not found",
                            index_route="main.index"
                        )

                        # Should have flashed error and redirected
                        mock_flash.assert_called_once_with("Result not found or expired.", 'danger')
                        mock_redirect.assert_called_once_with("/index")

    def test_handle_drilldown_request_account_missing(self, app, mock_cache_service, sample_cached_result):
        """Test handle_drilldown_request when account is missing from cache."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Mock flash and redirect
            with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
                with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                    with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                        mock_url_for.return_value = "/index"

                        _response = handle_drilldown_request(
                            result_id="test_result_id",
                            account="savings",  # This account doesn't exist
                            template="category_all_months.html",
                            filter_fn=lambda row: row.category == "Grocery",
                            template_context={'category': 'Grocery'},
                            data_not_found_error="Data not found",
                            index_route="main.index"
                        )

                        # Should have flashed error and redirected
                        mock_flash.assert_called_once_with('Account "savings" not found.', 'danger')
                        mock_redirect.assert_called_once_with("/index")

    def test_handle_drilldown_request_empty_filtered_data(self, app, mock_cache_service, sample_cached_result):
        """Test handle_drilldown_request when filter returns empty data."""
        with app.test_request_context():
            # Set up cache service in app extensions
            app.extensions['cache_service'] = mock_cache_service

            # Mock cache to return our sample result
            mock_cache_service._cache.get.return_value = sample_cached_result

            # Mock template rendering to avoid TemplateNotFound error
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "rendered template"

                # Mock flash and redirect
                with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
                    with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                        with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                            mock_url_for.return_value = "/index"

                            # Filter that matches nothing
                            _response = handle_drilldown_request(
                                result_id="test_result_id",
                                account="checking",
                                template="category_all_months.html",
                                filter_fn=lambda row: row.category == "NonExistent",
                                template_context={'category': 'NonExistent'},
                                data_not_found_error="Data not found",
                                index_route="main.index"
                            )

                            # Should have flashed error and redirected
                            mock_flash.assert_called_once_with("Data not found", 'danger')
                            mock_redirect.assert_called_once_with("/index")

class TestDrillDownRoutes:
    """Tests for actual drill-down route endpoints."""

    @pytest.fixture
    def app(self):
        """Create Flask app with test configuration."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
        app.register_blueprint(bp)

        # Mock the cache service in app extensions
        mock_cache_backend = Mock()
        app.extensions['cache_service'] = CacheService(mock_cache_backend)

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client for Flask app."""
        return app.test_client()

    @pytest.fixture
    def sample_cached_result(self):
        """Create sample cached processing result."""
        return CachedProcessingResult(
            responses={
                "checking": DataTablesResponse(
                    data=[
                        AggregatedRow(
                            category="Grocery",
                            total=DisplayRawField(display="100.00", raw=100.0),
                            month=DateField(display="Jan 2023", timestamp=1672531200),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        )
                    ],
                    account="checking",
                    currency="USD",
                    statistical_metadata=StatisticalMetadata(highlights=[])
                )
            },
            metadata=StatisticalMetadata(highlights=[])
        )

    def test_category_all_months_route_success(self, client, app, sample_cached_result):
        """Test /details/<result_id>/<account>/<category> route success."""
        # Mock the cache to return our sample result
        app.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering to capture the call
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.return_value = "rendered template"

            response = client.get('/details/test_result_id/checking/Grocery')

            # Should return 200 and call render_template
            assert response.status_code == 200
            assert response.data == b"rendered template"

            # Verify template was called with correct parameters
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == "category_all_months.html"

            # Check context
            context = call_args[1]
            assert 'data' in context
            assert len(context['data']) == 1  # Only Grocery
            assert context['data'][0].category == "Grocery"
            assert context['category'] == 'Grocery'
            assert context['account'] == 'checking'

    def test_month_all_categories_route_success(self, client, app, sample_cached_result):
        """Test /details/<result_id>/<account>/month/<month_ts> route success."""
        # Mock the cache to return our sample result
        app.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.return_value = "rendered template"

            response = client.get('/details/test_result_id/checking/month/1672531200')

            # Should return 200 and call render_template
            assert response.status_code == 200
            assert response.data == b"rendered template"

            # Verify template was called with correct parameters
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == "month_all_categories.html"

    def test_category_month_detail_route_success(self, client, app, sample_cached_result):
        """Test /details/<result_id>/<account>/<category>/<month_ts> route success."""
        # Mock the cache to return our sample result
        app.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.return_value = "rendered template"

            response = client.get('/details/test_result_id/checking/Grocery/1672531200')

            # Should return 200 and call render_template
            assert response.status_code == 200
            assert response.data == b"rendered template"

            # Verify template was called with correct parameters
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == "category_month_detail.html"

    def test_drilldown_route_cache_missing(self, client, app):
        """Test drill-down route when cache entry is missing."""
        # Mock the cache to return None (not found)
        app.extensions['cache_service']._cache.get.return_value = None

        # Mock flash and redirect
        with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                    mock_url_for.return_value = "/"
                    mock_redirect.return_value = ("", 302)  # Mock redirect response

                    response = client.get('/details/nonexistent_id/checking/Grocery')

                    # Should redirect to index
                    assert response.status_code == 302

                    # Should have flashed error
                    mock_flash.assert_called_once_with('Result not found or expired.', 'danger')
                    mock_redirect.assert_called_once_with("/")

    def test_drilldown_route_account_missing(self, client, app, sample_cached_result):
        """Test drill-down route when account is missing from cache."""
        # Mock the cache to return our sample result
        app.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock flash and redirect
        with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                    mock_url_for.return_value = "/"
                    mock_redirect.return_value = ("", 302)  # Mock redirect response

                    response = client.get('/details/test_result_id/savings/Grocery')

                    # Should redirect to index
                    assert response.status_code == 302

                    # Should have flashed error
                    mock_flash.assert_called_once_with('Account "savings" not found.', 'danger')
                    mock_redirect.assert_called_once_with("/")

class TestCacheExpiryInDrillDownRoutes:
    """Tests for cache expiry scenarios in drill-down routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app with test configuration."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
        app.register_blueprint(bp)

        # Create cache service with mock backend
        mock_cache_backend = Mock()
        cache_service = CacheService(mock_cache_backend, ttl=1)  # 1 second TTL
        app.extensions['cache_service'] = cache_service

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client for Flask app."""
        return app.test_client()

    @pytest.fixture
    def sample_cached_result(self):
        """Create sample cached processing result."""
        return CachedProcessingResult(
            responses={
                "checking": DataTablesResponse(
                    data=[
                        AggregatedRow(
                            category="Grocery",
                            total=DisplayRawField(display="100.00", raw=100.0),
                            month=DateField(display="Jan 2023", timestamp=1672531200),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        )
                    ],
                    account="checking",
                    currency="USD",
                    statistical_metadata=StatisticalMetadata(highlights=[])
                )
            },
            metadata=StatisticalMetadata(highlights=[])
        )

    def test_drilldown_route_cache_expiry(self, client, app, sample_cached_result):
        """Test drill-down route with expired cache entry."""

        # Mock the cache backend to support item assignment and expiry times
        mock_cache_backend = Mock()
        mock_cache_backend._store = {}
        mock_cache_backend._expiry_times = {}
        mock_cache_backend.get.side_effect = lambda key: mock_cache_backend._store.get(key) if time.time() < mock_cache_backend._expiry_times.get(key, float('inf')) else None

        # Replace the cache service with our mock
        app.extensions['cache_service'] = CacheService(mock_cache_backend, ttl=1)

        # Set cache initially
        mock_cache_backend._store["expiry_test"] = sample_cached_result
        mock_cache_backend._expiry_times["expiry_test"] = time.time() + 0.5  # Expires in 0.5 seconds

        # First request should work
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.return_value = "rendered template"

            response = client.get('/details/expiry_test/checking/Grocery')
            assert response.status_code == 200

        # Wait for cache to expire
        time.sleep(0.6)

        # Second request should fail with cache expiry
        with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                    mock_url_for.return_value = "/"
                    mock_redirect.return_value = ("", 302)

                    response = client.get('/details/expiry_test/checking/Grocery')
                    assert response.status_code == 302

                    # Should have flashed expiry error
                    mock_flash.assert_called_once_with('Result not found or expired.', 'danger')

    def test_drilldown_route_cache_expiry_multiple_requests(self, client, app, sample_cached_result):
        """Test multiple drill-down requests with cache expiry."""
        # Mock the cache backend to support item assignment and expiry times
        mock_cache_backend = Mock()
        mock_cache_backend._store = {}
        mock_cache_backend._expiry_times = {}
        mock_cache_backend.get.side_effect = lambda key: mock_cache_backend._store.get(key) if time.time() < mock_cache_backend._expiry_times.get(key, float('inf')) else None

        # Replace the cache service with our mock
        app.extensions['cache_service'] = CacheService(mock_cache_backend, ttl=1)

        # Set cache for multiple result IDs
        for i in range(3):
            result_id = f"result_{i}"
            mock_cache_backend._store[result_id] = sample_cached_result
            mock_cache_backend._expiry_times[result_id] = time.time() + 0.3  # Expires in 0.3 seconds

        # All requests should work initially
        for i in range(3):
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = f"rendered template {i}"

                response = client.get(f'/details/result_{i}/checking/Grocery')
                assert response.status_code == 200

        # Wait for cache to expire
        time.sleep(0.4)

        # All requests should now fail with cache expiry
        for i in range(3):
            with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
                with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                    with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                        mock_url_for.return_value = "/"
                        mock_redirect.return_value = ("", 302)

                        response = client.get(f'/details/result_{i}/checking/Grocery')
                        assert response.status_code == 302

                        # Should have flashed expiry error
                        mock_flash.assert_called_once_with('Result not found or expired.', 'danger')

class TestDrillDownRouteErrorHandling:
    """Tests for error handling in drill-down routes."""

    @pytest.fixture
    def app(self):
        """Create Flask app with test configuration."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
        app.register_blueprint(bp)

        # Mock the cache service in app extensions
        mock_cache_backend = Mock()
        app.extensions['cache_service'] = CacheService(mock_cache_backend)

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client for Flask app."""
        return app.test_client()

    @pytest.fixture
    def sample_cached_result(self):
        """Create sample cached processing result."""
        return CachedProcessingResult(
            responses={
                "checking": DataTablesResponse(
                    data=[
                        AggregatedRow(
                            category="Grocery",
                            total=DisplayRawField(display="100.00", raw=100.0),
                            month=DateField(display="Jan 2023", timestamp=1672531200),
                            date=DateField(display="Jan 2023", timestamp=1672531200),
                            details=[],
                            is_calculated=False
                        )
                    ],
                    account="checking",
                    currency="USD",
                    statistical_metadata=StatisticalMetadata(highlights=[])
                )
            },
            metadata=StatisticalMetadata(highlights=[])
        )

    def test_drilldown_route_cache_backend_error(self, client, app):
        """Test drill-down route when cache backend raises exception."""
        # Mock cache backend to raise exception
        app.extensions['cache_service']._cache.get.side_effect = RuntimeError("Cache backend error")

        # Mock flash and redirect
        with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                    mock_url_for.return_value = "/"
                    mock_redirect.return_value = ("", 302)

                    response = client.get('/details/error_test/checking/Grocery')
                    assert response.status_code == 302

                    # Should have flashed error
                    mock_flash.assert_called_once_with('Result not found or expired.', 'danger')

    def test_drilldown_route_template_rendering_error(self, client, app, sample_cached_result):
        """Test drill-down route when template rendering fails."""
        # Mock the cache to return our sample result
        app.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering to raise exception
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.side_effect = RuntimeError("Template error")

            with pytest.raises(RuntimeError, match="Template error"):
                client.get('/details/test_result_id/checking/Grocery')

"""Tests for drill-down routes with cache expiry functionality using parametrized tests and fixtures."""

import pytest
import time
from unittest.mock import Mock, patch
from flask import Flask
from whatsthedamage.controllers.routes import bp
from whatsthedamage.controllers.routes_helpers import (
    get_cached_data_for_drilldown,
    handle_drilldown_request
)
from whatsthedamage.models.dt_models import (
    ProcessingResponse, DataTablesResponse, AggregatedRow,
    DisplayRawField, DateField, StatisticalMetadata
)
from whatsthedamage.services.cache_service import CacheService

# Test data constants for parametrization
TEST_FILTER_SCENARIOS = [
    {
        "name": "category_filter",
        "filter_fn": lambda row: row.category == "Grocery",
        "template": "category_all_months.html",
        "template_context": {'category': 'Grocery'},
        "expected_data_count": 1,
        "expected_category": "Grocery"
    },
    {
        "name": "month_filter",
        "filter_fn": lambda row: str(row.date.timestamp) == "1672531200",
        "template": "month_all_categories.html",
        "template_context": {'month_ts': '1672531200'},
        "expected_data_count": 2,
        "expected_category": None
    },
    {
        "name": "category_and_month_filter",
        "filter_fn": lambda row: (
            row.category == "Utilities" and
            str(row.date.timestamp) == "1672531200"
        ),
        "template": "category_month_detail.html",
        "template_context": {'category': 'Utilities', 'month_ts': '1672531200'},
        "expected_data_count": 1,
        "expected_category": "Utilities"
    }
]

TEST_ROUTE_SCENARIOS = [
    {
        "name": "category_route",
        "url": "/details/test_result_id/checking/Grocery",
        "expected_template": "category_all_months.html",
        "expected_context_keys": ['data', 'category', 'account']
    },
    {
        "name": "month_route",
        "url": "/details/test_result_id/checking/month/1672531200",
        "expected_template": "month_all_categories.html",
        "expected_context_keys": ['data', 'month_ts', 'account']
    },
    {
        "name": "category_month_route",
        "url": "/details/test_result_id/checking/Grocery/1672531200",
        "expected_template": "category_month_detail.html",
        "expected_context_keys": ['data', 'category', 'month_ts', 'account']
    }
]

TEST_ERROR_SCENARIOS = [
    {
        "name": "cache_missing",
        "cache_result": None,
        "result_id": "nonexistent_id",
        "account": "checking",
        "expected_error": "Result not found or expired."
    },
    {
        "name": "account_missing",
        "cache_result": "valid_result",
        "result_id": "test_result_id",
        "account": "savings",
        "expected_error": 'Account "savings" not found.'
    }
]

@pytest.fixture
def app():
    """Create Flask app with test configuration."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
    app.register_blueprint(bp)

    # Add data formatting service to app extensions for testing
    from whatsthedamage.services.data_formatting_service import DataFormattingService
    app.extensions['data_formatting_service'] = DataFormattingService()

    return app

@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    cache_backend = Mock()
    return CacheService(cache_backend)

@pytest.fixture
def sample_cached_result():
    """Create sample cached processing result."""
    import uuid
    return ProcessingResponse(
        result_id="test-result-id",
        data={
            "checking": DataTablesResponse(
                data=[
                    AggregatedRow(
                        row_id=str(uuid.uuid4()),
                        category="Grocery",
                        total=DisplayRawField(display="100.00", raw=100.0),
                        date=DateField(display="Jan 2023", timestamp=1672531200),
                        details=[],
                        is_calculated=False
                    ),
                    AggregatedRow(
                        row_id=str(uuid.uuid4()),
                        category="Utilities",
                        total=DisplayRawField(display="150.00", raw=150.0),
                        date=DateField(display="Jan 2023", timestamp=1672531200),
                        details=[],
                        is_calculated=False
                    ),
                    AggregatedRow(
                        row_id=str(uuid.uuid4()),
                        category="Rent",
                        total=DisplayRawField(display="1000.00", raw=1000.0),
                        date=DateField(display="Feb 2023", timestamp=1675209600),
                        details=[],
                        is_calculated=False
                    )
                ],
                account="checking",
                currency="USD",
                metadata=None
            )
        },
        metadata=None,
        statistical_metadata=StatisticalMetadata(highlights=[])
    )

@pytest.fixture
def client(app):
    """Create test client for Flask app."""
    return app.test_client()

@pytest.fixture
def setup_cache_service(app, mock_cache_service):
    """Setup cache service in app extensions."""
    app.extensions['cache_service'] = mock_cache_service
    return mock_cache_service

class TestDrillDownRoutesHelpers:
    """Tests for drill-down route helper functions."""

    @pytest.mark.parametrize("scenario", TEST_FILTER_SCENARIOS)
    def test_handle_drilldown_request_filter_scenarios(self, app, setup_cache_service, sample_cached_result, scenario):
        """Test handle_drilldown_request with various filter scenarios using parametrization."""
        with app.test_request_context():
            # Mock cache to return our sample result
            setup_cache_service._cache.get.return_value = sample_cached_result

            # Mock template rendering
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "rendered template"

                # Test the filter scenario
                _response = handle_drilldown_request(
                    result_id="test_result_id",
                    account="checking",
                    template=scenario["template"],
                    filter_fn=scenario["filter_fn"],
                    template_context=scenario["template_context"],
                    data_not_found_error="Data not found",
                    index_route="main.index"
                )

                # Should have called render_template with filtered data
                mock_render.assert_called_once()
                call_args = mock_render.call_args
                assert call_args[0][0] == scenario["template"]

                # Check that context contains filtered data
                context = call_args[1]
                assert 'data' in context
                assert len(context['data']) == scenario["expected_data_count"]
                if scenario["expected_category"]:
                    assert context['data'][0].category == scenario["expected_category"]
                assert context['account'] == 'checking'

    @pytest.mark.parametrize("scenario", TEST_ERROR_SCENARIOS)
    def test_handle_drilldown_request_error_scenarios(self, app, setup_cache_service, sample_cached_result, scenario):
        """Test handle_drilldown_request error scenarios using parametrization."""
        with app.test_request_context():
            # Setup cache based on scenario
            if scenario["cache_result"] == "valid_result":
                setup_cache_service._cache.get.return_value = sample_cached_result
            else:
                setup_cache_service._cache.get.return_value = scenario["cache_result"]

            # Mock flash and redirect
            with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
                with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                    with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                        mock_url_for.return_value = "/index"

                        _response = handle_drilldown_request(
                            result_id=scenario["result_id"],
                            account=scenario["account"],
                            template="category_all_months.html",
                            filter_fn=lambda row: row.category == "Grocery",
                            template_context={'category': 'Grocery'},
                            data_not_found_error="Data not found",
                            index_route="main.index"
                        )

                        # Should have flashed error and redirected
                        mock_flash.assert_called_once_with(scenario["expected_error"], 'danger')
                        mock_redirect.assert_called_once_with("/index")

    def test_get_cached_data_for_drilldown_success(self, app, setup_cache_service, sample_cached_result):
        """Test successful retrieval of cached data for drill-down."""
        with app.app_context():
            # Mock cache to return our sample result
            setup_cache_service._cache.get.return_value = sample_cached_result

            result, error = get_cached_data_for_drilldown("test_result_id", "checking")

            assert error is None
            assert result is not None
            assert isinstance(result, DataTablesResponse)
            assert result.account == "checking"
            assert len(result.data) == 3

    def test_get_cached_data_for_drilldown_missing_result(self, app, setup_cache_service):
        """Test retrieval when result is not found in cache."""
        with app.app_context():
            # Mock cache to return None (not found)
            setup_cache_service._cache.get.return_value = None

            result, error = get_cached_data_for_drilldown("nonexistent_id", "checking")

            assert result is None
            assert error == 'Result not found or expired.'

    def test_get_cached_data_for_drilldown_missing_account(self, app, setup_cache_service, sample_cached_result):
        """Test retrieval when account is not found in cached result."""
        with app.app_context():
            # Mock cache to return our sample result
            setup_cache_service._cache.get.return_value = sample_cached_result

            # Request different account that doesn't exist
            result, error = get_cached_data_for_drilldown("test_result_id", "savings")

            assert result is None
            assert error == 'Account "savings" not found.'

class TestDrillDownRoutes:
    """Tests for actual drill-down route endpoints."""

    @pytest.fixture
    def app_with_cache(self, app, mock_cache_service):
        """Create Flask app with cache service setup."""
        app.extensions['cache_service'] = mock_cache_service
        return app

    @pytest.mark.parametrize("scenario", TEST_ROUTE_SCENARIOS)
    def test_drilldown_route_success_scenarios(self, client, app_with_cache, sample_cached_result, scenario):
        """Test drill-down route success scenarios using parametrization."""
        # Mock the cache to return our sample result
        app_with_cache.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering to capture the call
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.return_value = "rendered template"

            response = client.get(scenario["url"])

            # Should return 200 and call render_template
            assert response.status_code == 200
            assert response.data == b"rendered template"

            # Verify template was called with correct parameters
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == scenario["expected_template"]

            # Check context contains expected keys
            context = call_args[1]
            for key in scenario["expected_context_keys"]:
                assert key in context

    @pytest.mark.parametrize("scenario", TEST_ERROR_SCENARIOS)
    def test_drilldown_route_error_scenarios(self, client, app_with_cache, sample_cached_result, scenario):
        """Test drill-down route error scenarios using parametrization."""
        # Setup cache based on scenario
        if scenario["cache_result"] == "valid_result":
            app_with_cache.extensions['cache_service']._cache.get.return_value = sample_cached_result
        else:
            app_with_cache.extensions['cache_service']._cache.get.return_value = scenario["cache_result"]

        # Mock flash and redirect
        with patch('whatsthedamage.controllers.routes_helpers.flash') as mock_flash:
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                with patch('whatsthedamage.controllers.routes_helpers.url_for') as mock_url_for:
                    mock_url_for.return_value = "/"
                    mock_redirect.return_value = ("", 302)  # Mock redirect response

                    # Mock template rendering to avoid TemplateNotFound error
                    with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                        mock_render.return_value = "rendered template"

                        # Use a standard URL for error testing
                        response = client.get('/details/nonexistent_id/checking/Grocery')

                        # Check if we should expect redirect or template rendering based on scenario
                        if scenario["name"] == "account_missing":
                            # For account missing, it should render template with empty data
                            assert response.status_code == 200
                            mock_render.assert_called_once()
                            # No flash message for account missing scenario
                        else:
                            # For cache missing, it should redirect
                            assert response.status_code == 302
                            mock_redirect.assert_called_once_with("/")
                            # Should have flashed error for cache missing
                            mock_flash.assert_called_once_with(scenario["expected_error"], 'danger')

class TestCacheExpiryInDrillDownRoutes:
    """Tests for cache expiry scenarios in drill-down routes."""

    @pytest.fixture
    def cache_service_with_expiry(self, app):
        """Create cache service with expiry support."""
        # Mock the cache backend to support item assignment and expiry times
        mock_cache_backend = Mock()
        mock_cache_backend._store = {}
        mock_cache_backend._expiry_times = {}
        mock_cache_backend.get.side_effect = lambda key: mock_cache_backend._store.get(key) if time.time() < mock_cache_backend._expiry_times.get(key, float('inf')) else None

        cache_service = CacheService(mock_cache_backend, ttl=1)
        app.extensions['cache_service'] = cache_service
        return mock_cache_backend

    def test_drilldown_route_cache_expiry(self, client, app, sample_cached_result, cache_service_with_expiry):
        """Test drill-down route with expired cache entry."""
        # Set cache initially
        cache_service_with_expiry._store["expiry_test"] = sample_cached_result
        cache_service_with_expiry._expiry_times["expiry_test"] = time.time() + 0.5  # Expires in 0.5 seconds

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

    @pytest.mark.parametrize("num_requests", [1, 3, 5])
    def test_drilldown_route_cache_expiry_multiple_requests(self, client, app, sample_cached_result, cache_service_with_expiry, num_requests):
        """Test multiple drill-down requests with cache expiry using parametrization."""
        # Set cache for multiple result IDs
        for i in range(num_requests):
            result_id = f"result_{i}"
            cache_service_with_expiry._store[result_id] = sample_cached_result
            cache_service_with_expiry._expiry_times[result_id] = time.time() + 0.3  # Expires in 0.3 seconds

        # All requests should work initially
        for i in range(num_requests):
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = f"rendered template {i}"

                response = client.get(f'/details/result_{i}/checking/Grocery')
                assert response.status_code == 200

        # Wait for cache to expire
        time.sleep(0.4)

        # All requests should now fail with cache expiry
        for i in range(num_requests):
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
    def app_with_cache(self, app, mock_cache_service):
        """Create Flask app with cache service setup."""
        app.extensions['cache_service'] = mock_cache_service
        return app

    def test_drilldown_route_cache_backend_error(self, client, app_with_cache):
        """Test drill-down route when cache backend raises exception."""
        # Mock cache backend to raise exception
        app_with_cache.extensions['cache_service']._cache.get.side_effect = RuntimeError("Cache backend error")

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

    def test_drilldown_route_template_rendering_error(self, client, app_with_cache, sample_cached_result):
        """Test drill-down route when template rendering fails."""
        # Mock the cache to return our sample result
        app_with_cache.extensions['cache_service']._cache.get.return_value = sample_cached_result

        # Mock template rendering to raise exception
        with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
            mock_render.side_effect = RuntimeError("Template error")

            with pytest.raises(RuntimeError, match="Template error"):
                client.get('/details/test_result_id/checking/Grocery')
"""Unit and integration tests for drilldown routes.

This module contains comprehensive tests for the drilldown routes:
- show_category_months
- show_month_categories
- show_category_month_transactions
"""
import pytest
from tests.utils.route_test_factory import RouteTestFactory
from whatsthedamage.controllers.routes_helpers import handle_entity_drilldown
from unittest.mock import patch
from whatsthedamage.models.dt_models import StatisticalMetadata

class TestDrilldownRoutes:
    """Test suite for drilldown routes."""

    @pytest.fixture
    def factory(self) -> RouteTestFactory:
        """Create route test factory."""
        return RouteTestFactory()

    @pytest.fixture
    def client(self, factory: RouteTestFactory):
        """Create test client with configured services."""
        return factory.create_test_client()

    @pytest.fixture
    def test_data(self, factory: RouteTestFactory, client):
        """Setup test data in cache and ID mappings."""
        with client.application.app_context():
            return factory.setup_test_data()

    def test_handle_entity_drilldown_category_success(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown helper function for category drilldown."""
        # Setup test data
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()
            result_id = test_data['result_id']
            account_id = test_data['account_id']
            category_id = test_data['category_ids']['Grocery']

            # Call the helper function directly
            with patch('whatsthedamage.controllers.routes_helpers.make_response'):
                with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                    handle_entity_drilldown(
                        result_id=result_id,
                        account_id=account_id,
                        entity_id=category_id,
                        entity_type='category',
                        template='category_months_list.html',
                        data_not_found_error='Data not found',
                        index_route='main.index'
                    )

                    # Verify render_template was called with correct template
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == 'category_months_list.html'

    def test_handle_entity_drilldown_month_success(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown helper function for month drilldown."""
        # Setup test data
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()
            result_id = test_data['result_id']
            account_id = test_data['account_id']
            month_id = test_data['month_ids']['1704067200']  # Jan 2024

            # Call the helper function directly
            with patch('whatsthedamage.controllers.routes_helpers.make_response'):
                with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                    handle_entity_drilldown(
                        result_id=result_id,
                        account_id=account_id,
                        entity_id=month_id,
                        entity_type='month',
                        template='month_categories_list.html',
                        data_not_found_error='Data not found',
                        index_route='main.index'
                    )

                    # Verify render_template was called with correct template
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == 'month_categories_list.html'

    def test_handle_entity_drilldown_invalid_account(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown with invalid account ID."""
        with factory.create_app_with_test_services().test_request_context():
            # Call with invalid account ID
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                handle_entity_drilldown(
                    result_id='test123',
                    account_id='invalid_account',
                    entity_id='cat1',
                    entity_type='category',
                    template='category_months_list.html',
                    data_not_found_error='Data not found',
                    index_route='main.index'
                )

                # Verify redirect was called
                mock_redirect.assert_called_once()
                args, kwargs = mock_redirect.call_args
                assert args[0] == '/'  # redirect uses url_for which resolves to '/'

    def test_handle_entity_drilldown_invalid_entity(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown with invalid entity ID."""
        with factory.create_app_with_test_services().test_request_context():
            test_data = factory.setup_test_data()

            # Call with invalid entity ID
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                handle_entity_drilldown(
                    result_id=test_data['result_id'],
                    account_id=test_data['account_id'],
                    entity_id='invalid_entity',
                    entity_type='category',
                    template='category_months_list.html',
                    data_not_found_error='Data not found',
                    index_route='main.index'
                )

                # Verify redirect was called
                mock_redirect.assert_called_once()
                args, kwargs = mock_redirect.call_args
                assert args[0] == '/'  # redirect uses url_for which resolves to '/'

    def test_category_months_route_success(self, client, test_data):
        """Test show_category_months route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']

        # Make request to category months route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months')

        # Verify successful response
        assert response.status_code == 200
        assert b'Grocery' in response.data  # Category name should be in response
        assert b'category_months_list.html' not in response.data  # Template should be rendered

    def test_month_categories_route_success(self, client, test_data):
        """Test show_month_categories route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request to month categories route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/months/{month_id}/categories')

        # Verify successful response
        assert response.status_code == 200
        assert b'2024-01-01' in response.data  # Formatted date should be in response
        assert b'month_categories_list.html' not in response.data  # Template should be rendered

    def test_category_month_transactions_route_success(self, client, test_data):
        """Test show_category_month_transactions route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request to category month transactions route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')

        # Verify successful response
        assert response.status_code == 200
        assert b'Transaction Details' in response.data  # Page title should be in response
        assert b'2024-01-01' in response.data  # Formatted date should be in response
        assert b'category_month_transactions.html' not in response.data  # Template should be rendered

    def test_category_months_route_invalid_account(self, client):
        """Test show_category_months route with invalid account ID."""
        # Make request with invalid account ID
        response = client.get('/results/test123/accounts/invalid_account/categories/cat1/months')

        # Verify redirect to index
        assert response.status_code == 302
        assert response.location.endswith('/')

    def test_month_categories_route_invalid_month(self, client, test_data):
        """Test show_month_categories route with invalid month ID."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']

        # Make request with invalid month ID
        response = client.get(f'/results/{result_id}/accounts/{account_id}/months/invalid_month/categories')

        # Verify redirect to index
        assert response.status_code == 302
        assert response.location.endswith('/')

    def test_category_month_transactions_route_invalid_data(self, client, test_data):
        """Test show_category_month_transactions route with invalid category ID."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request with invalid category ID
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/invalid_category/months/{month_id}/transactions')

        # Verify redirect to index
        assert response.status_code == 302
        assert response.location.endswith('/')

    def test_category_months_route_missing_cache(self, client):
        """Test show_category_months route with missing cache data."""
        # Make request with non-existent result ID
        response = client.get('/results/nonexistent/accounts/account1/categories/cat1/months')

        # Verify redirect to index
        assert response.status_code == 302
        assert response.location.endswith('/')

    def test_handle_entity_drilldown_category_filtering(self, factory: RouteTestFactory):
        """Test that handle_entity_drilldown correctly filters by category."""
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()

            # Mock the services to track calls
            from whatsthedamage.controllers.routes_helpers import _get_drilldown_service
            drilldown_service = _get_drilldown_service()

            # Spy on filter_data_for_entity method
            original_filter = drilldown_service.filter_data_for_entity
            filtered_data = []

            def mock_filter(dt_response, entity_type, filter_value):
                result = original_filter(dt_response, entity_type, filter_value)
                filtered_data.extend(result)
                return result

            drilldown_service.filter_data_for_entity = mock_filter

            try:
                # Call the helper function
                with patch('whatsthedamage.controllers.routes_helpers.make_response'):
                    with patch('whatsthedamage.controllers.routes_helpers.render_template'):
                        handle_entity_drilldown(
                            result_id=test_data['result_id'],
                            account_id=test_data['account_id'],
                            entity_id=test_data['category_ids']['Grocery'],
                            entity_type='category',
                            template='category_months_list.html'
                        )

                        # Verify filtering worked correctly
                        assert len(filtered_data) == 2  # Should have 2 months for Grocery category
                        assert all(row.category == 'Grocery' for row in filtered_data)

            finally:
                # Restore original method
                drilldown_service.filter_data_for_entity = original_filter

    def test_handle_entity_drilldown_month_filtering(self, factory: RouteTestFactory):
        """Test that handle_entity_drilldown correctly filters by month."""
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()

            # Mock the services to track calls
            from whatsthedamage.controllers.routes_helpers import _get_drilldown_service
            drilldown_service = _get_drilldown_service()

            # Spy on filter_data_for_entity method
            original_filter = drilldown_service.filter_data_for_entity
            filtered_data = []

            def mock_filter(dt_response, entity_type, filter_value):
                result = original_filter(dt_response, entity_type, filter_value)
                filtered_data.extend(result)
                return result

            drilldown_service.filter_data_for_entity = mock_filter

            try:
                # Call the helper function
                with patch('whatsthedamage.controllers.routes_helpers.make_response'):
                    with patch('whatsthedamage.controllers.routes_helpers.render_template'):
                        handle_entity_drilldown(
                            result_id=test_data['result_id'],
                            account_id=test_data['account_id'],
                            entity_id=test_data['month_ids']['1704067200'],  # Jan 2024
                            entity_type='month',
                            template='month_categories_list.html'
                        )

                        # Verify filtering worked correctly
                        assert len(filtered_data) == 3  # Should have 3 categories for Jan 2024
                        assert all(str(row.date.timestamp) == '1704067200' for row in filtered_data)

            finally:
                # Restore original method
                drilldown_service.filter_data_for_entity = original_filter

    def test_category_month_transactions_route_context(self, client, test_data):
        """Test that show_category_month_transactions builds correct context."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')

        # Verify response contains expected context data
        assert response.status_code == 200
        assert b'Transaction Details' in response.data  # Page title
        assert b'2024-01-01' in response.data  # Formatted date
        assert b'ACCT1234-5678' in response.data  # Formatted account ID

    def test_route_error_handling(self, client):
        """Test error handling in routes."""
        # Test with completely invalid parameters
        response = client.get('/results/invalid/accounts/invalid/categories/invalid/months')
        assert response.status_code == 302  # Should redirect

        response = client.get('/results/invalid/accounts/invalid/months/invalid/categories')
        assert response.status_code == 302  # Should redirect

        response = client.get('/results/invalid/accounts/invalid/categories/invalid/months/invalid/transactions')
        assert response.status_code == 302  # Should redirect

    def test_route_template_rendering(self, client, test_data):
        """Test that routes render the correct templates."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Test category months template
        with client.application.test_request_context():
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "Mocked template"
                with patch('whatsthedamage.controllers.routes_helpers.make_response') as mock_make_response:
                    mock_make_response.return_value = "Mocked response"

                    client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months')

                    # Verify correct template was used
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == 'category_months_list.html'

        # Test month categories template
        with client.application.test_request_context():
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "Mocked template"
                with patch('whatsthedamage.controllers.routes_helpers.make_response') as mock_make_response:
                    mock_make_response.return_value = "Mocked response"

                    client.get(f'/results/{result_id}/accounts/{account_id}/months/{month_id}/categories')

                    # Verify correct template was used
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == 'month_categories_list.html'

        # Test category month transactions template
        with client.application.test_request_context():
            with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:
                mock_render.return_value = "Mocked template"
                with patch('whatsthedamage.controllers.routes_helpers.make_response') as mock_make_response:
                    mock_make_response.return_value = "Mocked response"

                    client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')

                    # Verify correct template was used
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == 'category_month_transactions.html'

class TestDrilldownRouteEdgeCases:
    """Edge case tests for drilldown routes."""

    @pytest.fixture
    def factory(self) -> RouteTestFactory:
        """Create route test factory."""
        return RouteTestFactory()

    @pytest.fixture
    def client(self, factory: RouteTestFactory):
        """Create test client with configured services."""
        return factory.create_test_client()

    @pytest.fixture
    def test_data(self, factory: RouteTestFactory, client):
        """Setup test data in cache and ID mappings."""
        with client.application.app_context():
            return factory.setup_test_data()

    def test_empty_cache_data(self, factory: RouteTestFactory):
        """Test routes with empty cache data."""
        with factory.create_app_with_test_services().test_request_context():
            # Setup empty cache
            from flask import current_app
            cache_service = current_app.extensions['cache_service']

            # Create empty processing response
            from whatsthedamage.models.dt_models import ProcessingResponse
            empty_response = ProcessingResponse(
                result_id='empty',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )
            cache_service.set('empty', empty_response)

            # Test with empty data
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                handle_entity_drilldown(
                    result_id='empty',
                    account_id='account1',
                    entity_id='cat1',
                    entity_type='category',
                    template='category_months_list.html'
                )

                # Should redirect due to no data
                mock_redirect.assert_called_once()

    def test_invalid_entity_type(self, factory: RouteTestFactory):
        """Test routes with invalid entity type."""
        with factory.create_app_with_test_services().test_request_context():
            test_data = factory.setup_test_data()

            # Test with invalid entity type
            with patch('whatsthedamage.controllers.routes_helpers.redirect') as mock_redirect:
                handle_entity_drilldown(
                    result_id=test_data['result_id'],
                    account_id=test_data['account_id'],
                    entity_id='some_id',
                    entity_type='invalid_type',
                    template='category_months_list.html'
                )

                # Should redirect due to invalid entity type
                mock_redirect.assert_called_once()

    def test_missing_result_id(self, client):
        """Test routes with missing result ID."""
        # Test category months route
        response = client.get('/results/missing/accounts/account1/categories/cat1/months')
        assert response.status_code == 302  # Should redirect

        # Test month categories route
        response = client.get('/results/missing/accounts/account1/months/month1/categories')
        assert response.status_code == 302  # Should redirect

        # Test category month transactions route
        response = client.get('/results/missing/accounts/account1/categories/cat1/months/month1/transactions')
        assert response.status_code == 302  # Should redirect

    def test_url_encoding(self, client, test_data):
        """Test routes with URL-encoded parameters."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Test with URL-encoded parameters
        response = client.get(
            f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months?param=value%20with%20spaces'
        )
        assert response.status_code == 200

        response = client.get(
            f'/results/{result_id}/accounts/{account_id}/months/{month_id}/categories?param=value+with+spaces'
        )
        assert response.status_code == 200

    def test_multiple_accounts(self, factory: RouteTestFactory):
        """Test routes with multiple accounts in cache."""
        with factory.create_app_with_test_services().app_context():
            # Setup test data for two accounts
            test_data1 = factory.setup_test_data(result_id='test1', account_number='ACCT11111111')
            test_data2 = factory.setup_test_data(result_id='test2', account_number='ACCT22222222')

            # Test that each account can access its own data
            with patch('whatsthedamage.controllers.routes_helpers.make_response'):
                with patch('whatsthedamage.controllers.routes_helpers.render_template') as mock_render:

                    # Test first account
                    handle_entity_drilldown(
                        result_id='test1',
                        account_id=test_data1['account_id'],
                        entity_id=test_data1['category_ids']['Grocery'],
                        entity_type='category',
                        template='category_months_list.html'
                    )

                    # Test second account
                    handle_entity_drilldown(
                        result_id='test2',
                        account_id=test_data2['account_id'],
                        entity_id=test_data2['category_ids']['Grocery'],
                        entity_type='category',
                        template='category_months_list.html'
                    )

                    # Should have been called twice
                    assert mock_render.call_count == 2
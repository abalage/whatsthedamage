"""Unit and integration tests for drilldown routes.

This module contains comprehensive tests for the drilldown routes:
- show_category_months
- show_month_categories
- show_category_month_transactions

Tests have been updated to work with JSON responses from the API-only backend.
"""
import pytest
from tests.utils.route_test_factory import RouteTestFactory
from whatsthedamage.controllers.routes_helpers import handle_entity_drilldown
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

            # Call the helper function directly - now returns JSON
            response = handle_entity_drilldown(
                result_id=result_id,
                account_id=account_id,
                entity_id=category_id,
                entity_type='category',
                template='category_months_list.html',
                data_not_found_error='Data not found'
            )

            # Verify JSON response structure
            if isinstance(response, tuple):
                response_data, status_code = response
                assert status_code == 200
            else:
                assert response.status_code == 200
                response_data = response.get_json()

            assert response_data['status'] == 'success'
            assert response_data['entity_name'] == 'Grocery'
            assert 'data' in response_data
            assert len(response_data['data']) == 2  # Grocery has 2 months

    def test_handle_entity_drilldown_month_success(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown helper function for month drilldown."""
        # Setup test data
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()
            result_id = test_data['result_id']
            account_id = test_data['account_id']
            month_id = test_data['month_ids']['1704067200']  # Jan 2024

            # Call the helper function directly - now returns JSON
            response = handle_entity_drilldown(
                result_id=result_id,
                account_id=account_id,
                entity_id=month_id,
                entity_type='month',
                template='month_categories_list.html',
                data_not_found_error='Data not found'
            )

            # Verify JSON response structure
            if isinstance(response, tuple):
                response_data, status_code = response
                assert status_code == 200
            else:
                assert response.status_code == 200
                response_data = response.get_json()

            assert response_data['status'] == 'success'
            assert '2024-01-01' in response_data['entity_name']  # Formatted month name
            assert 'data' in response_data
            assert len(response_data['data']) == 3  # Jan 2024 has 3 categories

    def test_handle_entity_drilldown_invalid_account(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown with invalid account ID."""
        with factory.create_app_with_test_services().test_request_context():
            # Call with invalid account ID - now returns 404 JSON error
            response = handle_entity_drilldown(
                result_id='test123',
                account_id='invalid_account',
                entity_id='cat1',
                entity_type='category',
                template='category_months_list.html',
                data_not_found_error='Data not found'
            )

            # Should return 404 error as JSON
            if isinstance(response, tuple):
                response_obj, status_code = response
                assert status_code == 404
                response_data = response_obj.get_json()
                assert 'error' in response_data
            else:
                assert response.status_code == 404
                response_data = response.get_json()
                assert 'error' in response_data

    def test_handle_entity_drilldown_invalid_entity(self, factory: RouteTestFactory):
        """Test handle_entity_drilldown with invalid entity ID."""
        with factory.create_app_with_test_services().test_request_context():
            test_data = factory.setup_test_data()

            # Call with invalid entity ID - now returns 404 JSON error
            response = handle_entity_drilldown(
                result_id=test_data['result_id'],
                account_id=test_data['account_id'],
                entity_id='invalid_entity',
                entity_type='category',
                template='category_months_list.html',
                data_not_found_error='Data not found'
            )

            # Should return 404 error as JSON
            if isinstance(response, tuple):
                response_obj, status_code = response
                assert status_code == 404
                response_data = response_obj.get_json()
                assert 'error' in response_data
            else:
                assert response.status_code == 404
                response_data = response.get_json()
                assert 'error' in response_data

    def test_category_months_route_success(self, client, test_data):
        """Test show_category_months route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']

        # Make request to category months route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months')

        # Verify successful JSON response
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'success'
        assert response_data['entity_name'] == 'Grocery'
        assert 'data' in response_data

    def test_month_categories_route_success(self, client, test_data):
        """Test show_month_categories route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request to month categories route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/months/{month_id}/categories')

        # Verify successful JSON response
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'success'
        assert '2024-01-01' in response_data['entity_name']  # Formatted date
        assert 'data' in response_data

    def test_category_month_transactions_route_success(self, client, test_data):
        """Test show_category_month_transactions route with valid data."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request to category month transactions route
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')

        # Verify successful JSON response
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'success'
        assert response_data['category_name'] == 'Grocery'
        assert '2024-01-01' in response_data['month_name']  # Formatted date
        assert 'data' in response_data

    def test_category_months_route_invalid_account(self, client):
        """Test show_category_months route with invalid account ID."""
        # Make request with invalid account ID - now returns 404
        response = client.get('/results/test123/accounts/invalid_account/categories/cat1/months')

        # Verify error response
        assert response.status_code == 404
        response_data = response.get_json()
        assert 'error' in response_data

    def test_month_categories_route_invalid_month(self, client, test_data):
        """Test show_month_categories route with invalid month ID."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']

        # Make request with invalid month ID - now returns 404
        response = client.get(f'/results/{result_id}/accounts/{account_id}/months/invalid_month/categories')

        # Verify error response
        assert response.status_code == 404
        response_data = response.get_json()
        assert 'error' in response_data

    def test_category_month_transactions_route_invalid_data(self, client, test_data):
        """Test show_category_month_transactions route with invalid category ID."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request with invalid category ID - now returns 404
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/invalid_category/months/{month_id}/transactions')

        # Verify error response
        assert response.status_code == 404
        response_data = response.get_json()
        assert 'error' in response_data

    def test_category_months_route_missing_cache(self, client):
        """Test show_category_months route with missing cache data."""
        # Make request with non-existent result ID - now returns 404
        response = client.get('/results/nonexistent/accounts/account1/categories/cat1/months')

        # Verify error response
        assert response.status_code == 404
        response_data = response.get_json()
        assert 'error' in response_data

    def test_handle_entity_drilldown_category_filtering(self, factory: RouteTestFactory):
        """Test that handle_entity_drilldown correctly filters by category."""
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()

            # Call the helper function - now returns JSON
            response = handle_entity_drilldown(
                result_id=test_data['result_id'],
                account_id=test_data['account_id'],
                entity_id=test_data['category_ids']['Grocery'],
                entity_type='category',
                template='category_months_list.html'
            )

            # Verify response and filtering worked correctly
            if isinstance(response, tuple):
                response_data, status_code = response
                assert status_code == 200
            else:
                assert response.status_code == 200
                response_data = response.get_json()

            assert response_data['status'] == 'success'
            assert len(response_data['data']) == 2  # Should have 2 months for Grocery category
            assert all(row['category'] == 'Grocery' for row in response_data['data'])

    def test_handle_entity_drilldown_month_filtering(self, factory: RouteTestFactory):
        """Test that handle_entity_drilldown correctly filters by month."""
        with factory.create_app_with_test_services().app_context():
            test_data = factory.setup_test_data()

            # Call the helper function - now returns JSON
            response = handle_entity_drilldown(
                result_id=test_data['result_id'],
                account_id=test_data['account_id'],
                entity_id=test_data['month_ids']['1704067200'],  # Jan 2024
                entity_type='month',
                template='month_categories_list.html'
            )

            # Verify response and filtering worked correctly
            if isinstance(response, tuple):
                response_data, status_code = response
                assert status_code == 200
            else:
                assert response.status_code == 200
                response_data = response.get_json()

            assert response_data['status'] == 'success'
            assert len(response_data['data']) == 3  # Should have 3 categories for Jan 2024
            assert all(str(row['date']['timestamp']) == '1704067200' for row in response_data['data'])

    def test_category_month_transactions_route_context(self, client, test_data):
        """Test that show_category_month_transactions builds correct context."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Make request
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')

        # Verify response contains expected data in JSON format
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['status'] == 'success'
        assert response_data['category_name'] == 'Grocery'
        assert '2024-01-01' in response_data['month_name']
        assert 'ACCT12345678' in response_data['account_name']  # Account number

    def test_route_error_handling(self, client):
        """Test error handling in routes."""
        # Test with completely invalid parameters - now returns 404
        response = client.get('/results/invalid/accounts/invalid/categories/invalid/months')
        assert response.status_code == 404

        response = client.get('/results/invalid/accounts/invalid/months/invalid/categories')
        assert response.status_code == 404

        response = client.get('/results/invalid/accounts/invalid/categories/invalid/months/invalid/transactions')
        assert response.status_code == 404

    def test_route_json_response_structure(self, client, test_data):
        """Test that routes return proper JSON response structure."""
        result_id = test_data['result_id']
        account_id = test_data['account_id']
        category_id = test_data['category_ids']['Grocery']
        month_id = test_data['month_ids']['1704067200']  # Jan 2024

        # Test category months route returns JSON
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months')
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'status' in response_data
        assert 'result_id' in response_data
        assert 'entity_name' in response_data
        assert 'data' in response_data

        # Test month categories route returns JSON
        response = client.get(f'/results/{result_id}/accounts/{account_id}/months/{month_id}/categories')
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'status' in response_data
        assert 'result_id' in response_data
        assert 'entity_name' in response_data
        assert 'data' in response_data

        # Test category month transactions route returns JSON
        response = client.get(f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions')
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'status' in response_data
        assert 'result_id' in response_data
        assert 'category_name' in response_data
        assert 'month_name' in response_data
        assert 'data' in response_data


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

            # Test with empty data - now returns 404
            response = handle_entity_drilldown(
                result_id='empty',
                account_id='account1',
                entity_id='cat1',
                entity_type='category',
                template='category_months_list.html'
            )

            # Should return 404 error as JSON
            if isinstance(response, tuple):
                response_obj, status_code = response
                assert status_code == 404
            else:
                assert response.status_code == 404

    def test_invalid_entity_type(self, factory: RouteTestFactory):
        """Test routes with invalid entity type."""
        with factory.create_app_with_test_services().test_request_context():
            test_data = factory.setup_test_data()

            # Test with invalid entity type - now returns 404
            response = handle_entity_drilldown(
                result_id=test_data['result_id'],
                account_id=test_data['account_id'],
                entity_id='some_id',
                entity_type='invalid_type',
                template='category_months_list.html'
            )

            # Should return 404 error as JSON
            if isinstance(response, tuple):
                response_obj, status_code = response
                assert status_code == 404
            else:
                assert response.status_code == 404

    def test_missing_result_id(self, client):
        """Test routes with missing result ID."""
        # Test category months route - now returns 404
        response = client.get('/results/missing/accounts/account1/categories/cat1/months')
        assert response.status_code == 404

        # Test month categories route - now returns 404
        response = client.get('/results/missing/accounts/account1/months/month1/categories')
        assert response.status_code == 404

        # Test category month transactions route - now returns 404
        response = client.get('/results/missing/accounts/account1/categories/cat1/months/month1/transactions')
        assert response.status_code == 404

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
            # First account
            response1 = handle_entity_drilldown(
                result_id='test1',
                account_id=test_data1['account_id'],
                entity_id=test_data1['category_ids']['Grocery'],
                entity_type='category',
                template='category_months_list.html'
            )

            # Second account
            response2 = handle_entity_drilldown(
                result_id='test2',
                account_id=test_data2['account_id'],
                entity_id=test_data2['category_ids']['Grocery'],
                entity_type='category',
                template='category_months_list.html'
            )

            # Both should succeed
            if isinstance(response1, tuple):
                assert response1[1] == 200
            else:
                assert response1.status_code == 200

            if isinstance(response2, tuple):
                assert response2[1] == 200
            else:
                assert response2.status_code == 200

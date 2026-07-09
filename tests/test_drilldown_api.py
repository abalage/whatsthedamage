"""Test drilldown API endpoints.

This module tests the API v2 drilldown endpoints for category months,
month categories, and transaction details.
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.models.domain.dt_models import ProcessingResponse, AggregatedRow, DetailRow, TransactionDetail
from whatsthedamage.models.domain.account import Account
from whatsthedamage.models.api.common import ProcessingMetadata
from whatsthedamage.models.api.responses import (
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    MonthData,
    CategoryData,
)


@pytest.fixture
def client():
    """Create test client for drilldown API endpoints."""
    app = Flask(__name__)
    app.register_blueprint(v2_bp)

    # Mock the cache service and drilldown response service
    with patch('whatsthedamage.api.v2.endpoints._get_cache_service') as mock_cache_service, \
         patch('whatsthedamage.api.v2.endpoints._get_drilldown_response_service') as mock_drilldown_response_service, \
         patch('whatsthedamage.api.helpers._get_id_mapping_service') as mock_id_mapping_service:

        # Create mock cache service
        mock_cache = MagicMock()
        mock_cache_service.return_value = mock_cache

        # Set up test data
        test_result = _create_test_processing_response()
        mock_cache.get.return_value = test_result

        # Create mock drilldown response service
        mock_drilldown_service = MagicMock()
        mock_drilldown_response_service.return_value = mock_drilldown_service

        # Configure mock responses for drilldown service
        def get_category_months_side_effect(result_id, account_id, category_id):
            from whatsthedamage.models.common.display_fields import DisplayRawField
            months_list = [
                MonthData(
                    month_timestamp=1672531200,
                    total=DisplayRawField(display='$150.00', raw=150.0),
                    row_id='row_1',
                    cell_url=f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/1672531200/transactions'
                )
            ]
            return CategoryMonthsApiResponse(
                result_id=result_id,
                account_id=account_id,
                account_name='Test Account',
                category_id=category_id,
                data=months_list,
                highlights=None
            )

        def get_month_categories_side_effect(result_id, account_id, month_id):
            from whatsthedamage.models.common.display_fields import DisplayRawField
            categories_list = [
                CategoryData(
                    category_id='grocery',
                    total=DisplayRawField(display='$150.00', raw=150.0),
                    row_id='row_1',
                    category_url=f'/results/{result_id}/accounts/{account_id}/categories/grocery/months/{month_id}/transactions'
                ),
                CategoryData(
                    category_id='entertainment_and_leisure',
                    total=DisplayRawField(display='$75.00', raw=75.0),
                    row_id='row_2',
                    category_url=f'/results/{result_id}/accounts/{account_id}/categories/entertainment_and_leisure/months/{month_id}/transactions'
                )
            ]
            return MonthCategoriesApiResponse(
                result_id=result_id,
                account_id=account_id,
                account_name='Test Account',
                month_id=month_id,
                month_timestamp=1672531200,
                data=categories_list,
                highlights=None
            )

        def get_category_month_transactions_side_effect(result_id, account_id, category_id, month_id):
            from whatsthedamage.models.common.display_fields import DisplayRawField, DateField
            # Return transaction data for the grocery category in January 2023
            if category_id == 'grocery' and month_id == '1672531200':
                transactions_list = [
                    TransactionDetail(
                        date=DateField(display='2023-01-01', timestamp=1672531200),
                        amount=DisplayRawField(display='$100.00', raw=100.0),
                        merchant='Test Merchant 1',
                        currency='',
                        account='',
                        type='',
                        confidence=None,
                        row_id='detail_1',
                        category_id=category_id,
                        month_id=month_id
                    ),
                    TransactionDetail(
                        date=DateField(display='2023-01-15', timestamp=1673740800),
                        amount=DisplayRawField(display='$50.00', raw=50.0),
                        merchant='Test Merchant 2',
                        currency='',
                        account='',
                        type='',
                        confidence=None,
                        row_id='detail_2',
                        category_id=category_id,
                        month_id=month_id
                    )
                ]
                return CategoryMonthTransactionsApiResponse(
                    result_id=result_id,
                    account_id=account_id,
                    account_name='Test Account',
                    category_id=category_id,
                    month_id=month_id,
                    month_timestamp=1672531200,
                    data=transactions_list,
                    highlights=None
                )
            else:
                # For non-existent category/month, raise ValueError
                raise ValueError('No transactions found for the specified category and month')

        mock_drilldown_service.get_category_months_response.side_effect = get_category_months_side_effect
        mock_drilldown_service.get_month_categories_response.side_effect = get_month_categories_side_effect
        mock_drilldown_service.get_category_month_transactions_response.side_effect = get_category_month_transactions_side_effect

        # Create mock ID mapping service
        mock_id_mapping = MagicMock()
        mock_id_mapping.get_account_number.return_value = 'test_account_123'
        mock_id_mapping.get_category_name.return_value = 'grocery'
        mock_id_mapping.get_month_timestamp.return_value = '1672531200'
        mock_id_mapping_service.return_value = mock_id_mapping

        with app.test_client() as client:
            yield client


def _create_test_processing_response() -> ProcessingResponse:
    """Create a test ProcessingResponse with sample data."""
    from whatsthedamage.models.common.display_fields import DisplayRawField, DateField

    # Create detail rows
    detail_rows = [
        TransactionDetail(
            date=DateField(display='2023-01-01', timestamp=1672531200),
            amount=DisplayRawField(display='$100.00', raw=100.0),
            merchant='Test Merchant 1',
            currency='USD',
            account='test_account_123',
            type='debit',
            confidence=0.95,
            row_id='detail_1'
        ),
        TransactionDetail(
            date=DateField(display='2023-01-15', timestamp=1673740800),
            amount=DisplayRawField(display='$50.00', raw=50.0),
            merchant='Test Merchant 2',
            currency='USD',
            account='test_account_123',
            type='debit',
            confidence=0.85,
            row_id='detail_2'
        )
    ]

    # Create aggregated rows
    aggregated_rows = [
        AggregatedRow(
            category_id='grocery',
            date=DateField(display='January 2023', timestamp=1672531200),
            total=DisplayRawField(display='$150.00', raw=150.0),
            details=detail_rows,
            row_id='row_1'
        ),
        AggregatedRow(
            category_id='entertainment_and_leisure',
            date=DateField(display='January 2023', timestamp=1672531200),
            total=DisplayRawField(display='$75.00', raw=75.0),
            details=[detail_rows[0]],  # Just one detail for this category
            row_id='row_2'
        )
    ]

    # Create Account
    datatables_response = Account(
        id='test_account_123',
        name='Test Account',
        formatted_id='test-account-123',
        currency='USD',
        data=aggregated_rows,
        result_id='test_result_123',
        metadata={'row_count': 2, 'processing_time': 1.5, 'ml_enabled': False, 'result_id': 'test_result_123', 'highlights': {}}
    )

    # Create ProcessingResponse
    return ProcessingResponse(
        result_id='test_result_123',
        data={'test_account_123': datatables_response},
        metadata=ProcessingMetadata(
            row_count=2,
            processing_time=1.5,
            ml_enabled=False,
            result_id='test_result_123',
            highlights={}
        ),
        statistical_metadata={}
    )


def test_get_category_months_success(client):
    """Test successful retrieval of category months data."""
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/grocery/months')

    assert response.status_code == 200
    data = response.get_json()

    assert data['result_id'] == 'test_result_123'
    assert data['account_id'] == 'test_account_123'
    assert data['category_id'] == 'grocery'
    assert len(data['data']) == 1
    assert data['data'][0]['total']['display'] == '$150.00'
    # Check that month_timestamp is present for frontend navigation
    assert 'cell_url' in data['data'][0]
    assert data['data'][0]['month_timestamp'] == 1672531200
    assert data['data'][0]['row_id'] == 'row_1'


def test_get_category_months_not_found(client):
    """Test 404 response when result is not found."""
    # Mock drilldown response service to raise ValueError (simulating not found)
    with patch('whatsthedamage.api.v2.endpoints._get_drilldown_response_service') as mock_drilldown_response_service, \
         patch('whatsthedamage.api.helpers._get_id_mapping_service'):
        mock_drilldown_service = MagicMock()
        mock_drilldown_response_service.return_value = mock_drilldown_service
        mock_drilldown_service.get_category_months_response.side_effect = ValueError('Results not found')

        response = client.get('/api/v2/results/nonexistent/accounts/test_account/categories/grocery/months')

        assert response.status_code == 404
        data = response.get_json()
        # In test environment without full app context, fallback response is used
        assert 'message' in data or 'error' in data
        if 'message' in data:
            assert 'Results not found' in data['message']
        else:
            assert 'Results not found' in data['error']


def test_get_month_categories_success(client):
    """Test successful retrieval of month categories data."""
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/months/1672531200/categories')

    assert response.status_code == 200
    data = response.get_json()

    assert data['result_id'] == 'test_result_123'
    assert data['account_id'] == 'test_account_123'
    assert data['month_id'] == '1672531200'
    assert data['month_timestamp'] == 1672531200
    assert len(data['data']) == 2  # Should have both food and entertainment

    # Check that both categories are present
    categories = [item['category_id'] for item in data['data']]
    assert 'grocery' in categories
    assert 'entertainment_and_leisure' in categories
    # Check that category_url is present for frontend navigation
    for item in data['data']:
        assert 'category_url' in item
        assert 'row_id' in item


def test_get_category_month_transactions_success(client):
    """Test successful retrieval of transaction details."""
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/grocery/months/1672531200/transactions')

    assert response.status_code == 200
    data = response.get_json()

    assert data['result_id'] == 'test_result_123'
    assert data['account_id'] == 'test_account_123'
    assert data['category_id'] == 'grocery'
    assert data['month_id'] == '1672531200'
    assert data['month_timestamp'] == 1672531200
    assert len(data['data']) == 2  # Should have both detail rows for food category

    # Check transaction details
    assert data['data'][0]['merchant'] == 'Test Merchant 1'
    assert data['data'][0]['amount']['display'] == '$100.00'
    # Check that row_id is present
    assert 'row_id' in data['data'][0]
    assert data['data'][0]['row_id'] == 'detail_1'


def test_get_category_month_transactions_not_found(client):
    """Test 404 response when no transactions are found."""
    # Test with a category that doesn't exist in our test data
    # Need to patch id_mapping_service to return the unknown category name
    # so that the filtering in get_category_month_transactions works correctly
    with patch('whatsthedamage.api.helpers._get_id_mapping_service') as mock_id_mapping_service:
        mock_id_mapping = MagicMock()
        mock_id_mapping.get_account_number.return_value = 'test_account_123'
        # Return the input category_id unchanged (simulating no mapping found)
        mock_id_mapping.get_category_name.return_value = 'other'
        mock_id_mapping.get_month_timestamp.return_value = '1672531200'
        mock_id_mapping_service.return_value = mock_id_mapping

        response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/other/months/1672531200/transactions')

        # The old implementation returns 404 when no transactions found
        assert response.status_code == 404
        data = response.get_json()
        # In test environment without full app context, fallback response is used
        assert 'message' in data or 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""Test drilldown API endpoints.

This module tests the API v2 drilldown endpoints for category months,
month categories, and transaction details.
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.models.dt_models import ProcessingResponse, AccountResponse, AggregatedRow, DetailRow, ProcessingMetadata
from whatsthedamage.models.api_responses import (
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    MonthData,
    CategoryData,
    TransactionDetail,
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
            months_list = [
                MonthData(
                    month='January 2023',
                    month_timestamp=1672531200,
                    total={'display': '$150.00', 'raw': 150.0},
                    row_id='row_1',
                    details=[],
                    cell_url=f'/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/1672531200/transactions'
                )
            ]
            return CategoryMonthsApiResponse(
                result_id=result_id,
                account_id=account_id,
                account_name='Test Account',
                category_id=category_id,
                category_name='Food',
                data=months_list,
                highlights=None
            )
        
        def get_month_categories_side_effect(result_id, account_id, month_id):
            categories_list = [
                CategoryData(
                    category='food',
                    total={'display': '$150.00', 'raw': 150.0},
                    row_id='row_1',
                    details=[],
                    category_url=f'/results/{result_id}/accounts/{account_id}/categories/food/months/{month_id}/transactions'
                ),
                CategoryData(
                    category='entertainment',
                    total={'display': '$75.00', 'raw': 75.0},
                    row_id='row_2',
                    details=[],
                    category_url=f'/results/{result_id}/accounts/{account_id}/categories/entertainment/months/{month_id}/transactions'
                )
            ]
            return MonthCategoriesApiResponse(
                result_id=result_id,
                account_id=account_id,
                account_name='Test Account',
                month_id=month_id,
                month_name='January 2023',
                data=categories_list,
                highlights=None
            )

        def get_category_month_transactions_side_effect(result_id, account_id, category_id, month_id):
            # Return transaction data for the food category in January 2023
            if category_id == 'food' and month_id == '1672531200':
                transactions_list = [
                    TransactionDetail(
                        date={'display': '2023-01-01', 'timestamp': '1672531200'},
                        amount={'display': '$100.00', 'raw': 100.0},
                        merchant='Test Merchant 1',
                        currency='',
                        type='',
                        confidence=None,
                        row_id='detail_1',
                        category='Food',
                        category_id=category_id,
                        month_id=month_id
                    ),
                    TransactionDetail(
                        date={'display': '2023-01-15', 'timestamp': '1673740800'},
                        amount={'display': '$50.00', 'raw': 50.0},
                        merchant='Test Merchant 2',
                        currency='',
                        type='',
                        confidence=None,
                        row_id='detail_2',
                        category='Food',
                        category_id=category_id,
                        month_id=month_id
                    )
                ]
                return CategoryMonthTransactionsApiResponse(
                    result_id=result_id,
                    account_id=account_id,
                    account_name='Test Account',
                    category_id=category_id,
                    category_name='Food',
                    month_id=month_id,
                    month_name='January 2023',
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
        mock_id_mapping.get_category_name.return_value = 'food'
        mock_id_mapping.get_month_timestamp.return_value = '1672531200'
        mock_id_mapping_service.return_value = mock_id_mapping
        
        with app.test_client() as client:
            yield client


def _create_test_processing_response() -> ProcessingResponse:
    """Create a test ProcessingResponse with sample data."""
    # Create detail rows
    detail_rows = [
        DetailRow(
            date={'display': '2023-01-01', 'timestamp': 1672531200},
            amount={'display': '$100.00', 'raw': 100.0},
            merchant='Test Merchant 1',
            currency='USD',
            account='test_account_123',
            type='debit',
            confidence=0.95,
            row_id='detail_1'
        ),
        DetailRow(
            date={'display': '2023-01-15', 'timestamp': 1673740800},
            amount={'display': '$50.00', 'raw': 50.0},
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
            category='food',
            date={'display': 'January 2023', 'timestamp': 1672531200},
            total={'display': '$150.00', 'raw': 150.0},
            details=detail_rows,
            row_id='row_1'
        ),
        AggregatedRow(
            category='entertainment',
            date={'display': 'January 2023', 'timestamp': 1672531200},
            total={'display': '$75.00', 'raw': 75.0},
            details=[detail_rows[0]],  # Just one detail for this category
            row_id='row_2'
        )
    ]
    
    # Create AccountResponse
    datatables_response = AccountResponse(
        data=aggregated_rows,
        account='test_account_123',
        name='Test Account',
        currency='USD',
        result_id='test_result_123',
        metadata=ProcessingMetadata(
            row_count=2,
            processing_time=1.5,
            ml_enabled=False,
            result_id='test_result_123',
            highlights={}
        )
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
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/food/months')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['result_id'] == 'test_result_123'
    assert data['account_id'] == 'test_account_123'
    assert data['category_id'] == 'food'
    assert data['category_name'] == 'Food'
    assert len(data['data']) == 1
    assert data['data'][0]['month'] == 'January 2023'
    assert data['data'][0]['total']['display'] == '$150.00'
    # Check that cell_url and month_timestamp are present for frontend navigation
    assert 'cell_url' in data['data'][0]
    assert 'month_timestamp' in data['data'][0]
    assert data['data'][0]['row_id'] == 'row_1'


def test_get_category_months_not_found(client):
    """Test 404 response when result is not found."""
    # Mock drilldown response service to raise ValueError (simulating not found)
    with patch('whatsthedamage.api.v2.endpoints._get_drilldown_response_service') as mock_drilldown_response_service, \
         patch('whatsthedamage.api.helpers._get_id_mapping_service'):
        mock_drilldown_service = MagicMock()
        mock_drilldown_response_service.return_value = mock_drilldown_service
        mock_drilldown_service.get_category_months_response.side_effect = ValueError('Results not found')
        
        response = client.get('/api/v2/results/nonexistent/accounts/test_account/categories/food/months')
        
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
    assert len(data['data']) == 2  # Should have both food and entertainment
    
    # Check that both categories are present
    categories = [item['category'] for item in data['data']]
    assert 'food' in categories
    assert 'entertainment' in categories
    # Check that category_url is present for frontend navigation
    for item in data['data']:
        assert 'category_url' in item
        assert 'row_id' in item


def test_get_category_month_transactions_success(client):
    """Test successful retrieval of transaction details."""
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/food/months/1672531200/transactions')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['result_id'] == 'test_result_123'
    assert data['account_id'] == 'test_account_123'
    assert data['category_id'] == 'food'
    assert data['month_id'] == '1672531200'
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
        mock_id_mapping.get_category_name.return_value = 'nonexistent'
        mock_id_mapping.get_month_timestamp.return_value = '1672531200'
        mock_id_mapping_service.return_value = mock_id_mapping
        
        response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/nonexistent/months/1672531200/transactions')
        
        # The old implementation returns 404 when no transactions found
        assert response.status_code == 404
        data = response.get_json()
        # In test environment without full app context, fallback response is used
        assert 'message' in data or 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
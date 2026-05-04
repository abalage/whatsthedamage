"""Test drilldown API endpoints.

This module tests the API v2 drilldown endpoints for category months,
month categories, and transaction details.
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from whatsthedamage.api.v2.endpoints import v2_bp
from whatsthedamage.models.dt_models import ProcessingResponse, DataTablesResponse, AggregatedRow, DetailRow, ProcessingMetadata


@pytest.fixture
def client():
    """Create test client for drilldown API endpoints."""
    app = Flask(__name__)
    app.register_blueprint(v2_bp)
    
    # Mock the cache service
    with patch('whatsthedamage.api.v2.endpoints._get_cache_service') as mock_cache_service:
        # Create mock cache service
        mock_cache = MagicMock()
        mock_cache_service.return_value = mock_cache
        
        # Set up test data
        test_result = _create_test_processing_response()
        mock_cache.get.return_value = test_result
        
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
    
    # Create DataTablesResponse
    datatables_response = DataTablesResponse(
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
    # Mock cache to return None
    with patch('whatsthedamage.api.v2.endpoints._get_cache_service') as mock_cache_service:
        mock_cache = MagicMock()
        mock_cache_service.return_value = mock_cache
        mock_cache.get.return_value = None
        
        response = client.get('/api/v2/results/nonexistent/accounts/test_account/categories/food/months')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


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
    response = client.get('/api/v2/results/test_result_123/accounts/test_account_123/categories/nonexistent/months/1672531200/transactions')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
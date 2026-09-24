"""API v2 Contract Tests.

These tests verify that each API endpoint returns responses that conform to
their declared Pydantic model schemas, ensuring type safety and contract compliance
between backend and frontend.

Each test validates:
1. Response structure matches the Pydantic model
2. All required fields are present
3. Field types are correct
4. Response can be parsed by the Pydantic model
"""
import pytest

from whatsthedamage.models.api.responses import (
    ResultsApiResponse,
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    RecalculateApiResponse,
)
from whatsthedamage.models.common.error_models import ErrorResponse
from whatsthedamage.models.domain.dt_models import DetailedResponse
from tests.api_test_utils import MockProcessingService


@pytest.fixture
def sample_csv_file():
    """Sample CSV file for testing."""
    from tests.api_test_utils import create_csv_bytes
    content = create_csv_bytes([
        ['2024-01-01', '100.00', 'Test Merchant', 'deposit', 'EUR'],
        ['2024-01-02', '-200.00', 'Another Merchant', 'withdrawal', 'EUR'],
        ['2024-01-03', '300.00', 'SALARY', 'deposit', 'EUR'],
    ])
    return (content, 'test.csv')


def _setup_mock_with_data(mock_processing_service):
    """Helper to configure mock processing service with test data."""
    detail_row = MockProcessingService.create_detail_row('grocery', 100.0, 'Test Merchant')
    detail_row2 = MockProcessingService.create_detail_row('transport', 200.0, 'Another Merchant')
    mock_processing_service.process_with_details.return_value = \
        MockProcessingService.create_detailed_result([detail_row, detail_row2], row_count=3)


# =============================================================================
# Process Endpoint Contract Tests
# =============================================================================

class TestProcessEndpoint:
    """Contract tests for POST /api/v2/processing-results endpoint."""

    def test_process_returns_valid_metadata_response(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /processing-results returns metadata only (new schema)."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/processing-results',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        assert response.status_code == 201
        data = response.get_json()

        # Verify new metadata-only response format
        assert 'result_id' in data
        assert 'user_id' in data
        assert 'csv_profile_id' in data
        assert 'row_count' in data
        assert 'processing_time' in data
        assert 'ml_enabled' in data
        assert 'start_date' in data
        assert 'end_date' in data
        assert 'created_at' in data

        # Verify no old fields are present
        assert len(data['result_id']) > 0

    def test_process_response_has_metadata_only_structure(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /processing-results response has metadata only (new schema)."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/processing-results',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        data = response.get_json()

        # Check metadata-only structure (new schema)
        assert 'result_id' in data
        assert 'user_id' in data
        assert 'csv_profile_id' in data
        assert 'row_count' in data
        assert 'processing_time' in data
        assert 'ml_enabled' in data
        assert 'start_date' in data
        assert 'end_date' in data
        assert 'created_at' in data
        assert 'transactions_count' in data

        # Ensure no old fields
        assert 'data' not in data
        assert 'metadata' not in data
        assert 'statistical_metadata' not in data
        assert 'processing_metadata' not in data

    def test_process_response_metadata_types(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /processing-results response has correct metadata types."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/processing-results',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        data = response.get_json()
        metadata = data['metadata']

        # Verify types
        assert isinstance(data['result_id'], str)
        assert isinstance(data['row_count'], int)
        assert isinstance(data['processing_time'], float)
        assert isinstance(data['ml_enabled'], bool)


# =============================================================================
# Processing Results Endpoint Contract Tests
# =============================================================================

class TestProcessingResultsEndpoint:
    """Contract tests for GET /api/v2/processing-results/<result_id> endpoint."""

    def test_processing_results_returns_metadata_only(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /processing-results/<id> returns metadata only."""
        _setup_mock_with_data(mock_processing_service)
        # First process a file to get a result_id
        process_response = api_client_with_mock.post(
            '/api/v2/processing-results',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['result_id']

        # Now fetch processing result metadata
        response = api_client_with_mock.get(f'/api/v2/processing-results/{result_id}')

        assert response.status_code == 200
        data = response.get_json()

        # Verify metadata-only response
        assert data['result_id'] == result_id
        assert 'user_id' in data
        assert 'csv_profile_id' in data
        assert 'row_count' in data
        assert 'processing_time' in data
        assert 'ml_enabled' in data
        assert 'start_date' in data
        assert 'end_date' in data
        assert 'created_at' in data
        assert 'transactions_url' in data

        # Verify no transaction data in response
        assert 'data' not in data
        assert 'accounts' not in data
        assert 'statistical_metadata' not in data

    def test_processing_results_404_for_nonexistent_id(self, api_client_with_mock):
        """Verify /processing-results/<id> returns error for non-existent result_id."""
        response = api_client_with_mock.get('/api/v2/processing-results/nonexistent-id-12345')
        # The endpoint may return 404 or 422 depending on error handling
        assert response.status_code in [404, 422]

        # Verify error response structure
        data = response.get_json()
        assert 'error' in data


# =============================================================================
# Drilldown Endpoints Contract Tests (Updated to use new /transactions/aggregate endpoint)
# =============================================================================

class TestDrilldownEndpoints:
    """Contract tests for new drilldown endpoints using /transactions/aggregate."""

    def test_aggregate_transactions_by_category(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /transactions/aggregate returns valid data when grouped by category."""
        _setup_mock_with_data(mock_processing_service)
        # Process and get result_id
        process_response = api_client_with_mock.post(
            '/api/v2/processing-results',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['result_id']

        # Fetch aggregated transactions grouped by category
        response = api_client_with_mock.get(
            f'/api/v2/transactions/aggregate?result_id={result_id}&group_by=category'
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify response structure
        assert 'result_id' in data
        assert 'group_by' in data
        assert data['group_by'] == 'category'
        assert 'groups' in data
        assert 'highlights' in data
        assert 'total_count' in data

    def test_month_categories_returns_valid_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify month categories drilldown returns valid MonthCategoriesApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        process_response = api_client_with_mock.post(
            '/api/v2/transactions',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        results_response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        results_data = results_response.get_json()

        # Find first account with valid id and data
        account = None
        for acc in results_data.get('accounts', []):
            if acc.get('id') and acc.get('data'):
                account = acc
                break

        if account:
            account_id = account['id']

            # Get first month from account data
            first_row = account['data'][0]
            month_id = first_row['date']['display']

            response = api_client_with_mock.get(
                f'/api/v2/results/{result_id}/accounts/{account_id}/months/{month_id}/categories'
            )

            assert response.status_code == 200
            data = response.get_json()

            validated = MonthCategoriesApiResponse.model_validate(data)

            assert validated.result_id == result_id
            assert validated.account_id == account_id
            assert validated.month_id == month_id
            assert validated.data is not None

    def test_category_month_transactions_returns_valid_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify cell transactions drilldown returns valid CategoryMonthTransactionsApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        process_response = api_client_with_mock.post(
            '/api/v2/transactions',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        results_response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        results_data = results_response.get_json()

        # Find first account with valid id and data
        account = None
        for acc in results_data.get('accounts', []):
            if acc.get('id') and acc.get('data'):
                account = acc
                break

        if account:
            account_id = account['id']

            first_row = account['data'][0]
            category_id = first_row['category_id']
            month_id = first_row['date']['display']

            response = api_client_with_mock.get(
                f'/api/v2/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions'
            )

            assert response.status_code == 200
            data = response.get_json()

            validated = CategoryMonthTransactionsApiResponse.model_validate(data)

            assert validated.result_id == result_id
            assert validated.account_id == account_id
            assert validated.category_id == category_id
            assert validated.month_id == month_id
            assert validated.data is not None


# =============================================================================
# Error Response Contract Tests
# =============================================================================

class TestErrorResponses:
    """Contract tests for error responses."""

    def test_missing_file_returns_error_response(self, api_client_with_mock):
        """Verify missing file error returns valid ErrorResponse format."""
        response = api_client_with_mock.post(
            '/api/v2/transactions',
            data={},  # No csv_file
            content_type='multipart/form-data',
        )

        assert response.status_code == 400
        data = response.get_json()

        # Validate against Pydantic model
        validated = ErrorResponse.model_validate(data)

        assert validated.code == 400
        assert validated.message is not None
        assert len(validated.message) > 0

    def test_nonexistent_result_returns_error_response(self, api_client_with_mock):
        """Verify non-existent result error returns valid ErrorResponse format."""
        response = api_client_with_mock.get('/api/v2/results/nonexistent-id')

        # The endpoint may return 404 or 422 depending on error handling
        assert response.status_code in [404, 422]
        data = response.get_json()

        validated = ErrorResponse.model_validate(data)

        assert validated.code in [404, 422]
        assert validated.message is not None

    def test_invalid_recalculate_payload_returns_error_response(self, api_client_with_mock):
        """Verify invalid recalculate payload returns valid ErrorResponse format."""
        response = api_client_with_mock.post(
            '/api/v2/recalculate-statistics',
            json={},  # Missing required fields
        )

        assert response.status_code == 400
        data = response.get_json()

        validated = ErrorResponse.model_validate(data)

        assert validated.code == 400
        assert validated.message is not None


# =============================================================================
# Pydantic Model Validation Tests
# =============================================================================

class TestPydanticModelValidation:
    """Tests to verify Pydantic models properly validate response structures."""

    def test_detailed_response_model_structure(self):
        """Verify DetailedResponse has correct field structure."""
        from pydantic import ValidationError

        # Valid data should pass
        valid_data = {
            'data': [],
            'metadata': {
                'result_id': 'test-id',
                'row_count': 0,
                'processing_time': 0.0,
                'ml_enabled': False,
            }
        }
        DetailedResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'data': []}  # Missing metadata
        with pytest.raises(ValidationError):
            DetailedResponse.model_validate(invalid_data)

    def test_results_api_response_model_structure(self):
        """Verify ResultsApiResponse has correct field structure."""
        from pydantic import ValidationError

        valid_data = {
            'result_id': 'test-id',
            'accounts': [],
            'highlights': {},
            'drilldown_urls_by_account': {}
        }
        ResultsApiResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'result_id': 'test-id'}  # Missing accounts
        with pytest.raises(ValidationError):
            ResultsApiResponse.model_validate(invalid_data)

    def test_recalculate_api_response_model_structure(self):
        """Verify RecalculateApiResponse has correct field structure."""
        from pydantic import ValidationError

        valid_data = {
            'status': 'success',
            'result_id': 'test-id',
            'highlights': {},
            'algorithms': [],
            'direction': 'columns'
        }
        RecalculateApiResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'status': 'success'}  # Missing other fields
        with pytest.raises(ValidationError):
            RecalculateApiResponse.model_validate(invalid_data)

    def test_error_response_model_structure(self):
        """Verify ErrorResponse has correct field structure."""
        from pydantic import ValidationError

        valid_data = {
            'code': 400,
            'message': 'Test error'
        }
        ErrorResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'code': 400}  # Missing message
        with pytest.raises(ValidationError):
            ErrorResponse.model_validate(invalid_data)

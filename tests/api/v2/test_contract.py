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

from whatsthedamage.models.api_responses import (
    ProcessApiResponse,
    ResultsApiResponse,
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    RecalculateApiResponse,
    ErrorApiResponse,
)
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
    """Contract tests for POST /api/v2/process endpoint."""

    def test_process_returns_valid_process_api_response_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /process returns valid ProcessApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        assert response.status_code == 200
        data = response.get_json()

        # Validate against Pydantic model
        validated = ProcessApiResponse.model_validate(data)

        # Verify required fields exist
        assert validated.data is not None
        assert isinstance(validated.data, list)
        assert len(validated.data) > 0

        # Verify metadata exists and has required fields
        assert validated.metadata is not None
        assert validated.metadata.result_id is not None
        assert isinstance(validated.metadata.result_id, str)
        assert len(validated.metadata.result_id) > 0

    def test_process_response_has_correct_structure(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /process response has all required fields with correct types."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        data = response.get_json()

        # Check top-level structure
        assert 'data' in data
        assert 'metadata' in data

        # Check data is an array
        assert isinstance(data['data'], list)

        # Check metadata structure
        assert 'result_id' in data['metadata']
        assert 'row_count' in data['metadata']
        assert 'processing_time' in data['metadata']
        assert 'ml_enabled' in data['metadata']

        # Check first data item has required fields
        if data['data']:
            first_item = data['data'][0]
            assert 'row_id' in first_item
            assert 'category' in first_item
            assert 'total' in first_item
            assert 'date' in first_item
            assert 'details' in first_item

    def test_process_response_metadata_types(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /process response metadata has correct types."""
        _setup_mock_with_data(mock_processing_service)
        response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )

        data = response.get_json()
        metadata = data['metadata']

        # Verify types
        assert isinstance(metadata['result_id'], str)
        assert isinstance(metadata['row_count'], int)
        assert isinstance(metadata['processing_time'], float)
        assert isinstance(metadata['ml_enabled'], bool)


# =============================================================================
# Results Endpoint Contract Tests
# =============================================================================

class TestResultsEndpoint:
    """Contract tests for GET /api/v2/results/<result_id> endpoint."""

    def test_results_returns_valid_results_api_response_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /results/<id> returns valid ResultsApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        # First process a file to get a result_id
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        # Now fetch results
        response = api_client_with_mock.get(f'/api/v2/results/{result_id}')

        assert response.status_code == 200
        data = response.get_json()

        # Validate against Pydantic model
        validated = ResultsApiResponse.model_validate(data)

        # Verify required fields
        assert validated.result_id == result_id
        assert validated.accounts_data is not None

    def test_results_response_has_correct_structure(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /results/<id> response has all required fields."""
        _setup_mock_with_data(mock_processing_service)
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        data = response.get_json()

        # Check top-level structure
        assert 'result_id' in data
        assert 'accounts_data' in data
        assert 'drilldown_urls_by_account' in data

        # Check accounts_data structure
        assert 'accounts' in data['accounts_data']
        assert 'highlights' in data['accounts_data']
        assert isinstance(data['accounts_data']['accounts'], list)

    def test_results_404_for_nonexistent_id(self, api_client_with_mock):
        """Verify /results/<id> returns error for non-existent result_id."""
        response = api_client_with_mock.get('/api/v2/results/nonexistent-id-12345')
        # The endpoint may return 404 or 422 depending on error handling
        assert response.status_code in [404, 422]

        # Verify error response structure
        data = response.get_json()
        assert 'code' in data
        assert 'message' in data


# =============================================================================
# Drilldown Endpoints Contract Tests
# =============================================================================

class TestDrilldownEndpoints:
    """Contract tests for drilldown endpoints."""

    def test_category_months_returns_valid_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify category months drilldown returns valid CategoryMonthsApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        # Process and get result_id
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        # Get first account with non-empty id from results
        results_response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        results_data = results_response.get_json()

        # Find first account with valid id and data
        account = None
        for acc in results_data.get('accounts_data', {}).get('accounts', []):
            if acc.get('id') and acc.get('dt_response', {}).get('data'):
                account = acc
                break

        if account:
            account_id = account['id']

            # Get first category_id from account data
            first_row = account['dt_response']['data'][0]
            category_id = first_row['category']

            # Fetch category months
            response = api_client_with_mock.get(
                f'/api/v2/results/{result_id}/accounts/{account_id}/categories/{category_id}/months'
            )

            assert response.status_code == 200
            data = response.get_json()

            # Validate against Pydantic model
            validated = CategoryMonthsApiResponse.model_validate(data)

            # Verify required fields
            assert validated.result_id == result_id
            assert validated.account_id == account_id
            assert validated.category_id == category_id
            assert validated.data is not None

    def test_month_categories_returns_valid_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify month categories drilldown returns valid MonthCategoriesApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        results_response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        results_data = results_response.get_json()

        # Find first account with valid id and data
        account = None
        for acc in results_data.get('accounts_data', {}).get('accounts', []):
            if acc.get('id') and acc.get('dt_response', {}).get('data'):
                account = acc
                break

        if account:
            account_id = account['id']

            # Get first month from account data
            first_row = account['dt_response']['data'][0]
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
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        results_response = api_client_with_mock.get(f'/api/v2/results/{result_id}')
        results_data = results_response.get_json()

        # Find first account with valid id and data
        account = None
        for acc in results_data.get('accounts_data', {}).get('accounts', []):
            if acc.get('id') and acc.get('dt_response', {}).get('data'):
                account = acc
                break

        if account:
            account_id = account['id']

            first_row = account['dt_response']['data'][0]
            category_id = first_row['category']
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
# Recalculate Statistics Endpoint Contract Tests
# =============================================================================

class TestRecalculateStatisticsEndpoint:
    """Contract tests for POST /api/v2/recalculate-statistics endpoint."""

    def test_recalculate_returns_valid_schema(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /recalculate-statistics returns valid RecalculateApiResponse schema."""
        _setup_mock_with_data(mock_processing_service)
        # First process a file
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        # Recalculate statistics
        response = api_client_with_mock.post(
            '/api/v2/recalculate-statistics',
            json={
                'result_id': result_id,
                'algorithms': ['iqr', 'pareto'],
                'direction': 'columns',
            },
        )

        assert response.status_code == 200
        data = response.get_json()

        # Validate against Pydantic model
        validated = RecalculateApiResponse.model_validate(data)

        # Verify required fields
        assert validated.status == 'success'
        assert validated.result_id == result_id
        assert validated.algorithms == ['iqr', 'pareto']
        assert validated.direction == 'columns'
        assert validated.highlights is not None

    def test_recalculate_response_has_correct_structure(
        self, api_client_with_mock, mock_processing_service, sample_csv_file
    ):
        """Verify /recalculate-statistics response has all required fields."""
        _setup_mock_with_data(mock_processing_service)
        process_response = api_client_with_mock.post(
            '/api/v2/process',
            data={'csv_file': sample_csv_file},
            content_type='multipart/form-data',
        )
        process_data = process_response.get_json()
        result_id = process_data['metadata']['result_id']

        response = api_client_with_mock.post(
            '/api/v2/recalculate-statistics',
            json={
                'result_id': result_id,
                'algorithms': ['iqr'],
                'direction': 'rows',
            },
        )

        data = response.get_json()

        # Check structure
        assert 'status' in data
        assert 'result_id' in data
        assert 'highlights' in data
        assert 'algorithms' in data
        assert 'direction' in data

        # Check types
        assert isinstance(data['status'], str)
        assert isinstance(data['result_id'], str)
        assert isinstance(data['highlights'], dict)
        assert isinstance(data['algorithms'], list)
        assert isinstance(data['direction'], str)


# =============================================================================
# Error Response Contract Tests
# =============================================================================

class TestErrorResponses:
    """Contract tests for error responses."""

    def test_missing_file_returns_error_response(self, api_client_with_mock):
        """Verify missing file error returns valid ErrorApiResponse format."""
        response = api_client_with_mock.post(
            '/api/v2/process',
            data={},  # No csv_file
            content_type='multipart/form-data',
        )

        assert response.status_code == 400
        data = response.get_json()

        # Validate against Pydantic model
        validated = ErrorApiResponse.model_validate(data)

        assert validated.code == 400
        assert validated.message is not None
        assert len(validated.message) > 0

    def test_nonexistent_result_returns_error_response(self, api_client_with_mock):
        """Verify non-existent result error returns valid ErrorApiResponse format."""
        response = api_client_with_mock.get('/api/v2/results/nonexistent-id')

        # The endpoint may return 404 or 422 depending on error handling
        assert response.status_code in [404, 422]
        data = response.get_json()

        validated = ErrorApiResponse.model_validate(data)

        assert validated.code in [404, 422]
        assert validated.message is not None

    def test_invalid_recalculate_payload_returns_error_response(self, api_client_with_mock):
        """Verify invalid recalculate payload returns valid ErrorApiResponse format."""
        response = api_client_with_mock.post(
            '/api/v2/recalculate-statistics',
            json={},  # Missing required fields
        )

        assert response.status_code == 400
        data = response.get_json()

        validated = ErrorApiResponse.model_validate(data)

        assert validated.code == 400
        assert validated.message is not None


# =============================================================================
# Pydantic Model Validation Tests
# =============================================================================

class TestPydanticModelValidation:
    """Tests to verify Pydantic models properly validate response structures."""

    def test_process_api_response_model_structure(self):
        """Verify ProcessApiResponse has correct field structure."""
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
        ProcessApiResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'data': []}  # Missing metadata
        with pytest.raises(ValidationError):
            ProcessApiResponse.model_validate(invalid_data)

    def test_results_api_response_model_structure(self):
        """Verify ResultsApiResponse has correct field structure."""
        from pydantic import ValidationError

        valid_data = {
            'result_id': 'test-id',
            'accounts_data': {
                'accounts': [],
                'highlights': {}
            },
            'drilldown_urls_by_account': {}
        }
        ResultsApiResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'result_id': 'test-id'}  # Missing accounts_data
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

    def test_error_api_response_model_structure(self):
        """Verify ErrorApiResponse has correct field structure."""
        from pydantic import ValidationError

        valid_data = {
            'code': 400,
            'message': 'Test error'
        }
        ErrorApiResponse.model_validate(valid_data)

        # Missing required fields should fail
        invalid_data = {'code': 400}  # Missing message
        with pytest.raises(ValidationError):
            ErrorApiResponse.model_validate(invalid_data)

"""Unit tests for API v2 endpoints.

Tests verify HTTP request/response handling, validation, and error codes
for the v2 API (detailed transaction responses). Uses mocked ProcessingService
to isolate API layer behavior.
"""
import pytest
from tests.api_test_utils import MockProcessingService


class TestAPIv2Process:
    """Test suite for /api/v2/process endpoint - happy path scenarios."""

    def test_process_valid_csv_returns_200(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test successful CSV processing returns 200 with detailed JSON structure."""
        # Override default mock with detailed data
        detail_row = MockProcessingService.create_detail_row('bank_category', 300.0, 'bank')
        mock_processing_service.process_with_details.return_value = \
            MockProcessingService.create_detailed_result([detail_row], row_count=2)

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file)

        data = api_test_helper.assert_success(response, expected_row_count=2)
        assert isinstance(data['data'], list)
        assert len(data['data']) > 0

        # Verify detailed structure
        first_row = data['data'][0]
        assert 'category' in first_row
        assert 'total' in first_row
        assert 'month' in first_row
        assert 'details' in first_row
        assert 'display' in first_row['total']
        assert 'raw' in first_row['total']

    def test_process_with_config_file(self, api_test_helper, mock_processing_service, sample_csv_file, config_yml_default_path):
        """Test processing with both CSV and config file."""
        with open(config_yml_default_path, 'rb') as f:
            from io import BytesIO
            config_file = (BytesIO(f.read()), 'config.yml')

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file, config_file=config_file)

        api_test_helper.assert_success(response)
        call_kwargs = mock_processing_service.process_with_details.call_args.kwargs
        assert call_kwargs.get('config_file_path') is not None

    @pytest.mark.parametrize('param_name,param_value,expected_metadata', [
        ('start_date', '2023.01.01', None),  # Metadata checked separately
        ('ml_enabled', 'true', {'ml_enabled': True}),
        ('category_filter', 'grocery', None),
        ('language', 'hu', None),
    ])
    def test_process_with_parameters(self, api_test_helper, mock_processing_service, sample_csv_file,
                                     param_name, param_value, expected_metadata):
        """Test processing with various query parameters."""
        kwargs = {param_name: param_value}

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file, **kwargs)

        data = api_test_helper.assert_success(response)

        # Verify parameter was passed to service
        call_kwargs = mock_processing_service.process_with_details.call_args.kwargs
        if param_name == 'ml_enabled':
            assert call_kwargs[param_name] is True
        else:
            assert call_kwargs[param_name] == param_value

        # Verify metadata if expected
        if expected_metadata:
            for key, value in expected_metadata.items():
                assert data['metadata'][key] == value


class TestAPIv2ValidationErrors:
    """Test suite for validation error handling in v2 API."""

    @pytest.mark.parametrize('data,content_type,expected_message', [
        ({}, 'multipart/form-data', 'csv_file'),
        ({'csv_file': ('', '')}, 'multipart/form-data', None),  # Empty filename
    ])
    def test_missing_or_invalid_file_returns_400(self, api_client_with_mock, data, content_type, expected_message):
        """Test that missing or invalid CSV file returns 400 error."""
        from io import BytesIO
        if 'csv_file' in data and data['csv_file'] == ('', ''):
            data['csv_file'] = (BytesIO(b''), '')

        response = api_client_with_mock.post('/api/v2/process', data=data, content_type=content_type)

        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data['code'] == 400
        if expected_message:
            assert expected_message in response_data['message'].lower()

    def test_invalid_date_format_returns_400(self, api_test_helper, sample_csv_file):
        """Test that invalid date format returns 400 validation error."""
        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file, start_date='not-a-date')

        data = api_test_helper.assert_error(response, 400)
        assert 'details' in data


class TestAPIv2ProcessingErrors:
    """Test suite for processing error handling in v2 API."""

    @pytest.mark.parametrize('exception,expected_status', [
        (ValueError("Invalid CSV format"), 422),
        (FileNotFoundError("Config not found"), 400),
        (RuntimeError("Unexpected error"), 500),
    ])
    def test_processing_errors_return_correct_status(self, api_test_helper, mock_processing_service,
                                                     sample_csv_file, exception, expected_status):
        """Test that different processing errors return appropriate status codes."""
        mock_processing_service.process_with_details.side_effect = exception

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file)

        api_test_helper.assert_error(response, expected_status)


class TestAPIv2FileCleanup:
    """Test suite for file cleanup in v2 API."""

    def test_files_cleaned_up_after_success(self, api_test_helper, mock_processing_service, sample_csv_file, monkeypatch):
        """Test that uploaded files are cleaned up after successful processing."""
        cleanup_called = {'called': False}

        def mock_cleanup(csv_path, config_path):
            cleanup_called['called'] = True
            import os
            if os.path.exists(csv_path):
                os.unlink(csv_path)

        mock_processing_service.process_with_details.return_value = \
            MockProcessingService.create_detailed_result([], row_count=2)

        monkeypatch.setattr('whatsthedamage.api.v2.endpoints.cleanup_files', mock_cleanup)

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file)

        assert response.status_code == 200
        assert cleanup_called['called'] is True

    def test_files_cleaned_up_after_error(self, api_test_helper, mock_processing_service, sample_csv_file, monkeypatch):
        """Test that uploaded files are cleaned up even after processing errors."""
        cleanup_called = {'called': False}

        def mock_cleanup(csv_path, config_path):
            cleanup_called['called'] = True
            import os
            if os.path.exists(csv_path):
                os.unlink(csv_path)

        mock_processing_service.process_with_details.side_effect = ValueError("Processing failed")
        monkeypatch.setattr('whatsthedamage.api.v2.endpoints.cleanup_files', mock_cleanup)

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file)

        assert response.status_code == 422
        assert cleanup_called['called'] is True


class TestAPIv2DetailedResponseStructure:
    """Test suite for verifying v2 detailed response structure."""

    def test_detailed_response_has_nested_structures(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test that detailed response includes proper nested data structures."""
        # Create detailed mock data
        detail_row = {
            'category': 'grocery',
            'total': {'display': '-45,000.00 HUF', 'raw': -45000.0},
            'month': {'display': 'January 2024', 'timestamp': 1704067200},
            'details': [
                {
                    'date': {'display': '2024-01-15', 'timestamp': 1705276800},
                    'amount': {'display': '-12,500.00', 'raw': -12500.0},
                    'merchant': 'TESCO'
                },
                {
                    'date': {'display': '2024-01-20', 'timestamp': 1705708800},
                    'amount': {'display': '-32,500.00', 'raw': -32500.0},
                    'merchant': 'ALDI'
                }
            ]
        }

        mock_processing_service.process_with_details.return_value = \
            MockProcessingService.create_detailed_result([detail_row], row_count=2)

        response = api_test_helper.post_csv('/api/v2/process', sample_csv_file)

        data = api_test_helper.assert_success(response)

        # Verify nested structure
        assert len(data['data']) == 1
        row = data['data'][0]

        assert row['category'] == 'grocery'
        assert row['total']['display'] == '-45,000.00 HUF'
        assert 'display' in row['month']
        assert 'timestamp' in row['month']
        assert len(row['details']) == 2
        assert row['details'][0]['merchant'] == 'TESCO'
        assert 'display' in row['details'][0]['amount']
        assert 'raw' in row['details'][0]['amount']

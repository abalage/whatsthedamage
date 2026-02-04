"""Tests for ProcessingService.

Unit tests for the ProcessingService class, which orchestrates CSV processing
and provides business logic for Controllers (CLI, Web, API).
"""

import pytest
from unittest.mock import Mock, patch
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.models.dt_models import ProcessingResponse


@pytest.fixture
def service(mock_dependencies):
    """Create ProcessingService instance with mocked config service."""
    return ProcessingService(configuration_service=mock_dependencies['config_service'])


@pytest.fixture
def mock_processor():
    """Create mock CSVProcessor with default data."""
    mock = Mock()
    mock._read_csv_file.return_value = [
        {'date': '2023-01-01', 'amount': 100.0},
        {'date': '2023-01-02', 'amount': 200.0}
    ]
    mock.processor.process_rows.return_value = {
        'January 2023': {'Food': 100.0, 'Transport': 200.0}
    }
    mock.process.return_value = Mock(data=[{'category': 'Food', 'total': 100.0}])
    mock._rows = [Mock(), Mock()]  # Mock cached rows for row_count
    return mock


@pytest.fixture
def mock_dependencies(mock_processor):
    """Mock all external dependencies."""
    # Create mock configuration service
    mock_config_service = Mock()
    mock_config_result = Mock()
    mock_config_result.config = {'csv': {'delimiter': ','}}
    mock_config_service.load_config.return_value = mock_config_result
    
    with patch('whatsthedamage.services.processing_service.CSVProcessor') as mock_class, \
         patch('whatsthedamage.services.processing_service.AppContext'):
        mock_class.return_value = mock_processor
        yield {
            'processor': mock_processor,
            'config_service': mock_config_service,
            'class': mock_class
        }


class TestProcessingService:
    """Tests for ProcessingService class."""

    def test_init(self, service):
        """Test ProcessingService initialization."""
        assert service is not None

    def test_process_with_details_basic(self, service, mock_dependencies):
        """Test process_with_details with basic parameters."""
        result = service.process_with_details(csv_file_path='/path/to/file.csv')

        # Verify structure
        assert isinstance(result, ProcessingResponse)
        assert 'data' in result.__dict__
        assert 'metadata' in result.__dict__
        assert result.metadata.row_count == 2
        assert result.metadata.ml_enabled is False
        assert hasattr(result.metadata, 'processing_time')

        # Verify method calls
        mock_dependencies['processor'].process.assert_called_once()

    @pytest.mark.parametrize('start_date,end_date,ml,category', [
        ('2023-01-01', '2023-12-31', True, 'Food'),
        (None, None, False, None),
    ])
    def test_process_with_details_filters(self, service, mock_dependencies,
                                         start_date, end_date, ml, category):
        """Test process_with_details with various filters."""
        result = service.process_with_details(
            csv_file_path='/path/to/file.csv',
            start_date=start_date,
            end_date=end_date,
            ml_enabled=ml,
            category_filter=category
        )

        assert result.metadata.ml_enabled == ml
        # Check date_range instead of filters_applied
        if start_date or end_date:
            assert result.metadata.date_range is not None
            if start_date:
                assert result.metadata.date_range['start'] == start_date
            if end_date:
                assert result.metadata.date_range['end'] == end_date
        else:
            assert result.metadata.date_range is None

    def test_process_with_details_empty_data(self, service, mock_dependencies):
        """Test process_with_details with empty CSV."""
        mock_dependencies['processor']._read_csv_file.return_value = []
        mock_dependencies['processor']._rows = []  # Empty rows for empty CSV

        result = service.process_with_details(csv_file_path='/path/to/file.csv')

        assert result.metadata.row_count == 0

    @pytest.mark.parametrize('config_input,expected', [
        (None, ''),
        ('', ''),
        ('/path/to/config.yml', '/path/to/config.yml'),
    ])
    def test_build_args_config_handling(self, service, config_input, expected):
        """Test _build_args config parameter handling."""
        args = service._build_args(filename='/path/to/file.csv', config=config_input)
        assert args.config == expected

    def test_build_args_defaults(self, service):
        """Test _build_args with default parameters."""
        args = service._build_args(filename='/path/to/file.csv', config=None)

        assert args.filename == '/path/to/file.csv'
        assert args.start_date is None
        assert args.end_date is None
        assert args.category == 'category'
        assert args.filter is None
        assert args.output_format == 'json'
        assert args.verbose is False
        assert args.lang == 'en'
        assert args.ml is False

    def test_build_args_all_parameters(self, service):
        """Test _build_args with all parameters."""
        args = service._build_args(
            filename='/path/to/file.csv',
            config='/config.yml',
            start_date='2023-01-01',
            end_date='2023-12-31',
            ml_enabled=True,
            category_filter='Food',
            language='hu',
            verbose=True
        )

        assert args.start_date == '2023-01-01'
        assert args.end_date == '2023-12-31'
        assert args.ml is True
        assert args.filter == 'Food'
        assert args.lang == 'hu'
        assert args.verbose is True

    @patch('whatsthedamage.services.processing_service.AppContext')
    def test_process_with_details_uses_verbose_true(self, mock_context, service, mock_dependencies):
        """Test process_with_details sets verbose=True when passed."""
        service.process_with_details(csv_file_path='/path/to/file.csv', verbose=True)

        args = mock_context.call_args[0][1]
        assert args.verbose is True

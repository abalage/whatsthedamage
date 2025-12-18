"""Tests for ProcessingService.

Unit tests for the ProcessingService class, which orchestrates CSV processing
and provides business logic for Controllers (CLI, Web, API).
"""

import pytest
from unittest.mock import Mock, patch
from whatsthedamage.services.processing_service import ProcessingService


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
    mock.process_v2.return_value = Mock(data=[{'category': 'Food', 'total': 100.0}])
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

    def test_process_summary_basic(self, service, mock_dependencies):
        """Test process_summary with basic parameters."""
        result = service.process_summary(csv_file_path='/path/to/file.csv')

        # Verify structure and data
        assert result['data'] == {'Food': 100.0, 'Transport': 200.0}
        assert result['metadata']['row_count'] == 2
        assert result['metadata']['ml_enabled'] is False
        assert 'processing_time' in result['metadata']
        assert 'processor' in result

        # Verify method calls
        mock_dependencies['processor']._read_csv_file.assert_called_once()
        mock_dependencies['processor'].processor.process_rows.assert_called_once()

    @pytest.mark.parametrize('start_date,end_date,ml,category,lang', [
        ('2023-01-01', '2023-12-31', True, 'Food', 'en'),
        ('2023-01-01', None, False, None, 'hu'),
        (None, '2023-12-31', True, 'Transport', 'en'),
    ])
    def test_process_summary_with_filters(self, service, mock_dependencies, 
                                         start_date, end_date, ml, category, lang):
        """Test process_summary with various filter combinations."""
        result = service.process_summary(
            csv_file_path='/path/to/file.csv',
            start_date=start_date,
            end_date=end_date,
            ml_enabled=ml,
            category_filter=category,
            language=lang
        )

        # Verify filters in metadata
        assert result['metadata']['ml_enabled'] == ml
        assert result['metadata']['filters_applied']['start_date'] == start_date
        assert result['metadata']['filters_applied']['end_date'] == end_date
        assert result['metadata']['filters_applied']['category'] == category

    def test_process_summary_multi_month_aggregation(self, service, mock_dependencies):
        """Test that data from multiple months is correctly aggregated."""
        mock_dependencies['processor'].processor.process_rows.return_value = {
            'January 2023': {'Food': 100.0, 'Transport': 50.0},
            'February 2023': {'Food': 150.0, 'Entertainment': 75.0},
            'March 2023': {'Transport': 200.0, 'Entertainment': 100.0}
        }

        result = service.process_summary(csv_file_path='/path/to/file.csv')

        # Verify aggregation
        assert result['data'] == {
            'Food': 250.0,           # 100 + 150
            'Transport': 250.0,       # 50 + 200
            'Entertainment': 175.0    # 75 + 100
        }

    def test_process_summary_empty_data(self, service, mock_dependencies):
        """Test process_summary with empty CSV."""
        mock_dependencies['processor']._read_csv_file.return_value = []
        mock_dependencies['processor'].processor.process_rows.return_value = {}

        result = service.process_summary(csv_file_path='/path/to/file.csv')

        assert result['data'] == {}
        assert result['metadata']['row_count'] == 0

    def test_process_with_details_basic(self, service, mock_dependencies):
        """Test process_with_details with basic parameters."""
        result = service.process_with_details(csv_file_path='/path/to/file.csv')

        # Verify structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['row_count'] == 2
        assert result['metadata']['ml_enabled'] is False
        assert 'processing_time' in result['metadata']

        # Verify method calls
        mock_dependencies['processor'].process_v2.assert_called_once()

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

        assert result['metadata']['ml_enabled'] == ml
        assert result['metadata']['filters_applied']['start_date'] == start_date
        assert result['metadata']['filters_applied']['end_date'] == end_date
        assert result['metadata']['filters_applied']['category'] == category

    def test_process_with_details_empty_data(self, service, mock_dependencies):
        """Test process_with_details with empty CSV."""
        mock_dependencies['processor']._read_csv_file.return_value = []

        result = service.process_with_details(csv_file_path='/path/to/file.csv')

        assert result['metadata']['row_count'] == 0

    @pytest.mark.parametrize('config_input,expected', [
        (None, ''),
        ('', ''),
        ('/path/to/config.yml', '/path/to/config.yml'),
    ])
    def test_build_args_config_handling(self, service, config_input, expected):
        """Test _build_args config parameter handling."""
        args = service._build_args(filename='/path/to/file.csv', config=config_input)
        assert args['config'] == expected

    def test_build_args_defaults(self, service):
        """Test _build_args with default parameters."""
        args = service._build_args(filename='/path/to/file.csv', config=None)

        assert args['filename'] == '/path/to/file.csv'
        assert args['start_date'] is None
        assert args['end_date'] is None
        assert args['category'] == 'category'
        assert args['filter'] is None
        assert args['output_format'] == 'json'
        assert args['verbose'] is False
        assert args['lang'] == 'en'
        assert args['ml'] is False

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

        assert args['start_date'] == '2023-01-01'
        assert args['end_date'] == '2023-12-31'
        assert args['ml'] is True
        assert args['filter'] == 'Food'
        assert args['lang'] == 'hu'
        assert args['verbose'] is True

    @patch('whatsthedamage.services.processing_service.time.time')
    def test_timing_measurement(self, mock_time, service, mock_dependencies):
        """Test that processing time is correctly measured and rounded."""
        mock_time.side_effect = [100.0, 102.567]  # 2.567 seconds

        result = service.process_summary(csv_file_path='/path/to/file.csv')

        # Verify rounding to 2 decimals
        assert abs(result['metadata']['processing_time'] - 2.57) < 0.01

    @patch('whatsthedamage.services.processing_service.AppContext')
    def test_process_summary_uses_verbose_false(self, mock_context, service, mock_dependencies):
        """Test process_summary sets verbose=False."""
        service.process_summary(csv_file_path='/path/to/file.csv')

        args = mock_context.call_args[0][1]
        assert args['verbose'] is False

    @patch('whatsthedamage.services.processing_service.AppContext')
    def test_process_with_details_uses_verbose_true(self, mock_context, service, mock_dependencies):
        """Test process_with_details sets verbose=True."""
        service.process_with_details(csv_file_path='/path/to/file.csv')

        args = mock_context.call_args[0][1]
        assert args['verbose'] is True

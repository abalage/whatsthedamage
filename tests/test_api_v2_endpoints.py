"""Unit tests for API v2 endpoints.

Tests verify HTTP request/response handling, validation, and error codes
for the v2 API. Uses mocked ProcessingService to isolate API layer behavior.
"""
import pytest
from tests.api_test_utils import MockProcessingService


class TestAPIv2Process:
    """Test suite for POST /api/v2/processing-results - happy path scenarios."""

    def test_process_valid_csv_returns_201(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test successful CSV processing returns 201 with metadata-only structure."""
        detail_row = MockProcessingService.create_detail_row('grocery', 300.0, 'bank')
        mock_processing_service.process_with_details.return_value = \
            MockProcessingService.create_detailed_result([detail_row], row_count=2)

        response = api_test_helper.post_processing_result(sample_csv_file)

        data = api_test_helper.assert_created(response)
        assert data['row_count'] == 2
        assert len(data['result_id']) > 0

        # Metadata-only response: no transaction payload
        assert 'data' not in data
        assert 'metadata' not in data

    def test_process_with_config_file(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test processing with both CSV and config file."""
        import tempfile
        from io import BytesIO
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            config_file.write("csv:\n  dialect: excel\n  delimiter: ','\n  date_attribute_format: '%Y-%m-%d'\n  attribute_mapping:\n    date: date\n    amount: amount\n    currency: currency\n    partner: partner\n")
            config_file_path = config_file.name

        with open(config_file_path, 'rb') as f:
            config_file = (BytesIO(f.read()), 'config.yml')

        response = api_test_helper.post_processing_result(sample_csv_file, config_file=config_file)

        api_test_helper.assert_created(response)
        call_kwargs = mock_processing_service.process_with_details.call_args.kwargs
        assert call_kwargs.get('config_file_path') is not None

    @pytest.mark.parametrize('param_name,param_value,expected_response', [
        ('start_date', '2023.01.01', None),  # Response value checked separately
        ('ml_enabled', 'true', True),
        ('category_filter', 'grocery', None)
    ])
    def test_process_with_parameters(self, api_test_helper, mock_processing_service, sample_csv_file,
                                     param_name, param_value, expected_response):
        """Test processing with various form parameters."""
        kwargs = {param_name: param_value}

        response = api_test_helper.post_processing_result(sample_csv_file, **kwargs)

        data = api_test_helper.assert_created(response)

        # Verify parameter was passed to service
        call_kwargs = mock_processing_service.process_with_details.call_args.kwargs
        if param_name == 'ml_enabled':
            assert call_kwargs[param_name] is True
        else:
            assert call_kwargs[param_name] == param_value

        # Verify response value when expected
        if expected_response is not None:
            assert data[param_name] == expected_response


class TestAPIv2ValidationErrors:
    """Test suite for validation error handling in v2 API."""

    @pytest.mark.parametrize('data,content_type', [
        ({}, 'multipart/form-data'),
        ({'csv_file': ('', '')}, 'multipart/form-data'),  # Empty filename
    ])
    def test_missing_or_invalid_file_returns_400(self, api_client_with_mock, data, content_type):
        """Test that missing or invalid CSV file returns 400 error."""
        from io import BytesIO
        if 'csv_file' in data and data['csv_file'] == ('', ''):
            data['csv_file'] = (BytesIO(b''), '')

        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/processing-results', data=data, content_type=content_type, headers=headers)

        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data['code'] == 400

    def test_invalid_date_format_returns_400(self, api_test_helper, sample_csv_file):
        """Test that invalid date format returns 400 validation error."""
        response = api_test_helper.post_processing_result(sample_csv_file, start_date='not-a-date')

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

        response = api_test_helper.post_processing_result(sample_csv_file)

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

        response = api_test_helper.post_processing_result(sample_csv_file)

        api_test_helper.assert_created(response)
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

        response = api_test_helper.post_processing_result(sample_csv_file)

        assert response.status_code == 422
        assert cleanup_called['called'] is True


class TestAPIv2RecalculateStatistics:
    """Test suite for /api/v2/recalculate-statistics endpoint."""

    @staticmethod
    def _make_transactions():
        """Create Transaction-like objects for statistical analysis."""
        from datetime import datetime
        from types import SimpleNamespace
        return [
            SimpleNamespace(account='acc1', category_id='grocery',
                            amount=-100.0, date=datetime(2024, 1, 15)),
            SimpleNamespace(account='acc1', category_id='utilities',
                            amount=-50.0, date=datetime(2024, 1, 15)),
            SimpleNamespace(account='acc1', category_id='entertainment',
                            amount=-200.0, date=datetime(2024, 1, 15)),
            # Income is filtered out of expense analysis
            SimpleNamespace(account='acc1', category_id='salary',
                            amount=1000.0, date=datetime(2024, 1, 15)),
        ]

    def _patch_transaction_repo(self, monkeypatch):
        """Patch the transaction repository to return fixed transactions."""
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        transactions = self._make_transactions()
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'find_all_by_user',
            lambda self, user_id, result_id=None, account=None: transactions,
        )

    def test_recalculate_statistics_defaults(self, api_client_with_mock, monkeypatch):
        """Test that an empty body uses defaults (all enabled algorithms, columns)."""
        self._patch_transaction_repo(monkeypatch)
        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/recalculate-statistics', json={}, headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['algorithms'] == ['iqr', 'pareto']
        assert data['direction'] == 'columns'
        assert data['result_id'] is None
        assert isinstance(data['highlights'], dict)

    def test_recalculate_statistics_result_id_optional(self, api_client_with_mock, monkeypatch):
        """Test that a missing result_id means all of the user's transactions."""
        self._patch_transaction_repo(monkeypatch)
        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/recalculate-statistics', json={
            'algorithms': ['pareto'],
            'direction': 'columns'
        }, headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['result_id'] is None

    def test_recalculate_statistics_returns_highlights(self, api_client_with_mock, monkeypatch):
        """Test that highlights are keyed by '{account}|{month}|{category}' cell IDs."""
        self._patch_transaction_repo(monkeypatch)
        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/recalculate-statistics', json={
            'result_id': 'test123',
            'algorithms': ['pareto'],
            'direction': 'columns'
        }, headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['result_id'] == 'test123'
        # Pareto on {grocery: -100, utilities: -50, entertainment: -200}
        # marks entertainment (200) and grocery (100) as top contributors
        assert data['highlights'].get('acc1|2024-01|entertainment') == ['pareto']
        assert data['highlights'].get('acc1|2024-01|grocery') == ['pareto']
        # Income cells are not analyzed
        assert 'acc1|2024-01|salary' not in data['highlights']

    def test_recalculate_statistics_invalid_algorithms(self, api_client_with_mock):
        """Test that invalid algorithms (not a list) returns 400 error."""
        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/recalculate-statistics', json={
            'result_id': 'test123',
            'algorithms': 'not-a-list'
        }, headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'algorithms must be a list' in data.get('error', '') or 'algorithms must be a list' in data.get('message', '')

    def test_recalculate_statistics_invalid_direction(self, api_client_with_mock):
        """Test that invalid direction returns 400 error."""
        headers = {'X-CSRF-Token': 'test_csrf_token'}
        response = api_client_with_mock.post('/api/v2/recalculate-statistics', json={
            'result_id': 'test123',
            'algorithms': ['iqr'],
            'direction': 'invalid'
        }, headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        error_msg = data.get('error', '') or data.get('message', '')
        assert "direction must be 'columns' or 'rows'" in error_msg


class TestAPIv2AggregateTransactions:
    """Test suite for /api/v2/transactions/aggregate endpoint highlights."""

    @staticmethod
    def _make_transactions():
        """Create Transaction entities for aggregation tests."""
        from datetime import datetime, UTC
        from whatsthedamage.models.database.transaction import Transaction

        def make(category, amount, month):
            return Transaction(
                user_id=1,
                result_id='test123',
                date=datetime(2024, month, 15, tzinfo=UTC),
                transaction_type='debit',
                original_partner='Test Partner',
                amount=amount,
                currency='HUF',
                account='acc1',
                deduplication_hash=f'hash-{category}-{month}',
                category_id=category,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        return [
            make('grocery', -100.0, 1),
            make('utilities', -50.0, 1),
            make('entertainment', -200.0, 1),
            # Different month: must not leak into the fixed-month analysis
            make('grocery', -100.0, 2),
        ]

    def _patch_transaction_repo(self, monkeypatch):
        """Patch the transaction repository to return fixed transactions."""
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        transactions = self._make_transactions()
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'find_by_user_with_filters',
            lambda self, **kwargs: (
                [t for t in transactions
                 if kwargs.get('month') is None
                 or t.date.strftime('%Y-%m') == kwargs.get('month')],
                0,
            ),
        )
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'find_all_by_user',
            lambda self, user_id, result_id=None, account=None: transactions,
        )

    def test_aggregate_returns_highlights_per_group(self, api_client_with_mock, monkeypatch):
        """Test that group highlights come from the parent matrix analysis."""
        self._patch_transaction_repo(monkeypatch)
        response = api_client_with_mock.get(
            '/api/v2/transactions/aggregate'
            '?account=acc1&month=2024-01&group_by=category&algorithms=pareto'
        )
        assert response.status_code == 200
        data = response.get_json()
        # Pareto on the January categories marks entertainment and grocery
        assert data['highlights'].get('entertainment') == ['pareto']
        assert data['highlights'].get('grocery') == ['pareto']
        assert data['highlights'].get('utilities') == []

    def test_aggregate_invalid_direction_returns_400(self, api_client_with_mock):
        """Test that an invalid direction returns 400 error."""
        response = api_client_with_mock.get(
            '/api/v2/transactions/aggregate?group_by=category&direction=invalid'
        )
        assert response.status_code == 400

    def test_aggregate_missing_group_by_returns_400(self, api_client_with_mock):
        """Test that a missing group_by returns 400 error."""
        response = api_client_with_mock.get('/api/v2/transactions/aggregate')
        assert response.status_code == 400


class TestAPIv2CsvProfileId:
    """Test suite for csv_profile_id parameter in v2 API."""

    def test_process_with_csv_profile_id_1800(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test processing with csv_profile_id=1800 parameter."""
        response = api_test_helper.post_processing_result(sample_csv_file, csv_profile_id='1800')

        data = api_test_helper.assert_created(response)
        assert data['csv_profile_id'] == '1800'

    def test_process_with_csv_profile_id_0(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test processing with csv_profile_id=0 (never expire)."""
        response = api_test_helper.post_processing_result(sample_csv_file, csv_profile_id='0')

        data = api_test_helper.assert_created(response)
        assert data['csv_profile_id'] == '0'

    def test_process_without_csv_profile_id_uses_default(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test processing without csv_profile_id parameter uses default."""
        response = api_test_helper.post_processing_result(sample_csv_file)

        api_test_helper.assert_created(response)

    @pytest.mark.parametrize('csv_profile_id_value', ['0', '1800', '3600', '60'])
    def test_process_with_various_csv_profile_id_values(self, api_test_helper, mock_processing_service,
                                                  sample_csv_file, csv_profile_id_value):
        """Test processing with various csv_profile_id values."""
        response = api_test_helper.post_processing_result(sample_csv_file, csv_profile_id=csv_profile_id_value)

        data = api_test_helper.assert_created(response)
        assert data['csv_profile_id'] == csv_profile_id_value

    def test_process_with_csv_profile_id_and_other_params(self, api_test_helper, mock_processing_service, sample_csv_file):
        """Test processing with csv_profile_id combined with other parameters."""
        response = api_test_helper.post_processing_result(sample_csv_file,
                                                          csv_profile_id='1800',
                                                          ml_enabled='true',
                                                          start_date='2024.01.01')

        api_test_helper.assert_created(response)
        # Verify other params were processed
        call_kwargs = mock_processing_service.process_with_details.call_args.kwargs
        assert call_kwargs['ml_enabled'] is True
        assert call_kwargs['start_date'] == '2024.01.01'


class TestAPIv2EmptyAccountFallback:
    """Test suite for the 'unknown' fallback of transactions without an account."""

    @staticmethod
    def _make_transactions():
        """Create Transaction entities, one with an empty account."""
        from datetime import datetime, UTC
        from whatsthedamage.models.database.transaction import Transaction

        def make(account):
            return Transaction(
                user_id=1,
                result_id='test123',
                date=datetime(2024, 1, 15, tzinfo=UTC),
                transaction_type='debit',
                original_partner='Test Partner',
                amount=-100.0,
                currency='HUF',
                account=account,
                deduplication_hash=f'hash-{account}',
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        return [make('acc1'), make('')]

    def _patch_transaction_repo(self, monkeypatch):
        """Patch the transaction repository to return fixed transactions."""
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        transactions = self._make_transactions()
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'find_by_user_with_filters',
            lambda self, **kwargs: (transactions, len(transactions)),
        )

    def test_list_transactions_serializes_empty_account_as_unknown(
        self, api_client_with_mock, monkeypatch
    ):
        """Transactions without an account are exposed as 'unknown' so that
        route params and drilldown filters stay valid."""
        self._patch_transaction_repo(monkeypatch)
        response = api_client_with_mock.get('/api/v2/transactions')

        assert response.status_code == 200
        data = response.get_json()
        accounts = [t['account'] for t in data['transactions']]
        assert accounts == ['acc1', 'unknown']

    def test_aggregate_groups_empty_account_as_unknown(
        self, api_client_with_mock, monkeypatch
    ):
        """Aggregation by account groups empty-account transactions under
        the 'unknown' key."""
        self._patch_transaction_repo(monkeypatch)
        response = api_client_with_mock.get(
            '/api/v2/transactions/aggregate?group_by=account'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert sorted(data['groups'].keys()) == ['acc1', 'unknown']


class TestAPIv2Categories:
    """Test suite for GET /api/v2/categories and /api/v2/categories/cost-of-living."""

    def test_categories_exclude_calculated_categories(self, api_client_with_mock):
        """Calculated categories (aggregates) must not be offered as assignable."""
        response = api_client_with_mock.get('/api/v2/categories')

        assert response.status_code == 200
        ids = [cat['id'] for cat in response.get_json()]
        assert 'grocery' in ids
        assert 'balance' not in ids
        assert 'cost_of_living' not in ids
        assert 'total_spendings' not in ids

    def test_categories_response_shape(self, api_client_with_mock):
        """Each category exposes exactly id, default_name, and patterns."""
        response = api_client_with_mock.get('/api/v2/categories')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        for cat in data:
            assert set(cat.keys()) == {'id', 'default_name', 'patterns'}

    def test_cost_of_living_categories_response_shape(self, api_client_with_mock):
        """Cost of living categories are filtered and have the same shape."""
        response = api_client_with_mock.get('/api/v2/categories/cost-of-living')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        for cat in data:
            assert set(cat.keys()) == {'id', 'default_name', 'patterns'}
        assert all(
            cat['id'] in ('grocery', 'loan', 'transportation', 'utility',
                          'payment', 'fee', 'health')
            for cat in data
        )


class TestAPIv2ProcessingResultDateRange:
    """Test suite for the transaction date range fields on processing results."""

    @staticmethod
    def _make_result(result_id, created_at):
        """Create a ProcessingResult entity without persisting it."""
        from whatsthedamage.models.database.processing_result import (
            ProcessingResult,
        )
        return ProcessingResult(
            result_id=result_id,
            user_id=1,
            csv_profile_id=None,
            row_count=2,
            processing_time=1.0,
            ml_enabled=False,
            start_date=None,
            end_date=None,
            created_at=created_at,
        )

    def _patch_repositories(self, monkeypatch):
        """Patch repositories to serve fixed results and date ranges."""
        from datetime import datetime, UTC
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        from whatsthedamage.models.repositories.processing_result_repository import (
            SqlAlchemyProcessingResultRepository,
        )

        results = [
            self._make_result('result-1', datetime(2026, 1, 2, tzinfo=UTC)),
            self._make_result('result-empty', datetime(2026, 1, 1, tzinfo=UTC)),
        ]
        ranges = {
            'result-1': (
                datetime(2024, 1, 15, tzinfo=UTC),
                datetime(2024, 3, 10, tzinfo=UTC),
            ),
        }

        monkeypatch.setattr(
            SqlAlchemyProcessingResultRepository,
            'find_by_user_id',
            lambda self, user_id, limit=100, offset=0: results,
        )
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'get_date_ranges_by_result_ids',
            lambda self, user_id, result_ids: {
                key: value for key, value in ranges.items()
                if key in result_ids
            },
        )

    def test_list_includes_transaction_date_range(
        self, api_client_with_mock, monkeypatch
    ):
        """The list endpoint reports the min/max transaction dates per result."""
        self._patch_repositories(monkeypatch)
        response = api_client_with_mock.get('/api/v2/processing-results')

        assert response.status_code == 200
        data = response.get_json()
        by_id = {item['id']: item for item in data}

        assert by_id['result-1']['transaction_start_date'] == '2024-01-15'
        assert by_id['result-1']['transaction_end_date'] == '2024-03-10'
        assert by_id['result-empty']['transaction_start_date'] is None
        assert by_id['result-empty']['transaction_end_date'] is None

    def test_single_result_includes_transaction_date_range(
        self, api_client_with_mock, monkeypatch
    ):
        """The single-result endpoint reports the transaction date range."""
        from datetime import datetime, UTC
        from whatsthedamage.models.repositories.transaction_repository import (
            SqlAlchemyTransactionRepository,
        )
        from whatsthedamage.models.repositories.processing_result_repository import (
            SqlAlchemyProcessingResultRepository,
        )

        result = self._make_result('result-1', datetime(2026, 1, 2, tzinfo=UTC))
        ranges = {
            'result-1': (
                datetime(2024, 1, 15, tzinfo=UTC),
                datetime(2024, 3, 10, tzinfo=UTC),
            ),
        }

        monkeypatch.setattr(
            SqlAlchemyProcessingResultRepository,
            'find_by_user_and_result_id',
            lambda self, user_id, result_id: result,
        )
        monkeypatch.setattr(
            SqlAlchemyTransactionRepository,
            'get_date_ranges_by_result_ids',
            lambda self, user_id, result_ids: {
                key: value for key, value in ranges.items()
                if key in result_ids
            },
        )

        response = api_client_with_mock.get('/api/v2/processing-results/result-1')

        assert response.status_code == 200
        data = response.get_json()
        assert data['transaction_start_date'] == '2024-01-15'
        assert data['transaction_end_date'] == '2024-03-10'

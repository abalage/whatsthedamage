"""Tests for DataFormattingService caching and multi-account extraction.

Tests for the new SummaryData model, caching behavior, and multi-account handling.
"""
import pytest
from whatsthedamage.services.data_formatting_service import DataFormattingService, SummaryData
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField


@pytest.fixture
def service():
    """Create a DataFormattingService instance for testing."""
    return DataFormattingService()


@pytest.fixture
def mock_dt_response_account1():
    """Create a mock DataTablesResponse for account 1."""
    return DataTablesResponse(
        data=[
            AggregatedRow(
                month=DateField(display="January", timestamp=1704067200),
                category="Grocery",
                total=DisplayRawField(display="150.50 EUR", raw=150.5),
                details=[]
            ),
            AggregatedRow(
                month=DateField(display="January", timestamp=1704067200),
                category="Utilities",
                total=DisplayRawField(display="80.00 EUR", raw=80.0),
                details=[]
            ),
        ],
        currency="EUR"
    )


@pytest.fixture
def mock_dt_response_account2():
    """Create a mock DataTablesResponse for account 2."""
    return DataTablesResponse(
        data=[
            AggregatedRow(
                month=DateField(display="January", timestamp=1704067200),
                category="Transport",
                total=DisplayRawField(display="200.00 USD", raw=200.0),
                details=[]
            ),
        ],
        currency="USD"
    )


class TestSummaryDataModel:
    """Test suite for SummaryData Pydantic model."""

    def test_summary_data_creation(self):
        """Test SummaryData model creation."""
        summary_data = SummaryData(
            summary={"January": {"Grocery": 150.5}},
            currency="EUR",
            account_id="12345"
        )

        assert summary_data.summary == {"January": {"Grocery": 150.5}}
        assert summary_data.currency == "EUR"
        assert summary_data.account_id == "12345"

    def test_summary_data_immutable(self):
        """Test SummaryData is immutable (frozen)."""
        summary_data = SummaryData(
            summary={"January": {"Grocery": 150.5}},
            currency="EUR",
            account_id="12345"
        )

        with pytest.raises(Exception):  # ValidationError for frozen model
            summary_data.currency = "USD"


class TestExtractSummaryFromAccount:
    """Test suite for _extract_summary_from_account method."""

    def test_extract_single_account(self, service, mock_dt_response_account1):
        """Test extraction from single account."""
        summary_data = service._extract_summary_from_account(
            mock_dt_response_account1,
            "12345"
        )

        assert isinstance(summary_data, SummaryData)
        assert summary_data.account_id == "12345"
        assert summary_data.currency == "EUR"
        assert "January" in summary_data.summary
        assert abs(summary_data.summary["January"]["Grocery"] - 150.5) < 0.01
        assert abs(summary_data.summary["January"]["Utilities"] - 80.0) < 0.01

    def test_extraction_caching(self, service, mock_dt_response_account1):
        """Test that extraction results are cached."""
        # First call
        summary_data1 = service._extract_summary_from_account(
            mock_dt_response_account1,
            "12345"
        )

        # Second call - should return cached result
        summary_data2 = service._extract_summary_from_account(
            mock_dt_response_account1,
            "12345"
        )

        # Should be the same object (from cache)
        assert summary_data1 is summary_data2
        assert "12345" in service._summary_cache

    def test_cache_per_account(self, service, mock_dt_response_account1, mock_dt_response_account2):
        """Test that cache is per account."""
        summary1 = service._extract_summary_from_account(
            mock_dt_response_account1,
            "12345"
        )
        summary2 = service._extract_summary_from_account(
            mock_dt_response_account2,
            "67890"
        )

        assert summary1.account_id == "12345"
        assert summary2.account_id == "67890"
        assert summary1.currency == "EUR"
        assert summary2.currency == "USD"
        assert len(service._summary_cache) == 2


class TestSelectAccount:
    """Test suite for _select_account helper method."""

    def test_single_account_no_id_specified(self, service, mock_dt_response_account1):
        """Test selection with single account and no account_id specified."""
        dt_responses = {"12345": mock_dt_response_account1}

        selected = service._select_account(dt_responses)

        assert selected == "12345"

    def test_single_account_with_id_specified(self, service, mock_dt_response_account1):
        """Test selection with single account and account_id specified."""
        dt_responses = {"12345": mock_dt_response_account1}

        selected = service._select_account(dt_responses, account_id="12345")

        assert selected == "12345"

    def test_multiple_accounts_no_id_raises_error(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test that multiple accounts without account_id raises ValueError."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        with pytest.raises(ValueError) as exc_info:
            service._select_account(dt_responses)

        assert "Multiple accounts found" in str(exc_info.value)
        assert "12345" in str(exc_info.value)
        assert "67890" in str(exc_info.value)

    def test_multiple_accounts_with_valid_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test selection with multiple accounts and valid account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Select account 1
        selected1 = service._select_account(dt_responses, account_id="12345")
        assert selected1 == "12345"

        # Select account 2
        selected2 = service._select_account(dt_responses, account_id="67890")
        assert selected2 == "67890"

    def test_invalid_account_id_raises_error(self, service, mock_dt_response_account1):
        """Test that invalid account_id raises ValueError."""
        dt_responses = {"12345": mock_dt_response_account1}

        with pytest.raises(ValueError) as exc_info:
            service._select_account(dt_responses, account_id="invalid")

        assert "Account 'invalid' not found" in str(exc_info.value)
        assert "12345" in str(exc_info.value)

    def test_empty_responses(self, service):
        """Test selection with empty responses."""
        with pytest.raises(ValueError) as exc_info:
            service._select_account({})

        assert "No account data available" in str(exc_info.value)


class TestWrapperMethodsCaching:
    """Test that wrapper methods benefit from caching."""

    def test_format_datatables_as_html_uses_cache(
        self,
        service,
        mock_dt_response_account1
    ):
        """Test that repeated calls to wrapper methods use cache."""
        dt_responses = {"12345": mock_dt_response_account1}

        # First call
        html1 = service.format_datatables_as_html_table(dt_responses)
        assert "12345" in service._summary_cache

        # Second call should use cache
        html2 = service.format_datatables_as_html_table(dt_responses)

        assert html1 == html2
        assert len(service._summary_cache) == 1

    def test_different_wrapper_methods_share_cache(
        self,
        service,
        mock_dt_response_account1
    ):
        """Test that different wrapper methods share the same cache."""
        dt_responses = {"12345": mock_dt_response_account1}

        # Call different methods
        _ = service.format_datatables_as_html_table(dt_responses)
        _ = service.format_datatables_as_csv(dt_responses)
        _ = service.format_datatables_as_string(dt_responses)

        # Should only have one cached entry
        assert len(service._summary_cache) == 1
        assert "12345" in service._summary_cache


class TestMultiAccountIntegration:
    """Integration tests for multi-account scenarios."""

    def test_format_multiple_accounts_sequentially(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test formatting multiple accounts one by one."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # This should raise error without account_id
        with pytest.raises(ValueError):
            service.format_datatables_as_html_table(dt_responses)

        # But should work with explicit single account
        single_account = {"12345": mock_dt_response_account1}
        html = service.format_datatables_as_html_table(single_account)
        assert "150.50 EUR" in html

    def test_cache_persists_across_service_instance(
        self,
        mock_dt_response_account1
    ):
        """Test that cache is instance-specific."""
        service1 = DataFormattingService()
        service2 = DataFormattingService()

        # Extract in service1
        service1._extract_summary_from_account(mock_dt_response_account1, "12345")

        # service2 should have empty cache
        assert len(service1._summary_cache) == 1
        assert len(service2._summary_cache) == 0

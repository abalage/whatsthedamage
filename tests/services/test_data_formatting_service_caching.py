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


class TestAllWrapperMethodsWithAccountSelection:
    """Test all wrapper methods with explicit account selection."""

    def test_format_datatables_as_html_with_account_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test HTML formatting with explicit account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Format account 1 (EUR)
        html1 = service.format_datatables_as_html_table(dt_responses, account_id="12345")
        assert "150.50 EUR" in html1
        assert "EUR" in html1
        assert "USD" not in html1

        # Format account 2 (USD)
        html2 = service.format_datatables_as_html_table(dt_responses, account_id="67890")
        assert "200.00 USD" in html2
        assert "USD" in html2
        assert "EUR" not in html2

    def test_format_datatables_as_csv_with_account_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test CSV formatting with explicit account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Format account 1 with semicolon delimiter
        csv1 = service.format_datatables_as_csv(dt_responses, account_id="12345", delimiter=";")
        assert "150.50 EUR" in csv1 or "150.5 EUR" in csv1
        assert "Grocery" in csv1

        # Format account 2
        csv2 = service.format_datatables_as_csv(dt_responses, account_id="67890", delimiter=",")
        assert "200.00 USD" in csv2 or "200.0 USD" in csv2
        assert "Transport" in csv2

    def test_format_datatables_as_string_with_account_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test string formatting with explicit account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Format account 1
        string1 = service.format_datatables_as_string(dt_responses, account_id="12345")
        assert "Grocery" in string1
        assert "150.5" in string1 or "150.50" in string1

        # Format account 2
        string2 = service.format_datatables_as_string(dt_responses, account_id="67890")
        assert "Transport" in string2
        assert "200" in string2

    def test_prepare_datatables_summary_table_data_with_account_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test prepare_datatables_summary_table_data with explicit account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Prepare account 1
        headers1, rows1 = service.prepare_datatables_summary_table_data(
            dt_responses,
            account_id="12345"
        )
        assert "January" in headers1
        # Check that data was prepared
        assert len(rows1) > 0

        # Prepare account 2
        headers2, rows2 = service.prepare_datatables_summary_table_data(
            dt_responses,
            account_id="67890"
        )
        assert "January" in headers2
        assert len(rows2) > 0

    def test_format_datatables_for_output_with_account_id(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test format_datatables_for_output with explicit account_id."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Format output for account 1
        output1 = service.format_datatables_for_output(
            dt_responses,
            account_id="12345",
            output_format="html"
        )
        assert "150.50 EUR" in output1
        assert "Grocery" in output1

        # Format output for account 2
        output2 = service.format_datatables_for_output(
            dt_responses,
            account_id="67890",
            output_format="html"
        )
        assert "200.00 USD" in output2
        assert "Transport" in output2


class TestCacheBehaviorUnderEdgeCases:
    """Test caching behavior under edge cases."""

    def test_cache_with_multiple_months(self, service):
        """Test caching with multi-month data."""
        dt_response = DataTablesResponse(
            data=[
                AggregatedRow(
                    month=DateField(display="January", timestamp=1704067200),
                    category="Grocery",
                    total=DisplayRawField(display="100.00 EUR", raw=100.0),
                    details=[]
                ),
                AggregatedRow(
                    month=DateField(display="February", timestamp=1706659200),
                    category="Grocery",
                    total=DisplayRawField(display="150.00 EUR", raw=150.0),
                    details=[]
                ),
                AggregatedRow(
                    month=DateField(display="February", timestamp=1706659200),
                    category="Transport",
                    total=DisplayRawField(display="50.00 EUR", raw=50.0),
                    details=[]
                ),
            ],
            currency="EUR"
        )

        summary_data = service._extract_summary_from_account(dt_response, "multi-month")

        # Check multiple months are extracted
        assert "January" in summary_data.summary
        assert "February" in summary_data.summary
        assert abs(summary_data.summary["January"]["Grocery"] - 100.0) < 0.01
        assert abs(summary_data.summary["February"]["Grocery"] - 150.0) < 0.01
        assert abs(summary_data.summary["February"]["Transport"] - 50.0) < 0.01

        # Verify cached
        assert "multi-month" in service._summary_cache

    def test_cache_with_empty_data(self, service):
        """Test caching with empty DataTablesResponse."""
        dt_response = DataTablesResponse(
            data=[],
            currency="EUR"
        )

        summary_data = service._extract_summary_from_account(dt_response, "empty")

        # Empty summary should still be cached
        assert summary_data.summary == {}
        assert summary_data.currency == "EUR"
        assert "empty" in service._summary_cache

    def test_cache_independence_between_methods(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test that cache works correctly across different wrapper methods."""
        dt_responses = {
            "12345": mock_dt_response_account1,
            "67890": mock_dt_response_account2
        }

        # Call different methods with different accounts
        _ = service.format_datatables_as_html_table(
            {"12345": mock_dt_response_account1},
            account_id="12345"
        )
        _ = service.format_datatables_as_csv(
            {"67890": mock_dt_response_account2},
            account_id="67890"
        )

        # Both should be cached
        assert len(service._summary_cache) == 2
        assert "12345" in service._summary_cache
        assert "67890" in service._summary_cache


class TestErrorHandlingComprehensive:
    """Comprehensive error handling tests."""

    def test_error_message_quality_multiple_accounts(
        self,
        service,
        mock_dt_response_account1,
        mock_dt_response_account2
    ):
        """Test that error messages are clear and helpful."""
        dt_responses = {
            "account_abc": mock_dt_response_account1,
            "account_xyz": mock_dt_response_account2,
            "account_123": mock_dt_response_account1
        }

        with pytest.raises(ValueError) as exc_info:
            service.format_datatables_as_html_table(dt_responses)

        error_msg = str(exc_info.value)
        # Check all account IDs are mentioned
        assert "account_abc" in error_msg
        assert "account_xyz" in error_msg
        assert "account_123" in error_msg
        assert "Multiple accounts" in error_msg

    def test_error_on_invalid_account_all_methods(
        self,
        service,
        mock_dt_response_account1
    ):
        """Test that all wrapper methods raise error for invalid account_id."""
        dt_responses = {"12345": mock_dt_response_account1}

        methods = [
            lambda: service.format_datatables_as_html_table(dt_responses, account_id="invalid"),
            lambda: service.format_datatables_as_csv(dt_responses, account_id="invalid"),
            lambda: service.format_datatables_as_string(dt_responses, account_id="invalid"),
            lambda: service.prepare_datatables_summary_table_data(dt_responses, account_id="invalid"),
            lambda: service.format_datatables_for_output(dt_responses, account_id="invalid")
        ]

        for method in methods:
            with pytest.raises(ValueError) as exc_info:
                method()
            assert "not found" in str(exc_info.value)
            assert "12345" in str(exc_info.value)

    def test_no_error_when_single_account_and_no_id(
        self,
        service,
        mock_dt_response_account1
    ):
        """Test that single account works without specifying account_id."""
        single_account = {"only_account": mock_dt_response_account1}

        # All methods should work without account_id
        html = service.format_datatables_as_html_table(single_account)
        assert "150.50 EUR" in html

        csv = service.format_datatables_as_csv(single_account)
        assert "Grocery" in csv

        string_out = service.format_datatables_as_string(single_account)
        assert "Grocery" in string_out

        headers, _ = service.prepare_datatables_summary_table_data(single_account)
        assert "January" in headers

        output = service.format_datatables_for_output(single_account)
        assert "EUR" in output

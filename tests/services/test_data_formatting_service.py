"""Tests for DataFormattingService.

Comprehensive test suite using parametrized tests for maintainability.
"""
import pytest
import json
import pandas as pd
from whatsthedamage.services.data_formatting_service import DataFormattingService


@pytest.fixture
def service():
    """Create a DataFormattingService instance for testing."""
    return DataFormattingService()


@pytest.fixture
def single_month_data():
    """Single month data for testing."""
    return {"Total": {"Grocery": 150.5, "Utilities": 80.0}}


class TestFormatAsHtmlTable:
    """Test suite for HTML table formatting."""

    @pytest.mark.parametrize("currency,expected", [
        ("EUR", "150.50 EUR"),
        ("USD", "150.50 USD"),
        ("HUF", "150.50 HUF"),
    ])
    def test_format_with_currencies(self, service, single_month_data, currency, expected):
        """Test HTML formatting with different currencies."""
        html = service.format_as_html_table(single_month_data, currency)
        assert expected in html
        assert "<table" in html and "<thead>" in html

    @pytest.mark.parametrize("no_currency,should_have_currency", [
        (False, True),
        (True, False),
    ])
    def test_currency_formatting_toggle(self, service, single_month_data, no_currency, should_have_currency):
        """Test enabling/disabling currency formatting."""
        html = service.format_as_html_table(single_month_data, "EUR", no_currency_format=no_currency)
        has_currency = "150.50 EUR" in html
        assert has_currency == should_have_currency

    @pytest.mark.parametrize("header_text", ["Categories", "Category", "Type"])
    def test_custom_categories_header(self, service, single_month_data, header_text):
        """Test custom categories headers."""
        html = service.format_as_html_table(single_month_data, "EUR", categories_header=header_text)
        assert f"<th>{header_text}</th>" in html

    @pytest.mark.parametrize("data,categories", [
        ({"Total": {}}, []),
        ({"Total": {"A": 10.0}}, ["A"]),
        ({"Total": {"Zebra": 10.0, "Apple": 20.0, "Monkey": 15.0}}, ["Apple", "Monkey", "Zebra"]),
    ])
    def test_category_handling(self, service, data, categories):
        """Test category sorting and presence in HTML."""
        html = service.format_as_html_table(data, "EUR")
        for cat in categories:
            assert cat in html
        # Verify alphabetical sorting
        if len(categories) > 1:
            positions = [html.find(cat) for cat in categories]
            assert positions == sorted(positions)

    def test_nan_handling(self, service):
        """Test that NaN values are replaced with 0."""
        data = {"Month1": {"Cat1": float('nan'), "Cat2": 50.0}}
        html = service.format_as_html_table(data, "EUR")
        assert "0.00 EUR" in html

    def test_nowrap_option(self, service, single_month_data):
        """Test nowrap option affects pandas settings."""
        service.format_as_html_table(single_month_data, "EUR", nowrap=True)
        assert pd.get_option('display.expand_frame_repr') is False


class TestFormatAsCsv:
    """Test suite for CSV formatting."""

    @pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
    def test_delimiters(self, service, single_month_data, delimiter):
        """Test CSV formatting with different delimiters."""
        csv = service.format_as_csv(single_month_data, "EUR", delimiter=delimiter)
        assert delimiter in csv

    @pytest.mark.parametrize("no_currency,should_have", [
        (False, "150.50 EUR"),
        (True, "150.5"),
    ])
    def test_currency_in_csv(self, service, single_month_data, no_currency, should_have):
        """Test currency presence in CSV output."""
        csv = service.format_as_csv(single_month_data, "EUR", no_currency_format=no_currency)
        assert should_have in csv or "150.50" in csv

    def test_csv_structure(self, service, single_month_data):
        """Test CSV contains expected headers and data."""
        csv = service.format_as_csv(single_month_data, "EUR")
        assert "Total" in csv
        assert "Grocery" in csv
        assert "Utilities" in csv


class TestFormatAsJson:
    """Test suite for JSON formatting."""

    @pytest.mark.parametrize("data,expected_keys", [
        ({"grocery": 150.5}, ["grocery"]),
        ({}, []),
        ({"a": 1, "b": 2}, ["a", "b"]),
    ])
    def test_json_structure(self, service, data, expected_keys):
        """Test JSON formatting with various data structures."""
        json_str = service.format_as_json(data)
        parsed = json.loads(json_str)
        assert list(parsed.keys()) == expected_keys

    @pytest.mark.parametrize("pretty,has_newlines", [
        (True, True),
        (False, False),
    ])
    def test_pretty_print(self, service, pretty, has_newlines):
        """Test pretty print option."""
        json_str = service.format_as_json({"key": "value"}, pretty=pretty)
        assert ("\n" in json_str and "  " in json_str) == has_newlines

    @pytest.mark.parametrize("data", [
        {"key": None},
        {"nested": {"key": "value"}},
        {"list": [1, 2, 3]},
        {"unicode": "Árvíztűrő tükörfúrógép"},
    ])
    def test_complex_data_types(self, service, data):
        """Test JSON with complex data types."""
        json_str = service.format_as_json(data)
        assert json.loads(json_str) == data


class TestFormatCurrency:
    """Test suite for currency formatting."""

    @pytest.mark.parametrize("value,currency,decimal_places,expected", [
        (150.5, "EUR", 2, "150.50 EUR"),
        (0.0, "USD", 2, "0.00 USD"),
        (1000.123, "HUF", 2, "1000.12 HUF"),
        (-50.75, "GBP", 2, "-50.75 GBP"),
        (150.5, "EUR", 0, "150 EUR"),
        (150.5, "EUR", 3, "150.500 EUR"),
    ])
    def test_currency_formatting(self, service, value, currency, decimal_places, expected):
        """Test currency formatting with various parameters."""
        result = service.format_currency(value, currency, decimal_places=decimal_places)
        assert result == expected

    @pytest.mark.parametrize("value,expected", [
        (150.567, "150.57 EUR"),
        (150.564, "150.56 EUR"),
    ])
    def test_rounding(self, service, value, expected):
        """Test currency rounding behavior."""
        assert service.format_currency(value, "EUR") == expected


class TestPrepareSummaryTableData:
    """Test suite for prepare_summary_table_data method."""

    def test_prepare_summary_data_basic(self, service):
        """Test basic summary data preparation."""
        data = {"January": {"Grocery": 150.5, "Utilities": 80.0}}
        headers, rows = service.prepare_summary_table_data(data, "EUR")

        assert headers == ["Categories", "January"]
        assert len(rows) == 2

        # Check Grocery row
        assert rows[0][0]['display'] == "Grocery"
        assert rows[0][0]['order'] is None
        assert rows[0][1]['display'] == "150.50 EUR"
        assert abs(rows[0][1]['order'] - 150.5) < 0.01

        # Check Utilities row
        assert rows[1][0]['display'] == "Utilities"
        assert rows[1][1]['display'] == "80.00 EUR"

    def test_prepare_summary_data_multiple_months(self, service):
        """Test preparation with multiple months."""
        data = {
            "January": {"Grocery": 150.5},
            "February": {"Grocery": 200.0}
        }
        headers, rows = service.prepare_summary_table_data(data, "USD")

        assert headers == ["Categories", "January", "February"]
        assert rows[0][0]['display'] == "Grocery"
        assert rows[0][1]['display'] == "150.50 USD"
        assert rows[0][2]['display'] == "200.00 USD"

    def test_prepare_summary_data_no_currency_format(self, service):
        """Test preparation without currency formatting."""
        data = {"Total": {"Grocery": 150.5}}
        _, rows = service.prepare_summary_table_data(
            data, "EUR", no_currency_format=True
        )

        assert rows[0][1]['display'] == "150.50"
        assert "EUR" not in rows[0][1]['display']

    def test_prepare_summary_data_custom_header(self, service):
        """Test preparation with custom categories header."""
        data = {"Total": {"Grocery": 100.0}}
        headers, _ = service.prepare_summary_table_data(
            data, "EUR", categories_header="Types"
        )

        assert headers[0] == "Types"

    @pytest.mark.parametrize("value", [0, 0.0, 150.567])
    def test_prepare_summary_data_various_values(self, service, value):
        """Test preparation with various numeric values."""
        data = {"Total": {"Test": value}}
        _, rows = service.prepare_summary_table_data(data, "EUR")

        assert isinstance(rows[0][1]['order'], float)
        assert abs(rows[0][1]['order'] - value) < 0.01


class TestIntegration:
    """Integration tests for end-to-end scenarios."""

    def test_format_and_prepare_data(self, service, single_month_data):
        """Test formatting and data preparation."""
        _ = service.format_as_html_table(single_month_data, "EUR")
        headers, rows = service.prepare_summary_table_data(single_month_data, "EUR")

        assert "Categories" in headers and "Total" in headers
        assert len(rows) == 2

    def test_multiple_formats_consistency(self, service, single_month_data):
        """Test data consistency across formats."""
        html = service.format_as_html_table(single_month_data, "EUR")
        csv = service.format_as_csv(single_month_data, "EUR")

        for cat in ["Grocery", "Utilities"]:
            assert cat in html and cat in csv
        assert "150.50 EUR" in html and "150.50 EUR" in csv


class TestFormatForOutput:
    """Test suite for the comprehensive format_for_output method."""

    def test_html_output_format(self, service, single_month_data):
        """Test format_for_output with HTML format."""
        result = service.format_for_output(
            single_month_data,
            "EUR",
            output_format="html"
        )
        assert "<table" in result
        assert "150.50 EUR" in result

    def test_csv_file_output(self, service, single_month_data, tmp_path):
        """Test format_for_output with file output."""
        output_file = tmp_path / "test.csv"
        result = service.format_for_output(
            single_month_data,
            "EUR",
            output_file=str(output_file)
        )
        assert output_file.exists()
        content = output_file.read_text()
        assert "Grocery" in content
        assert result == content

    def test_string_output_default(self, service, single_month_data):
        """Test format_for_output with default string output."""
        result = service.format_for_output(single_month_data, "EUR")
        assert "Grocery" in result
        assert "150.50 EUR" in result

    @pytest.mark.parametrize("no_currency,should_have", [
        (False, True),
        (True, False),
    ])
    def test_currency_toggle_in_output(self, service, single_month_data, no_currency, should_have):
        """Test currency formatting toggle in format_for_output."""
        result = service.format_for_output(
            single_month_data,
            "EUR",
            no_currency_format=no_currency
        )
        has_currency = "150.50 EUR" in result
        assert has_currency == should_have

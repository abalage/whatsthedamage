import pytest
import pandas as pd
from whatsthedamage.models.data_frame_formatter import DataFrameFormatter


@pytest.fixture
def formatter():
    return DataFrameFormatter()


def test_set_nowrap(formatter):
    formatter.set_nowrap(True)
    assert formatter._nowrap is True

    formatter.set_nowrap(False)
    assert formatter._nowrap is False


def test_set_no_currency_format(formatter):
    formatter.set_no_currency_format(True)
    assert formatter._no_currency_format is True

    formatter.set_no_currency_format(False)
    assert formatter._no_currency_format is False


def test_format_dataframe_with_currency(formatter):
    data = {
        "Category1": {"Item1": 10.5, "Item2": 20.75},
        "Category2": {"Item1": 5.0, "Item2": 15.25}
    }
    currency = "EUR"
    expected_data = {
        "Category1": {"Item1": "10.50 EUR", "Item2": "20.75 EUR"},
        "Category2": {"Item1": "5.00 EUR", "Item2": "15.25 EUR"}
    }
    expected_df = pd.DataFrame(expected_data).sort_index()

    result_df = formatter.format_dataframe(data, currency)

    pd.testing.assert_frame_equal(result_df, expected_df)


def test_format_dataframe_without_currency(formatter):
    formatter.set_no_currency_format(True)
    data = {
        "Category1": {"Item1": 10.5, "Item2": 20.75},
        "Category2": {"Item1": 5.0, "Item2": 15.25}
    }
    currency = "EUR"
    expected_df = pd.DataFrame(data).sort_index()

    result_df = formatter.format_dataframe(data, currency)

    pd.testing.assert_frame_equal(result_df, expected_df)


def test_format_dataframe_with_nowrap(formatter):
    formatter.set_nowrap(True)
    data = {
        "Category1": {"Item1": 10.5, "Item2": 20.75},
        "Category2": {"Item1": 5.0, "Item2": 15.25}
    }
    currency = "EUR"
    formatter.format_dataframe(data, currency)

    assert pd.get_option('display.expand_frame_repr') is False


def test_format_dataframe_with_empty_data(formatter):
    data = {}
    currency = "EUR"
    expected_df = pd.DataFrame(data)

    result_df = formatter.format_dataframe(data, currency)

    pd.testing.assert_frame_equal(result_df, expected_df)


def test_format_dataframe_with_non_numeric_values(formatter):
    data = {
        "Category1": {"Item1": "N/A", "Item2": 20.75},
        "Category2": {"Item1": 5.0, "Item2": "Unknown"}
    }
    currency = "EUR"
    expected_data = {
        "Category1": {"Item1": "N/A", "Item2": "20.75 EUR"},
        "Category2": {"Item1": "5.00 EUR", "Item2": "Unknown"}
    }
    expected_df = pd.DataFrame(expected_data).sort_index()

    result_df = formatter.format_dataframe(data, currency)

    pd.testing.assert_frame_equal(result_df, expected_df)

import pytest
import pandas as pd
from whatsthedamage.data_frame_formatter import DataFrameFormatter
import locale


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


def test_format_dataframe_without_currency_format(formatter):
    formatter.set_no_currency_format(True)
    data = {
        'Category1': {'Item1': 10.0, 'Item2': 20.0},
        'Category2': {'Item1': 30.0, 'Item2': 40.0}
    }
    df = formatter.format_dataframe(data)
    expected_df = pd.DataFrame(data).sort_index()
    pd.testing.assert_frame_equal(df, expected_df)


def test_format_dataframe_with_currency_format(formatter):
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    data = {
        'Category1': {'Item1': 10.0, 'Item2': 20.0},
        'Category2': {'Item1': 30.0, 'Item2': 40.0}
    }
    formatter.set_no_currency_format(False)
    df = formatter.format_dataframe(data)

    def format_currency(value):
        return locale.currency(value, grouping=True)

    expected_data = {
        'Category1': {'Item1': format_currency(10.0), 'Item2': format_currency(20.0)},
        'Category2': {'Item1': format_currency(30.0), 'Item2': format_currency(40.0)}
    }
    expected_df = pd.DataFrame(expected_data).sort_index()
    pd.testing.assert_frame_equal(df, expected_df)


def test_format_dataframe_with_none_values(formatter):
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    data = {
        'Category1': {'Item1': None, 'Item2': 20.0},
        'Category2': {'Item1': 30.0, 'Item2': None}
    }
    formatter.set_no_currency_format(False)
    df = formatter.format_dataframe(data)

    def format_currency(value):
        if value is None:
            return 'N/A'
        return locale.currency(value, grouping=True)

    expected_data = {
        'Category1': {'Item1': '$nan', 'Item2': format_currency(20.0)},
        'Category2': {'Item1': format_currency(30.0), 'Item2': '$nan'}
    }
    expected_df = pd.DataFrame(expected_data).sort_index()
    pd.testing.assert_frame_equal(df, expected_df)

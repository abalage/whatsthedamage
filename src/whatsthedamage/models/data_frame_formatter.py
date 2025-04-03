import pandas as pd
import locale
from typing import Dict

"""
A module for formatting pandas DataFrames with optional currency formatting and nowrap options.
"""


def format_currency(value: float) -> str:
    """
    Formats a numeric value as a currency string.

    :param value: The numeric value to format. Must be a float.
    :return: The formatted currency string.
    :raises TypeError: If the value is not a float.
    """
    if not isinstance(value, float):
        raise TypeError(f"Expected a float, but got {type(value).__name__}")
    return locale.currency(value, grouping=True)


class DataFrameFormatter:
    def __init__(self) -> None:
        """
        Initializes the DataFrameFormatter with default settings.
        Attributes:
            _nowrap (bool): If True, disables text wrapping. Default is False.
            _no_currency_format (bool): If True, disables currency formatting. Default is False.
        """
        self._nowrap: bool = False
        self._no_currency_format: bool = False

    def set_nowrap(self, nowrap: bool) -> None:
        """
        Set the nowrap attribute.

        :param nowrap: If True, disables text wrapping.
        """
        self._nowrap = nowrap

    def set_no_currency_format(self, no_currency_format: bool) -> None:
        """
        Set the no_currency_format attribute.

        :param no_currency_format: If True, disables currency formatting.
        """
        self._no_currency_format = no_currency_format

    def format_dataframe(self, data_for_pandas: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Formats a given dictionary of data into a pandas DataFrame with optional currency formatting.

        :param data_for_pandas: The input data to be formatted into a DataFrame.
            The outer dictionary keys represent the columns, and the inner dictionary keys represent the rows.
        :return: The formatted DataFrame with optional currency formatting.
        """
        # Set pandas to display all columns and rows without truncation
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        if self._nowrap:
            pd.set_option('display.expand_frame_repr', False)

        # Create a DataFrame from the data
        df = pd.DataFrame(data_for_pandas)

        # Sort the DataFrame by index (which are the categories)
        df = df.sort_index()

        # Format the DataFrame with currency values
        if not self._no_currency_format:
            df = df.apply(lambda row: row.apply(format_currency), axis=1)
        return df

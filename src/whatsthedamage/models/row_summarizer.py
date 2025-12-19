from typing import Mapping, Sequence
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import get_category_name

class RowSummarizer:
    def __init__(self, rows: Mapping[str, Sequence[CsvRow]]) -> None:
        """
        Initialize the RowSummarizer with a dictionary of categorized CsvRow objects.

        :param rows: Dictionary with category names as keys and lists of CsvRow objects as values.
        """
        self._rows = rows

    def summarize(self) -> dict[str, float]:
        """
        Summarize the values of the 'amount' attribute in categorized rows.

        :return: A dictionary with category names as keys and total values as values.
                 Adds an overall balance as a key 'balance'.
                 Adds total spendings (sum of negative amounts) as a key 'total_spendings'.
        """
        categorized_rows = self._rows
        summary: dict[str, float] = {}

        balance = 0.0
        total_spendings = 0.0
        for category, rows in categorized_rows.items():
            total = 0.0
            for row in rows:
                value = getattr(row, 'amount', 0)
                try:
                    float_value = float(value)
                    total += float_value
                    balance += float_value
                    # Track total spendings (negative amounts = money going out)
                    if float_value < 0:
                        total_spendings += abs(float_value)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert value '{value}' to float for category '{category}'")
            summary[category] = total

        summary[get_category_name('balance')] = balance
        summary[get_category_name('total_spendings')] = total_spendings
        return summary

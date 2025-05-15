from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import get_category_name


class RowSummarizer:
    def __init__(self, rows: Dict[str, List[CsvRow]]) -> None:
        """
        Initialize the RowSummarizer with a dictionary of categorized CsvRow objects.

        :param rows: Dictionary with category names as keys and lists of CsvRow objects as values.
        """
        self._rows = rows

    def summarize(self) -> Dict[str, float]:
        """
        Summarize the values of the 'amount' attribute in categorized rows.

        :return: A dictionary with category names as keys and total values as values.
                 Adds an overall balance as a key 'balance'.
        """
        categorized_rows = self._rows
        summary: Dict[str, float] = {}

        balance = 0.0
        for category, rows in categorized_rows.items():
            total = 0.0
            for row in rows:
                value = getattr(row, 'amount', 0)
                try:
                    total += float(value)  # Convert to float for summation
                    balance += float(value)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert value '{value}' to float for category '{category}'")
            summary[category] = total

        summary[get_category_name('balance')] = balance
        return summary

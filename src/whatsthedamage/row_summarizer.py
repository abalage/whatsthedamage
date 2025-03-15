from whatsthedamage.csv_row import CsvRow


class RowSummarizer:
    def __init__(self, rows: dict[str, list['CsvRow']]) -> None:
        """
        Initialize the RowSummarizer with a list of CsvRow objects.

        :param rows: List of CsvRow objects to summarize.
        """
        self.rows = rows

    def summarize(self) -> dict[str, float]:
        """
        Summarize the values of the 'amount' attribute in categorized rows.

        :return: A dictionary with category names as keys and formatted total values as values.
        Adding overall balance as a key 'balance'.
        """
        categorized_rows = self.rows
        summary: dict[str, float] = {}

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

        summary['balance'] = balance
        return summary

from whatsthedamage.csv_row import CsvRow


class RowSummarizer:
    def __init__(self, rows: dict[str, list['CsvRow']], sum_attribute: str) -> None:
        """
        Initialize the RowSummarizer with a list of CsvRow objects.

        :param rows: List of CsvRow objects to summarize.
        :param sum_attribute: CSV attribute containing the amount to be summarized.
        """
        self.rows = rows
        self.sum_attribute = sum_attribute

    def summarize(self) -> dict[str, float]:
        """
        Summarize the values of a specified attribute in categorized rows.

        :return: A dictionary with category names as keys and formatted total values as values.
        Adding overall balance as a key 'balance'.
        """
        categorized_rows = self.rows
        summary: dict[str, float] = {}

        balance = 0.0
        for category, rows in categorized_rows.items():
            total = 0.0
            for row in rows:
                value = getattr(row, self.sum_attribute, 0)
                try:
                    total += float(value)  # Convert to float for summation
                    balance += float(value)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert value '{value}' to float for category '{category}'")
            summary[category] = total

        summary['balance'] = balance
        return summary

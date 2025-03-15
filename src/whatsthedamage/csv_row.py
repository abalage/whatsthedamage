# Class representing a single row of data in the CSV file
class CsvRow:
    def __init__(self, row: dict[str, str], mapping: dict[str, str]) -> None:
        """
        Initialize the CsvRow object with header values as attributes.

        :param row: Key-value pairs representing the CSV header and corresponding values.
        :param mapping: Mapping of standardized attributes to CSV headers.
        """
        self.date = row.get(mapping.get('date', ''), '')
        self.type = row.get(mapping.get('type', ''), '')
        self.partner = row.get(mapping.get('partner', ''), '')
        self.amount = row.get(mapping.get('amount', ''), '')
        self.currency = row.get(mapping.get('currency', ''), '')

    def __repr__(self) -> str:
        """
        Return a string representation of the CsvRow object for easy printing.

        :return: A string representation of the CsvRow.
        """
        return (
            f"<CsvRow("
            f"date={self.date}, "
            f"type={self.type}, "
            f"partner={self.partner}, "
            f"amount={self.amount}, "
            f"currency={self.currency}"
            f")>"
        )

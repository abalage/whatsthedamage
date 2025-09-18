# Class representing a single row of data in the CSV file
class CsvRow:
    def __init__(self, row: dict[str, str], mapping: dict[str, str]) -> None:
        """
        Initialize the CsvRow object with header values as attributes.

        :param row: Key-value pairs representing the CSV header and corresponding values.
        :param mapping: Mapping of standardized attributes to CSV headers.
        """
        self.date = row.get(mapping.get('date', ''), '').strip()
        self.type = row.get(mapping.get('type', ''), '').strip()
        self.partner = row.get(mapping.get('partner', ''), '').strip()
        self.amount = float(row.get(mapping.get('amount', ''), 0))
        self.currency = row.get(mapping.get('currency', ''), '').strip()
        self.category = row.get(mapping.get('category', ''), '').strip()

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
            f"currency={self.currency}, "
            f"category={self.category}"
            f")>"
        )

    def __eq__(self, other: object) -> bool:
        """
        Check if two CsvRow objects are equal based on their attributes.

        :param other: The other CsvRow object to compare with.
        :return: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, CsvRow):
            return False
        return (
            self.date == other.date and
            self.type == other.type and
            self.partner == other.partner and
            self.amount == other.amount and
            self.currency == other.currency and
            self.category == other.category
        )

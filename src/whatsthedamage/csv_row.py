# Class representing a single row of data in the CSV file
class CsvRow:
    def __init__(self, row: dict[str, str]) -> None:
        """
        Initialize the CsvRow object with header values as attributes.

        :param kwargs: Key-value pairs representing the CSV header and corresponding values.
        """
        for key, value in row.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        """
        Return a string representation of the CsvRow object for easy printing.

        :return: A string representation of the CsvRow.
        """
        return f"<CsvRow({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})>"

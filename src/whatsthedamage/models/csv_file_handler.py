import csv
from typing import Sequence, Dict, List
from whatsthedamage.models.csv_row import CsvRow


class CsvFileHandler:
    def __init__(
            self,
            filename: str,
            dialect: str = 'excel-tab',
            delimiter: str = '\t',
            mapping: Dict[str, str] = {}):
        """
        Initialize the CsvFileReader with the path to the CSV file, dialect, delimiter, and optional mapping.

        :param filename: The path to the CSV file to read.
        :param dialect: The dialect to use for the CSV reader.
        :param delimiter: The delimiter to use for the CSV reader.
        :param mapping: Dictionary to map CSV column names to different names.
        """
        self._filename: str = filename
        self._dialect: str = dialect
        self._delimiter: str = delimiter
        self._headers: Sequence[str] = []  # List to store header names
        self._rows: List[CsvRow] = []  # List to store CsvRow objects
        self._mapping: Dict[str, str] = mapping

    def read(self) -> None:
        """
        Read the CSV file and populate headers and rows.

        :return: None
        """
        try:
            with open(self._filename, mode='r', newline='', encoding='utf-8') as file:
                csvreader = csv.DictReader(file, dialect=self._dialect, delimiter=self._delimiter, restkey='leftover')
                if csvreader.fieldnames is None or all(fieldname is None for fieldname in csvreader.fieldnames):
                    raise ValueError("CSV file is empty or missing headers.")
                self._headers = csvreader.fieldnames  # Save the header
                self._rows = [CsvRow(row, self._mapping) for row in csvreader]
                if not self._rows:
                    raise ValueError("CSV file is empty or missing headers.")
        except FileNotFoundError:
            print(f"Error: The file '{self._filename}' was not found.")
            raise
        except Exception as e:
            print(f"An error occurred while reading the CSV file: {e}")
            raise

    def get_headers(self) -> Sequence[str]:
        """
        Get the headers of the CSV file.

        :return: A list of header names.
        """
        return self._headers

    def get_rows(self) -> List[CsvRow]:
        """
        Get the rows of the CSV file as CsvRow objects.

        :return: A list of CsvRow objects.
        """
        return self._rows

    def write(self, filename: str, rows: List[CsvRow]) -> None:
        """
        Write the CsvRow objects into a CSV file.

        :param filename: The path to the CSV file to write.
        :param rows: A list of CsvRow objects to write to the file.
        :return: None
        """
        if not rows:
            raise ValueError("No rows to write to the CSV file.")

        headers = list(self._mapping.keys())

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=headers, dialect=self._dialect, delimiter=self._delimiter)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row.__dict__)
        except Exception as e:
            print(f"An error occurred while writing to the CSV file: {e}")

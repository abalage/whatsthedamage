from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.csv_file_handler import CsvFileHandler
from whatsthedamage.models.rows_processor import RowsProcessor
from whatsthedamage.config.config import AppContext
from whatsthedamage.models.dt_models import DataTablesResponse


class CSVProcessor:
    """
    CSVProcessor encapsulates the processing of CSV files. It reads the CSV file,
    processes the rows using RowsProcessor, and formats the data for output.

    Attributes:
        config (AppConfig): The configuration object.
        args (AppArgs): The application arguments.
        processor (RowsProcessor): The RowsProcessor instance used to process the rows.
    """

    def __init__(self, context: AppContext) -> None:
        """
        Initializes the CSVProcessor with configuration and arguments.

        Args:
            config (AppConfig): The configuration object.
            args (AppArgs): The application arguments.
        """
        self.context = context
        self.config = context.config
        self.args = context.args
        self.processor = RowsProcessor(self.context)
        self._rows: List[CsvRow] = []  # Cache for rows to avoid re-reading

    def process(self) -> Dict[str, DataTablesResponse]:
        """
        Processes the CSV file and returns the DataTablesResponse structure for DataTables frontend (API v2).
        Only used for ML categorization.

        Returns:
            Dict[str, DataTablesResponse]: The DataTables-compatible structure for frontend.
        """
        self._rows = self._read_csv_file()
        return self.processor.process_rows(self._rows)

    def _read_csv_file(self) -> List[CsvRow]:
        """
        Reads the CSV file and returns the rows.

        Returns:
            List[CsvRow]: The list of CsvRow objects.
        """
        csv_reader = CsvFileHandler(
            str(self.args.filename),
            str(self.config.csv.dialect),
            str(self.config.csv.delimiter),
            dict(self.config.csv.attribute_mapping)
        )
        csv_reader.read()
        return csv_reader.get_rows()

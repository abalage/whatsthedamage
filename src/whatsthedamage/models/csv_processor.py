from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.csv_file_handler import CsvFileHandler
from whatsthedamage.models.rows_processor import RowsProcessor
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.config.config import AppContext
from whatsthedamage.config.dt_models import DataTablesResponse
from gettext import gettext as _


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

    def process(self) -> str:
        """
        Processes the CSV file and returns the formatted result.

        Returns:
            str: The formatted result as a string or None.
        """
        rows = self._read_csv_file()
        data_for_pandas = self.processor.process_rows(rows)
        return self._format_data(data_for_pandas)

    def process_v2(self) -> 'DataTablesResponse':
        """
        Processes the CSV file and returns the DataTablesResponse structure for DataTables frontend (API v2).
        Only used for ML categorization.

        Returns:
            DataTablesResponse: The DataTables-compatible structure for frontend.
        """
        rows = self._read_csv_file()
        return self.processor.process_rows_v2(rows)

    def _read_csv_file(self) -> List[CsvRow]:
        """
        Reads the CSV file and returns the rows.

        Returns:
            List[CsvRow]: The list of CsvRow objects.
        """
        csv_reader = CsvFileHandler(
            str(self.args['filename']),
            str(self.config.csv.dialect),
            str(self.config.csv.delimiter),
            dict(self.config.csv.attribute_mapping)
        )
        csv_reader.read()
        return csv_reader.get_rows()

    def _format_data(self, data_for_pandas: Dict[str, Dict[str, float]]) -> str:
        """
        Formats the data using DataFormattingService.

        Args:
            data_for_pandas (Dict[str, Dict[str, float]]): The data to format.

        Returns:
            str: The formatted data as a string or None.
        """
        formatting_service = DataFormattingService()

        return formatting_service.format_for_output(
            data=data_for_pandas,
            currency=self.processor.get_currency(),
            output_format=self.args.get('output_format'),
            output_file=self.args.get('output'),
            nowrap=self.args.get('nowrap', False),
            no_currency_format=self.args.get('no_currency_format', False),
            categories_header=_("Categories")
        )

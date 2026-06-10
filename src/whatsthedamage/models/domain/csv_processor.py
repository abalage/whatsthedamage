from typing import Dict, List
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.models.domain.csv_file_handler import CsvFileHandler
from whatsthedamage.models.domain.rows_processor import RowsProcessor
from whatsthedamage.config.config import AppContext
from whatsthedamage.models.domain.dt_models import AccountResponse
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


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
            context (AppContext): The application context containing configuration and arguments.
        """
        self.context = context
        self.config = context.config
        self.args = context.args
        self.processor = RowsProcessor(self.context)
        self._rows: List[CsvRow] = []  # Cache for rows to avoid re-reading

    def process(self) -> Dict[str, AccountResponse]:
        """
        Processes the CSV file and returns the AccountResponse structure for frontend (API v2).
        Only used for ML categorization.

        Returns:
            Dict[str, AccountResponse]: The account-compatible structure for frontend.
        """
        logger.info(f"Processing CSV file: {self.args.filename}")
        self._rows = self._read_csv_file()
        logger.debug(f"Read {len(self._rows)} rows from CSV file")
        result = self.processor.process_rows(self._rows)
        logger.info(f"Completed CSV processing with {len(result)} account responses")
        return result

    def _read_csv_file(self) -> List[CsvRow]:
        """
        Reads the CSV file and returns the rows.

        Returns:
            List[CsvRow]: The list of CsvRow objects.
        """
        logger.info(f"Reading CSV file: {self.args.filename}")
        try:
            csv_reader = CsvFileHandler(
                str(self.args.filename),
                str(self.config.csv.dialect),
                str(self.config.csv.delimiter),
                dict(self.config.csv.attribute_mapping)
            )
            csv_reader.read()
            rows = csv_reader.get_rows()
            logger.info(f"Successfully read {len(rows)} rows from CSV file")
            return rows
        except Exception as e:
            logger.error(f"Failed to read CSV file {self.args.filename}: {e}")
            raise

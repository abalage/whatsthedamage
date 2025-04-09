from typing import Dict, List
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.csv_file_handler import CsvFileHandler
from whatsthedamage.models.rows_processor import RowsProcessor
from whatsthedamage.models.data_frame_formatter import DataFrameFormatter
from whatsthedamage.config.config import AppContext


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
        Formats the data using DataFrameFormatter.

        Args:
            data_for_pandas (Dict[str, Dict[str, float]]): The data to format.

        Returns:
            str: The formatted data as a string or None.
        """
        formatter = DataFrameFormatter()
        formatter.set_nowrap(self.args.get('nowrap', False))
        formatter.set_no_currency_format(self.args.get('no_currency_format', False))
        currency = self.processor.get_currency()
        df = formatter.format_dataframe(data_for_pandas, currency=currency)

        if self.args.get('output_format') == 'html':
            return df.to_html(border=0)
        elif self.args.get('output'):
            if self.args.get('output'):
                # FIXME normally returns None but confuses callers, stringify it
                return str(df.to_csv(self.args.get('output'), index=True, header=True, sep=';', decimal=','))
            else:
                # always returns string
                return df.to_csv(None, index=True, header=True, sep=';', decimal=',')
        else:
            return df.to_string()

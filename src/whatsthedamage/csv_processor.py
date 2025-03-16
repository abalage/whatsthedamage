from whatsthedamage.csv_row import CsvRow
from whatsthedamage.csv_file_reader import CsvFileReader
from whatsthedamage.rows_processor import RowsProcessor
from whatsthedamage.data_frame_formatter import DataFrameFormatter
from whatsthedamage.config import AppArgs, AppConfig, load_config


class CSVProcessor:
    """
    CSVProcessor encapsulates the processing of CSV files. It reads the CSV file,
    processes the rows using RowsProcessor, and formats the data for output.

    Attributes:
        config (AppConfig): The configuration object.
        args (AppArgs): The application arguments.
        processor (RowsProcessor): The RowsProcessor instance used to process the rows.
    """

    def __init__(self, config: AppConfig, args: AppArgs) -> None:
        """
        Initializes the CSVProcessor with configuration and arguments.

        Args:
            config (AppConfig): The configuration object.
            args (AppArgs): The application arguments.
        """
        self.config = config
        self.args = args
        self.processor = RowsProcessor()

    def process(self) -> str | None:
        """
        Processes the CSV file and returns the formatted result.

        Returns:
            str | None: The formatted result as a string or None.
        """
        self._set_processor_config()
        rows = self._read_csv_file()
        data_for_pandas = self.processor.process_rows(rows)
        return self._format_data(data_for_pandas)

    def _set_processor_config(self) -> None:
        """
        Sets the configuration for the RowsProcessor.
        """
        self.processor.set_date_attribute_format(self.config.csv.date_attribute_format)
        self.processor.set_cfg_pattern_sets(self.config.enricher_pattern_sets)
        self.processor.set_start_date(self.args.get('start_date'))
        self.processor.set_end_date(self.args.get('end_date'))
        self.processor.set_verbose(self.args.get('verbose', False))
        self.processor.set_category(self.args.get('category', 'category'))
        self.processor.set_filter(self.args.get('filter'))

    def _read_csv_file(self) -> list[CsvRow]:
        """
        Reads the CSV file and returns the rows.

        Returns:
            list[CsvRow]: The list of CsvRow objects.
        """
        csv_reader = CsvFileReader(
            str(self.args['filename']),
            str(self.config.csv.dialect),
            str(self.config.csv.delimiter),
            dict(self.config.csv.attribute_mapping)
        )
        csv_reader.read()
        return csv_reader.get_rows()

    def _format_data(self, data_for_pandas: dict) -> str | None:
        """
        Formats the data using DataFrameFormatter.

        Args:
            data_for_pandas (dict): The data to format.

        Returns:
            str | None: The formatted data as a string or None.
        """
        formatter = DataFrameFormatter()
        formatter.set_nowrap(self.args.get('nowrap', False))
        formatter.set_no_currency_format(self.args.get('no_currency_format', False))
        df = formatter.format_dataframe(data_for_pandas)

        if self.args.get('output_format') == 'html':
            return df.to_html(border=0)
        elif self.args.get('output'):
            return df.to_csv(self.args.get('output'), index=True, header=True, sep=';', decimal=',')
        else:
            return df.to_string()
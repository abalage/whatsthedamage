"""
This module processes KHBHU CSV files and provides a CLI tool to categorize and summarize the data.

Functions:
    load_config(config_path: str) -> dict[str, dict[str, dict[str, str]]]:
        Loads the configuration file and validates its contents.

    set_locale(locale_str: str) -> None:
        Sets the locale for currency formatting.

    main(args: dict[str, str | bool | None]) -> str | None:
        The main function receives arguments, loads the configuration, reads the CSV file,
        processes the rows, and prints or saves the result.
"""
import locale
import sys
from whatsthedamage.csv_file_reader import CsvFileReader
from whatsthedamage.rows_processor import RowsProcessor
from whatsthedamage.data_frame_formatter import DataFrameFormatter
from whatsthedamage.config import AppArgs, load_config


__all__ = ['main']


def set_locale(locale_str: str) -> None:
    # Setting locale
    try:
        locale.setlocale(locale.LC_ALL, locale_str)
    except locale.Error:
        print(f"Warning: Locale '{locale_str}' is not supported. Falling back to default locale.", file=sys.stderr)
        locale.setlocale(locale.LC_ALL, '')


def main(args: AppArgs) -> str | None:
    # Load the configuration file
    config = load_config(str(args['config']))

    # Set the locale for currency formatting
    set_locale(config.main.locale)

    # Create a CsvReader object and read the file contents
    csv_reader = CsvFileReader(
        str(args['filename']),
        str(config.csv.dialect),
        str(config.csv.delimiter)
    )
    csv_reader.read()
    rows = csv_reader.get_rows()

    # Process the rows
    processor = RowsProcessor()

    # Pass the configuration to the processor
    processor.set_date_attribute(config.csv.date_attribute)
    processor.set_date_attribute_format(config.csv.date_attribute_format)
    processor.set_sum_attribute(config.csv.sum_attribute)
    processor.set_selected_attributes(config.main.selected_attributes)
    processor.set_cfg_pattern_sets(config.enricher_pattern_sets)

    # Pass the arguments to the processor
    processor.set_start_date(args.get('start_date'))
    processor.set_end_date(args.get('end_date'))
    processor.set_verbose(args.get('verbose', False))
    processor.set_category(args.get('category', 'category'))
    processor.set_filter(args.get('filter'))

    data_for_pandas = processor.process_rows(rows)

    # Create an instance of DataFrameFormatter
    formatter = DataFrameFormatter()
    formatter.set_nowrap(args.get('nowrap', False))
    formatter.set_no_currency_format(args.get('no_currency_format', False))

    # Format the DataFrame
    df = formatter.format_dataframe(data_for_pandas)

    # Different output format depending on client request
    if args.get('output_format') == 'html':
        return df.to_html(border=0)
    elif args.get('output'):
        return df.to_csv(args.get('output'), index=True, header=True, sep=';', decimal=',')
    else:
        return df.to_string()

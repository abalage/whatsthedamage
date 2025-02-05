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
import json
import locale
import sys
from whatsthedamage.csv_file_reader import CsvFileReader
from whatsthedamage.rows_processor import RowsProcessor
from whatsthedamage.data_frame_formatter import DataFrameFormatter


__all__ = ['main']


def load_config(config_path: str) -> dict[str, dict[str, dict[str, str]]]:
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config: dict[str, dict[str, dict[str, str]]] = json.load(file)
            if 'csv' not in config or 'main' not in config or 'enricher_pattern_sets' not in config:
                raise KeyError("Configuration file must contain 'csv', 'main' and 'enricher_pattern_sets' keys.")
        return config
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{config_path}' is not a valid JSON.", file=sys.stderr)
        exit(1)


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
    set_locale(str(config['main']['locale']))

    # Create a CsvReader object and read the file contents
    csv_reader = CsvFileReader(
        args.filename,
        str(config['csv']['dialect']),
        str(config['csv']['delimiter'])
    )
    csv_reader.read()
    rows = csv_reader.get_rows()

    # Process the rows
    processor = RowsProcessor(config)

    # Pass the arguments to the processor
    processor.set_start_date(args.start_date)
    processor.set_end_date(args.end_date)
    processor.set_verbose(args.verbose)
    processor.set_category(args.category)
    processor.set_filter(args.filter)

    data_for_pandas = processor.process_rows(rows)

    # Create an instance of DataFrameFormatter
    formatter = DataFrameFormatter()
    formatter.set_nowrap(args.get('nowrap', False))
    formatter.set_no_currency_format(args.get('no_currency_format', False))

    # Format the DataFrame
    df = formatter.format_dataframe(data_for_pandas)

    # Print the DataFrame
    if args.output:
        df.to_csv(args.output, index=True, header=True, sep=';', decimal=',')
    else:
        print(df)

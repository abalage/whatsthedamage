"""
This module processes KHBHU CSV files and provides a CLI tool to categorize and summarize the data.

Functions:
    load_config(config_path: str) -> dict[str, dict[str, dict[str, str]]]:
        Loads the configuration file and validates its contents.

    set_locale(locale_str: str) -> None:
        Sets the locale for currency formatting.
    print_categorized_rows(
        Prints categorized rows based on the selected attributes.

    process_rows(
        Processes the rows by filtering, enriching, categorizing, and summarizing them.

    format_dataframe(data_for_pandas: dict[str, dict[str, float]], args: argparse.Namespace) -> pd.DataFrame:
        Formats the processed data into a pandas DataFrame with optional currency formatting.

    main() -> None:
        The main function that sets up the argument parser, loads the configuration, reads the CSV file,
        processes the rows, and prints or saves the result.
"""
import json
import argparse
import locale
import sys
from typing import Optional, Any
from whatsthedamage.csv_row import CsvRow
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


def main() -> None:
    # Set up argument parser
    parser = argparse.ArgumentParser(description="A CLI tool to process KHBHU CSV files.")
    parser.add_argument('filename', type=str,
                        help='The CSV file to read.')
    parser.add_argument('--start-date', type=str,
                        help='Start date in format YYYY.MM.DD.')
    parser.add_argument('--end-date', type=str,
                        help='End date in format YYYY.MM.DD.')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print categorized rows for troubleshooting.')
    parser.add_argument('--version', action='version', version='What\'s the Damage',
                        help='Show the version of the program.')
    parser.add_argument('--config', '-c', type=str, default='config.json.default',
                        help='Path to the configuration file. (default: config.json.default)')
    parser.add_argument('--category', type=str, default='category',
                        help='The attribute to categorize by. (default: category)')
    parser.add_argument('--no-currency-format', action='store_true',
                        help='Disable currency formatting. Useful for importing the data into a spreadsheet.')
    parser.add_argument('--output', '-o', type=str,
                        help='Save the result into a CSV file with the specified filename.')
    parser.add_argument('--nowrap', '-n', action='store_true',
                        help='Do not wrap the output text. Useful for viewing the output without line wraps.')
    parser.add_argument('--filter', '-f', type=str, help='Filter by category. Use it conjunction with --verbose.')

    # Parse the arguments
    args = parser.parse_args()

    # Load the configuration file
    config = load_config(args.config)

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
    formatter.set_nowrap(args.nowrap)
    formatter.set_no_currency_format(args.no_currency_format)

    # Format the DataFrame
    df = formatter.format_dataframe(data_for_pandas)

    # Print the DataFrame
    if args.output:
        df.to_csv(args.output, index=True, header=True, sep=';', decimal=',')
    else:
        print(df)

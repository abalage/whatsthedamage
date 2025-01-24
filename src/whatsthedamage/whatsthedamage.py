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
import pandas as pd
from typing import Optional, Any
from whatsthedamage.csv_row import CsvRow
from whatsthedamage.csv_file_reader import CsvFileReader
from whatsthedamage.date_converter import DateConverter
from whatsthedamage.row_filter import RowFilter
from whatsthedamage.row_enrichment import RowEnrichment
from whatsthedamage.row_summarizer import RowSummarizer


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


def print_categorized_rows(
        set_name: str,
        set_rows_dict: dict[str, list[CsvRow]],
        selected_attributes: list[str]) -> None:

    print(f"\nSet name: {set_name}")
    for type_value, rowset in set_rows_dict.items():
        print(f"\nType: {type_value}")
        for row in rowset:
            selected_values = {attr: getattr(row, attr, None) for attr in selected_attributes}
            print(selected_values)


def process_rows(
        rows: list['CsvRow'],
        config: Any,
        args: argparse.Namespace) -> dict[str, dict[str, float]]:

    date_attribute = config['csv']['date_attribute']
    date_attribute_format = config['csv']['date_attribute_format']
    sum_attribute = config['csv']['sum_attribute']
    selected_attributes = config['main']['selected_attributes']
    cfg_pattern_sets = config['enricher_pattern_sets']

    # Convert start and end dates to epoch time
    start_date: Optional[int] = DateConverter.convert_to_epoch(
        args.start_date,
        date_attribute_format
    ) if args.start_date else None

    end_date: Optional[int] = DateConverter.convert_to_epoch(
        args.end_date,
        date_attribute_format
    ) if args.end_date else None

    # Filter rows by date if start_date or end_date is provided
    row_filter = RowFilter(rows, date_attribute_format)
    if start_date and end_date:
        filtered_sets = row_filter.filter_by_date(date_attribute, start_date, end_date)
    else:
        filtered_sets = row_filter.filter_by_month(date_attribute)

    if args.verbose:
        print("Summary of attribute '" + sum_attribute + "' grouped by '" + args.category + "':")

    data_for_pandas = {}

    for filtered_set in filtered_sets:
        # set_name is the month or date range
        # set_rows is the list of CsvRow objects
        for set_name, set_rows in filtered_set.items():
            # Add attribute 'category' based on a specified other attribute matching against a set of patterns
            enricher = RowEnrichment(set_rows, cfg_pattern_sets)
            enricher.set_sum_attribute(sum_attribute)
            enricher.initialize()

            # Categorize rows by specificed attribute
            set_rows_dict = enricher.categorize_by_attribute(args.category)

            # Filter rows by category name if provided
            if args.filter:
                set_rows_dict = {k: v for k, v in set_rows_dict.items() if k == args.filter}

            # Initialize the summarizer with the categorized rows
            summarizer = RowSummarizer(set_rows_dict, sum_attribute)

            # Summarize the values of the given attribute by category
            summary = summarizer.summarize()

            # Convert month number to name if set_name is a number
            try:
                set_name = DateConverter.convert_month_number_to_name(int(set_name))
            except ValueError:
                start_date_str = DateConverter.convert_from_epoch(
                    start_date,
                    date_attribute_format
                ) if start_date else None
                end_date_str = DateConverter.convert_from_epoch(
                    end_date,
                    date_attribute_format
                ) if end_date else None
                set_name = str(start_date_str) + " - " + str(end_date_str)

            data_for_pandas[set_name] = summary

            # Print categorized rows if verbose
            if args.verbose:
                print_categorized_rows(set_name, set_rows_dict, selected_attributes)

    return data_for_pandas


def format_dataframe(data_for_pandas: dict[str, dict[str, float]], args: argparse.Namespace) -> pd.DataFrame:
    # Set pandas to display all columns and rows without truncation
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 130)
    if args.nowrap:
        pd.set_option('display.expand_frame_repr', False)

    # Create a DataFrame from the data
    df = pd.DataFrame(data_for_pandas)

    # Sort the DataFrame by index (which are the categories)
    df = df.sort_index()

    # Format the DataFrame with currency values
    if not args.no_currency_format:
        def format_currency(value: Optional[float]) -> str:
            if value is None:
                return 'N/A'
            if isinstance(value, (int, float)):
                return locale.currency(value, grouping=True)
            return str(value)  # type: ignore[unreachable]

        df = df.apply(lambda row: row.apply(format_currency), axis=1)
    return df


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
    data_for_pandas = process_rows(
        rows,
        config,
        args)

    # Set pandas to display all columns and rows
    df = format_dataframe(data_for_pandas, args)

    # Print the DataFrame
    if args.output:
        df.to_csv(args.output, index=True, header=True, sep=';', decimal=',')
    else:
        print(df)

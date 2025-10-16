"""CLI controller for whatsthedamage."""
import argparse
from whatsthedamage.utils.version import get_version
from whatsthedamage.config.config import AppArgs


class CLIController:
    def __init__(self) -> None:
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="A CLI tool to process KHBHU CSV files.")
        parser.add_argument('filename', type=str, help='The CSV file to read.')
        parser.add_argument('--start-date', type=str, help='Start date (e.g. YYYY.MM.DD.)')
        parser.add_argument('--end-date', type=str, help='End date (e.g. YYYY.MM.DD.)')
        parser.add_argument('--verbose', '-v', action='store_true', help='Print categorized rows for troubleshooting.')
        parser.add_argument('--version', action='version', version=f"whatsthedamage v{get_version()}", help='Show the version of the program.')  # noqa: E501
        parser.add_argument('--config', '-c', type=str, help='Path to the configuration file.')
        parser.add_argument('--category', type=str, default='category', help='The attribute to categorize by. (default: category)')  # noqa: E501
        parser.add_argument('--no-currency-format', action='store_true', help='Disable currency formatting. Useful for importing the data into a spreadsheet.')  # noqa: E501
        parser.add_argument('--output', '-o', type=str, help='Save the result into a CSV file with the specified filename.')  # noqa: E501
        parser.add_argument('--output-format', type=str, default='csv', help='Supported formats are: html, csv. (default: csv).')  # noqa: E501
        parser.add_argument('--nowrap', '-n', action='store_true', help='Do not wrap the output text. Useful for viewing the output without line wraps.')  # noqa: E501
        parser.add_argument('--filter', '-f', type=str, help='Filter by category. Use it in conjunction with --verbose.')
        parser.add_argument('--lang', '-l', type=str, help='Language for localization.')
        parser.add_argument('--training-data', action='store_true', help="Print training data in JSON format to STDERR. Use 2> redirection to save it to a file.")  # noqa: E501
        parser.add_argument('--ml', action='store_true', help="Use machine learning for categorization instead of regular expressions. (experimental)")
        return parser

    def parse_arguments(self) -> AppArgs:
        parsed_args = self.parser.parse_args()
        return {
            'category': parsed_args.category,
            'config': parsed_args.config,
            'end_date': parsed_args.end_date,
            'filename': parsed_args.filename,
            'filter': parsed_args.filter,
            'no_currency_format': parsed_args.no_currency_format,
            'nowrap': parsed_args.nowrap,
            'output_format': parsed_args.output_format,
            'output': parsed_args.output,
            'start_date': parsed_args.start_date,
            'verbose': parsed_args.verbose,
            'lang': parsed_args.lang,
            'training_data': parsed_args.training_data,
            'ml': parsed_args.ml
        }

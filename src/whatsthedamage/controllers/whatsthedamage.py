"""
This module processes KHBHU CSV files and provides a CLI tool to categorize and summarize the data.

Functions:
    set_locale(locale_str: str) -> None:
        Sets the locale for currency formatting.

    main(args: AppArgs) -> str | None:
        The main function receives arguments, loads the configuration, reads the CSV file,
        processes the rows, and prints or saves the result.
"""
import locale
import sys
from whatsthedamage.models.csv_processor import CSVProcessor
from whatsthedamage.config.config import AppArgs, AppContext, load_config


__all__ = ['main']


def set_locale(locale_str: str) -> None:
    """
    Sets the locale for currency formatting.

    Args:
        locale_str (str): The locale string to set.
    """
    try:
        locale.setlocale(locale.LC_ALL, locale_str)
    except locale.Error:
        print(f"Warning: Locale '{locale_str}' is not supported. Falling back to default locale.", file=sys.stderr)
        locale.setlocale(locale.LC_ALL, '')


def main(args: AppArgs) -> str:
    """
    The main function receives arguments, loads the configuration, reads the CSV file,
    processes the rows, and prints or saves the result.

    Args:
        args (AppArgs): The application arguments.

    Returns:
        str | None: The formatted result as a string or None.
    """
    # Load the configuration file
    config = load_config(str(args['config']))

    # Create AppContext
    context = AppContext(config, args)

    # Set the locale for currency formatting
    set_locale(config.main.locale)

    # Process the CSV file
    processor = CSVProcessor(context)
    return processor.process()

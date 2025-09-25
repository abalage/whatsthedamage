"""
This module processes KHBHU CSV files and provides a CLI tool to categorize and summarize the data.

Functions:
    set_locale(locale_str: str) -> None:
        Sets the locale for currency formatting.

    main(args: AppArgs) -> str | None:
        The main function receives arguments, loads the configuration, reads the CSV file,
        processes the rows, and prints or saves the result.
"""
import os
import gettext
import importlib.resources as resources
from whatsthedamage.models.csv_processor import CSVProcessor
from whatsthedamage.config.config import AppArgs, AppContext, load_config


__all__ = ['main']


def set_locale(locale_str: str | None) -> None:
    """
    Sets the locale for the application, allowing override of the system locale.

    Args:
        locale_str (str | None): The language code (e.g., 'en', 'hu'). If None, defaults to the system locale.
    """
    # Default to system locale if no language is provided
    if not locale_str:
        locale_str = os.getenv("LANG", "en").split(".")[0]  # Use system locale or fallback to 'en'

    # Override the LANGUAGE environment variable
    os.environ["LANGUAGE"] = locale_str

    with resources.path("whatsthedamage", "locale") as localedir:
        try:
            gettext.bindtextdomain('messages', str(localedir))
            gettext.textdomain('messages')
            gettext.translation('messages', str(localedir), languages=[locale_str], fallback=False).install()
        except FileNotFoundError:
            print(f"Warning: Locale '{locale_str}' not found. Falling back to default.")
            gettext.translation('messages', str(localedir), fallback=True).install()


def main(args: AppArgs) -> str:
    """
    The main function receives arguments, loads the configuration, reads the CSV file,
    processes the rows, and prints or saves the result.

    Args:
        args (AppArgs): The application arguments.

    Returns:
        str | None: The formatted result as a string or None.
    """
    # Set the locale
    set_locale(args['lang'])

    # Load the configuration file
    config = load_config(args['config'])

    # Create AppContext
    context = AppContext(config, args)

    # Process the CSV file
    processor = CSVProcessor(context)
    return processor.process()

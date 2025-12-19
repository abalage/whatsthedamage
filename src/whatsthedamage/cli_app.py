"""CLI application entrypoint for whatsthedamage."""
import os
import gettext
import importlib.resources as resources
from typing import Dict, Any
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.config.config import AppArgs
from gettext import gettext as _


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


def format_output(data: Dict[str, Dict[str, float]], args: AppArgs, currency: str) -> str:
    """Format processed data for CLI output.

    Args:
        data: Processed data with monthly breakdown Dict[month, Dict[category, amount]]
        args: CLI arguments with formatting options
        currency: Currency code for formatting

    Returns:
        str: Formatted output string
    """
    formatting_service = DataFormattingService()

    return formatting_service.format_for_output(
        data=data,
        currency=currency,
        output_format=args.get('output_format'),
        output_file=args.get('output'),
        nowrap=args.get('nowrap', False),
        no_currency_format=args.get('no_currency_format', False),
        categories_header=_("Categories")
    )


def main() -> None:
    """Main CLI entrypoint using ProcessingService."""
    controller = CLIController()
    args = controller.parse_arguments()

    # Set the locale
    set_locale(args.get('lang'))

    # Initialize service
    service = ProcessingService()

    # Check if verbose or training_data mode is requested
    # These require direct CSVProcessor access for now
    if args.get('verbose') or args.get('training_data'):
        # Fall back to old implementation for verbose/training_data modes
        from whatsthedamage.controllers.whatsthedamage import main as process_csv
        output_str = process_csv(args)
        print(output_str)
        return

    # Process using service layer
    try:
        result: Dict[str, Any] = service.process_summary(
            csv_file_path=args['filename'],
            config_file_path=args.get('config'),
            start_date=args.get('start_date'),
            end_date=args.get('end_date'),
            ml_enabled=args.get('ml', False),
            category_filter=args.get('filter'),
            language=args.get('lang') or 'en'
        )

        # Get processor and currency
        processor = result['processor']
        currency: str = processor.processor.get_currency()

        # Get monthly breakdown data (before flattening)
        # Re-process to get monthly data instead of flattened totals
        rows = processor._read_csv_file()
        monthly_data: Dict[str, Dict[str, float]] = processor.processor.process_rows(rows)

        # Format output with monthly columns
        output = format_output(monthly_data, args, currency)
        print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        exit(1)


if __name__ == "__main__":
    main()

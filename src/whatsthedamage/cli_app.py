"""CLI application entrypoint for whatsthedamage."""
import os
import gettext
import importlib.resources as resources
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.models.data_frame_formatter import DataFrameFormatter
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


def format_output(data: dict, args: dict, currency: str) -> str:
    """Format processed data for CLI output.

    Args:
        data: Processed data - flattened summary Dict[str, float]
        args: CLI arguments with formatting options
        currency: Currency code for formatting

    Returns:
        str: Formatted output string
    """
    formatter = DataFrameFormatter()
    formatter.set_nowrap(args.get('nowrap', False))
    formatter.set_no_currency_format(args.get('no_currency_format', False))

    # Wrap flattened data in "Total" month for formatter compatibility
    # DataFrameFormatter expects Dict[month, Dict[category, amount]]
    monthly_data = {"Total": data}

    df = formatter.format_dataframe(monthly_data, currency=currency)

    if args.get('output_format') == 'html':
        # Convert to HTML and manually replace the empty th for index with translatable "Categories"
        html = df.to_html(border=0)
        html = html.replace('<th></th>', f'<th>{_("Categories")}</th>', 1)
        return html
    elif args.get('output'):
        # Save to file and return confirmation message
        df.to_csv(args.get('output'), index=True, header=True, sep=';', decimal=',')
        return str(df.to_csv(None, index=True, header=True, sep=';', decimal=','))
    else:
        return df.to_string()


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
        result = process_csv(args)
        print(result)
        return

    # Process using service layer
    try:
        result = service.process_summary(
            csv_file_path=args['filename'],
            config_file_path=args.get('config'),
            start_date=args.get('start_date'),
            end_date=args.get('end_date'),
            ml_enabled=args.get('ml', False),
            category_filter=args.get('filter'),
            language=args.get('lang') or 'en'
        )

        # Get currency from service result (set by RowsProcessor)
        currency = result['metadata'].get('currency', 'HUF')

        # Format and display output
        output = format_output(result['data'], vars(args), currency)
        print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        exit(1)


if __name__ == "__main__":
    main()

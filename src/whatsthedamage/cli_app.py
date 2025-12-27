"""CLI application entrypoint for whatsthedamage."""
import os
import gettext
import importlib.resources as resources
from typing import Dict, Any
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.services.processing_service import ProcessingService
from whatsthedamage.services.data_formatting_service import DataFormattingService
from whatsthedamage.config.config import AppArgs
from whatsthedamage.config.dt_models import DataTablesResponse
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


def format_output(dt_responses: Dict[str, DataTablesResponse], args: AppArgs) -> str:
    """Format processed data for CLI output.

    Args:
        dt_responses: DataTablesResponse objects per account
        args: CLI arguments with formatting options

    Returns:
        str: Formatted output string
    """
    formatting_service = DataFormattingService()

    return formatting_service.format_datatables_for_output(
        dt_responses=dt_responses,
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

    # Process using service layer (v2 processing pipeline with DataTablesResponse)
    try:
        result: Dict[str, Any] = service.process_with_details(
            csv_file_path=args['filename'],
            config_file_path=args.get('config'),
            start_date=args.get('start_date'),
            end_date=args.get('end_date'),
            ml_enabled=args.get('ml', False),
            category_filter=args.get('filter'),
            language=args.get('lang') or 'en',
            verbose=args.get('verbose', False),
            training_data=args.get('training_data', False)
        )

        # Extract DataTablesResponse per account
        dt_responses: Dict[str, DataTablesResponse] = result['data']

        # Process all accounts uniformly
        all_outputs = []
        output_file = args.get('output')

        for account_id, dt_response in dt_responses.items():
            # Print account header for multi-account scenarios
            if len(dt_responses) > 1:
                print(f"\n{'=' * 60}")
                print(f"Account: {account_id}")
                print(f"{'=' * 60}")

            single_account_data = {account_id: dt_response}
            # Create args copy without output to avoid file overwrite
            args_copy = dict(args)
            args_copy['output'] = None
            output = format_output(single_account_data, args_copy)  # type: ignore[arg-type]
            print(output)

            # Collect for file output if needed
            if output_file:
                header = f"Account: {account_id}\n" if len(dt_responses) > 1 else ""
                all_outputs.append(f"{header}{output}")

        # Write all accounts to file once
        if output_file and all_outputs:
            with open(output_file, 'w') as f:
                separator = '\n\n' if len(dt_responses) > 1 else ''
                f.write(separator.join(all_outputs))

    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        exit(1)


if __name__ == "__main__":
    main()

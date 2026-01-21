"""CLI application entrypoint for whatsthedamage."""
import os
import gettext
import importlib.resources as resources
from typing import Dict, Any
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.services.service_factory import create_service_container, ServiceContainer
from whatsthedamage.config.config import AppArgs
from whatsthedamage.config.dt_models import DataTablesResponse


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


def format_output(
    dt_responses: Dict[str, DataTablesResponse],
    args: AppArgs,
    container: ServiceContainer
) -> str:
    """Format processed data for CLI output.

    Args:
        dt_responses: DataTablesResponse objects per account
        args: CLI arguments with formatting options
        container: Service container with formatting service

    Returns:
        str: Formatted output string
    """
    formatting_service = container.data_formatting_service

    return formatting_service.format_all_accounts_for_output(
        dt_responses=dt_responses,
        output_format=args.output_format,
        output_file=args.output,
        nowrap=args.nowrap
    )


def main() -> None:
    """Main CLI entrypoint using service factory and dependency injection."""
    controller = CLIController()
    args = controller.parse_arguments()

    # Set the locale
    set_locale(args.lang)

    # Initialize services via factory (dependency injection)
    container = create_service_container()

    # Process using service layer (v2 processing pipeline with DataTablesResponse)
    try:
        result: Dict[str, Any] = container.processing_service.process_with_details(
            csv_file_path=args.filename,
            config_file_path=args.config,
            start_date=args.start_date,
            end_date=args.end_date,
            ml_enabled=args.ml,
            category_filter=args.filter,
            language=args.lang or 'en',
            verbose=args.verbose,
            training_data=args.training_data
        )

        # Extract DataTablesResponse per account
        dt_responses: Dict[str, DataTablesResponse] = result['data']

        # Format all accounts using service (handles multi-account iteration)
        output = format_output(dt_responses, args, container)  # type: ignore[arg-type]
        print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        exit(1)


if __name__ == "__main__":
    main()

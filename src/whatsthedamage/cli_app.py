"""CLI application entrypoint for whatsthedamage."""
import os
import gettext
import importlib.resources as resources
from typing import Dict
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.services.service_container import create_service_container, ServiceContainer
from whatsthedamage.config.config import AppArgs
from whatsthedamage.models.dt_models import AccountResponse, ProcessingResponse
from whatsthedamage.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)

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
            logger.warning(f"Locale '{locale_str}' not found. Falling back to default.")
            gettext.translation('messages', str(localedir), fallback=True).install()


def format_output(
    dt_responses: Dict[str, AccountResponse],
    args: AppArgs,
    container: ServiceContainer
) -> str:
    """Format processed data for CLI output.

    Args:
        dt_responses: AccountResponse objects per account
        args: CLI arguments with formatting options
        container: Service container with formatting service

    Returns:
        str: Formatted output string
    """
    formatting_service = container.response_formatting_service

    return formatting_service.format_all_accounts_for_output(
        dt_responses=dt_responses,
        output_format=args.output_format,
        output_file=args.output,
        nowrap=args.nowrap
    )


def main() -> None:
    """Main CLI entrypoint using service factory and dependency injection."""
    # Parse arguments first to get logging configuration
    controller = CLIController()
    args = controller.parse_arguments()

    # Configure logging with CLI arguments
    configure_logging(log_level=args.log_level, log_output=args.log_output, log_format=args.log_format)
    logger = get_logger(__name__)
    logger.info("Starting CLI application")


    logger.debug("CLI arguments parsed", context={"filename": args.filename, "config": args.config})

    # Set the locale
    set_locale(args.lang)

    # Initialize services via factory (dependency injection)
    container = create_service_container()
    logger.info("Services initialized via factory")

    # Process using service layer
    try:
        result: ProcessingResponse = container.processing_service.process_with_details(
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

        # Extract AccountResponse per account
        dt_responses: Dict[str, AccountResponse] = result.data

        # Format all accounts using service (handles multi-account iteration)
        output = format_output(dt_responses, args, container)
        print(output)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        exit(1)


if __name__ == "__main__":
    main()

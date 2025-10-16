"""CLI application entrypoint for whatsthedamage."""
from whatsthedamage.controllers.cli_controller import CLIController
from whatsthedamage.controllers.whatsthedamage import main as process_csv


def main() -> None:
    """Main CLI entrypoint."""
    controller = CLIController()
    args = controller.parse_arguments()
    result = process_csv(args)
    print(result)


if __name__ == "__main__":
    main()
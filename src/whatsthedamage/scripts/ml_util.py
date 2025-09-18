import argparse
from whatsthedamage.models.machine_learning import Train, Inference


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train or test transaction categorizer model (modular version)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train the model")
    train_parser.add_argument("training_data", help="Path to training data JSON file")
    train_parser.add_argument("--gridsearch", action="store_true", help="Use GridSearchCV for hyperparameter tuning")  # noqa: E501
    train_parser.add_argument("--randomsearch", action="store_true", help="Use RandomizedSearchCV for hyperparameter tuning")  # noqa: E501
    train_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output during training")
    train_parser.add_argument("--output", help="Output directory for trained model (auto-generated if not exists)")

    # Predict subcommand
    predict_parser = subparsers.add_parser("predict", help="Predict categories for new data")
    predict_parser.add_argument("model", help="Path to trained model file")
    predict_parser.add_argument("new_data", help="Path to new data JSON file")
    predict_parser.add_argument("--confidence", action="store_true", help="Show prediction confidence scores and verbose data")  # noqa: E501

    args = parser.parse_args()

    # ML subcommand validation
    if args.command == 'ml':
        # --train and --inference require --model
        if (args.train or args.inference) and not args.model:
            parser.error("--model is required when using --train or --inference.")

        # --gridsearch, --randomsearch only allowed with --train
        if (args.gridsearch or args.randomsearch) and not args.train:
            parser.error("--gridsearch, and --randomsearch are only allowed with --train.")

        # --gridsearch and --randomsearch are mutually exclusive
        if args.gridsearch and args.randomsearch:
            parser.error("--gridsearch and --randomsearch cannot be used together.")

    if args.command == "train":
        # Instantiate and configure Train class with arguments
        train = Train(
            training_data_path=args.training_data,
            output=args.output,
            verbose=args.verbose
        )

        if args.gridsearch or args.randomsearch:
            train.hyperparameter_tuning(
                method="grid" if args.gridsearch else "random"
            )

        else:
            train.train()

    elif args.command == "predict":
        # Use Inference class for predictions
        predict = Inference(args.new_data)
        predict.print_inference_data(args.confidence)


if __name__ == "__main__":
    main()

import argparse
from whatsthedamage.services.ml_service import MLService
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train or test transaction categorizer model (modular version)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train the model")
    train_parser.add_argument("--data", help="Path to training data JSON file")
    train_parser.add_argument("--gridsearch", action="store_true", help="Use GridSearchCV for hyperparameter tuning")  # noqa: E501
    train_parser.add_argument("--randomsearch", action="store_true", help="Use RandomizedSearchCV for hyperparameter tuning")  # noqa: E501
    train_parser.add_argument("--smote", action="store_true", help="Enable SMOTE for synthetic data generation on rare categories")  # noqa: E501
    train_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output during training")

    # Predict subcommand
    predict_parser = subparsers.add_parser("predict", help="Predict categories for new data")
    predict_parser.add_argument("--model", help="Path to trained model file")
    predict_parser.add_argument("--data", help="Path to new data JSON file")
    predict_parser.add_argument("--confidence", action="store_true", help="Show prediction confidence scores and verbose data")  # noqa: E501

    # Metrics subcommand
    metrics_parser = subparsers.add_parser("metrics", help="Calculate model evaluation metrics")
    metrics_parser.add_argument("--model", required=True, help="Path to trained model file")
    metrics_parser.add_argument("--data", required=True, help="Path to test data JSON file")
    metrics_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output during metrics calculation")  # noqa: E501

    args = parser.parse_args()

    # Initialize ML service
    ml_service = MLService()
    if args.command == "train":
        # Delegate training logic to ML service
        ml_service.train(
            training_data_path=args.data,
            verbose=args.verbose,
            gridsearch=args.gridsearch,
            randomsearch=args.randomsearch,
            enable_smote=args.smote
        )

    elif args.command == "predict":
        # Delegate prediction logic to ML service
        ml_service.predict(
            model_path=args.model,
            new_data_path=args.data,
            show_confidence=args.confidence
        )

    elif args.command == "metrics":
        # Delegate metrics logic to ML service
        ml_service.calculate_metrics(
            model_path=args.model,
            test_data_path=args.data,
            verbose=args.verbose
        )
if __name__ == "__main__":
    main()

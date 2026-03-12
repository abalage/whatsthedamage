import argparse
from whatsthedamage.models.machine_learning import Train, Inference, Metrics

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

    # Metrics subcommand
    metrics_parser = subparsers.add_parser("metrics", help="Calculate model evaluation metrics")
    metrics_parser.add_argument("--model", required=True, help="Path to trained model file")
    metrics_parser.add_argument("--data", required=True, help="Path to test data JSON file")
    metrics_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output during metrics calculation")  # noqa: E501

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

    elif args.command == "metrics":
        # Use Metrics class for model evaluation
        metrics = Metrics(
            model_path=args.model,
            test_data_path=args.data
        )

        # Get raw metrics data (now includes formatted confusion matrix and classification report)
        metrics_data = metrics.get_metrics_data()

        # Prepare data for template
        template_data = {
            'accuracy': metrics_data['accuracy'],
            'confusion_matrix_content': metrics_data['confusion_matrix_content'],
            'classification_report': metrics_data['classification_report'],
            'confused_pairs': metrics_data['confused_pairs'],
            'confidence_analysis': metrics_data['confidence_analysis'],
            'merchant_analysis': metrics_data['merchant_analysis']
        }

        # Render using Jinja2 templates directly
        from jinja2 import Environment, PackageLoader, select_autoescape

        env = Environment(
            loader=PackageLoader('whatsthedamage.view.metrics_renderers', 'templates'),
            autoescape=select_autoescape(['jinja2'])
        )
        template = env.get_template('metrics_report.jinja2')
        report = template.render(**template_data)

        print(report)

if __name__ == "__main__":
    main()

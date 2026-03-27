from typing import List, Union
from whatsthedamage.models.machine_learning import Train, Inference, Metrics
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

class MLService:
    """Service for ML-related operations."""

    def train(
        self,
        training_data_path: str,
        gridsearch: bool = False,
        randomsearch: bool = False,
        enable_smote: bool = False
    ) -> None:
        """Train the model."""
        config = MLConfig(enable_smote=enable_smote)
        train = Train(
            training_data_path=training_data_path,
            config=config,
        )

        if gridsearch or randomsearch:
            train.hyperparameter_tuning(
                method="grid" if gridsearch else "random"
            )
        else:
            train.train()

    def predict(
        self,
        model_path: str,
        new_data_path: str,
        show_confidence: bool = False
    ) -> None:
        """Predict categories for new data."""
        predict = Inference(new_data_path, model_path)
        predict.print_inference_data(show_confidence)

    def get_predictions(
        self,
        model_path: str,
        new_data: Union[str, List[CsvRow]]
    ) -> List[CsvRow]:
        """Get predictions for new data and return as CsvRow objects.

        Args:
            model_path: Path to trained model file
            new_data: Either path to JSON file or List[CsvRow] objects

        Returns:
            List of CsvRow objects with predicted categories and confidence scores
        """
        inference = Inference(model_path, new_data)
        return inference.get_predictions()

    def calculate_metrics(
        self,
        model_path: str,
        test_data_path: str,
    ) -> None:
        """Calculate model evaluation metrics."""
        metrics = Metrics(
            model_path=model_path,
            test_data_path=test_data_path
        )

        # Get raw metrics data
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

        # Render using Jinja2 templates
        from jinja2 import Environment, PackageLoader, select_autoescape

        env = Environment(
            loader=PackageLoader('whatsthedamage.view.metrics_renderers', 'templates'),
            autoescape=select_autoescape(['jinja2'])
        )
        template = env.get_template('metrics_report.jinja2')
        report = template.render(**template_data)

        print(report)

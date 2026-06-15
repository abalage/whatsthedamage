from typing import List, Dict, Optional, TYPE_CHECKING
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.config.config import get_category_id_from_name
from whatsthedamage.utils.logging import get_logger

if TYPE_CHECKING:
    from whatsthedamage.services.ml_service import MLService

logger = get_logger(__name__)


class RowEnrichmentML:
    def __init__(self, rows: List[CsvRow], confidence_threshold: float = 0.5):
        """
        Initialize with a list of CsvRow objects and a trained ML model pipeline.

        :param rows: List of CsvRow objects to categorize.
        :param model: Trained ML pipeline (e.g., from train_model.py).
        """
        self.rows = rows
        self.confidence_threshold = confidence_threshold
        self.categorized: Dict[str, List[CsvRow]] = {"other": []}
        self.ml_service: Optional['MLService'] = None

    def _get_ml_service(self) -> 'MLService':
        """Lazy import and initialization of MLService to avoid circular imports."""
        if self.ml_service is None:
            from whatsthedamage.services.ml_service import MLService
            self.ml_service = MLService()
        return self.ml_service

    def _enrich_rows(self) -> None:
        """
        Enrich rows using the ML model.

        This method handles missing row types, gets ML predictions, processes the results,
        applies confidence thresholds, and categorizes the rows accordingly.

        Raises:
            RuntimeError: If ML prediction fails or no valid model is available.
        """
        if not self.rows:
            logger.warning("No rows to enrich")
            return

        # In case 'type' attribute is empty then set it to 'card_reservation'
        # This is a quirk to handle missing types in some bank exports
        for row in self.rows:
            if not row.type or row.type.strip() == "":
                row.type = 'card_reservation'

        try:
            # Use MLService to get predictions instead of directly calling Inference
            # Note: Empty model_path will use default from MLConfig
            ml_service = self._get_ml_service()
            predictions = ml_service.get_predictions(model_path='', new_data=self.rows)
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            raise RuntimeError(f"Failed to get ML predictions: {e}") from e

        if not predictions:
            logger.warning("No predictions returned from ML service")
            return

        # Assign predicted categories and confidence to CsvRow objects
        for row, predicted_row in zip(self.rows, predictions):
            category_str = predicted_row.category_id
            # Map ML prediction (which uses display names) to category ID
            category_id = get_category_id_from_name(category_str)

            # Propagate confidence from ML prediction
            row.confidence = predicted_row.confidence

            # Apply confidence threshold
            if (row.confidence is not None and
                row.confidence < self.confidence_threshold):
                # Use 'other' category for low-confidence predictions
                category_id = "other"
                # Log rows with low confidence scores
                logger.debug(f"Low confidence prediction: {row}")

            row.category_id = category_id

            if category_id not in self.categorized:
                self.categorized[category_id] = []

    def categorize_by_attribute(self, attribute_name: str) -> Dict[str, List[CsvRow]]:
        """
        Categorize CsvRow objects based on a specified attribute.

        :param attribute_name: The name of the attribute to categorize by.
        :return: A dictionary where keys are attribute values and values are lists of CsvRow objects.
        """

        self._enrich_rows()

        for row in self.rows:
            attribute_value = getattr(row, attribute_name, None)
            if attribute_value is not None:
                if attribute_value not in self.categorized:
                    self.categorized[attribute_value] = []
                self.categorized[attribute_value].append(row)
        return self.categorized

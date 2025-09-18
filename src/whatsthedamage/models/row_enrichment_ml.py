from typing import List, Dict
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import get_category_name
from whatsthedamage.models.machine_learning import Inference


class RowEnrichmentML:
    def __init__(self, rows: List[CsvRow]):
        """
        Initialize with a list of CsvRow objects and a trained ML model pipeline.

        :param rows: List of CsvRow objects to categorize.
        :param model: Trained ML pipeline (e.g., from train_model.py).
        """
        self.rows = rows
        self.categorized: Dict[str, List[CsvRow]] = {get_category_name('other'): []}

    def _enrich_rows(self) -> None:
        """
        Enrich rows using the ML model.
        """

        # In case 'type' attribute is empty then set it to 'card_reservation'
        # This is a quirk to handle missing types in some bank exports
        for row in self.rows:
            if not row.type or row.type.strip() == "":
                row.type = 'card_reservation'

        predict = Inference(self.rows)

        predictions = predict.get_predictions()

        # Assign predicted categories to CsvRow objects
        for row, predicted_row in zip(self.rows, predictions):
            category_str = predicted_row.category
            # Quirk to not break existing setup
            if " " in category_str:
                category_str = category_str.replace(" ", "_")
            localized_category = get_category_name(category_str.lower())
            row.category = localized_category
            if localized_category not in self.categorized:
                self.categorized[localized_category] = []

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

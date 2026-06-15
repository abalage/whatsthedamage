from unittest.mock import patch
from whatsthedamage.models.domain.csv_row import CsvRow


class DummyPrediction:
    def __init__(self, category, confidence=None):
        self.category = category
        self.confidence = confidence


def _create_mock_csv_row_from_prediction(csv_row, dummy_prediction, mapping):
    """Helper to create a mock CsvRow with predicted values."""
    row_data = {
        'date': csv_row.date,
        'type': csv_row.type,
        'partner': csv_row.partner,
        'amount': str(csv_row.amount),
        'currency': csv_row.currency,
        'category': dummy_prediction.category,  # This is the ML prediction string (display name)
        'account': csv_row.account
    }
    mock_row = CsvRow(row_data, mapping)
    mock_row.category_id = dummy_prediction.category  # Set the category_id directly from ML prediction
    mock_row.confidence = dummy_prediction.confidence
    return mock_row


def test_enrich_rows_sets_type_and_category(csv_rows, mapping):
    # Set one row's type to empty to test the 'card_reservation' logic
    csv_rows[1].type = ""
    with patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories (display names from ML)
        # ML outputs category names, which get mapped to IDs by get_category_id_from_name
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("Grocery"), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("Other"), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].type == "deposit"
        assert csv_rows[1].type == "card_reservation"
        # ML prediction "Grocery" maps to category_id "grocery" via get_category_id_from_name
        assert csv_rows[0].category_id == "grocery"
        assert csv_rows[1].category_id == "other"
        assert "grocery" in enricher.categorized
        assert "other" in enricher.categorized


def test_enrich_rows_category_with_spaces(csv_rows, mapping):
    with patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("Dining Out"), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("Other"), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        # ML prediction "Dining Out" maps to category_id "dining_out" via get_category_id_from_name
        assert csv_rows[0].category_id == "dining_out"
        assert "dining_out" in enricher.categorized


def test_enrich_rows_empty_rows():
    with patch("whatsthedamage.services.ml_service.MLService") as MockMLService:
        MockMLService.return_value.get_predictions.return_value = []
        from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML([])
        enricher._enrich_rows()
        assert list(enricher.categorized.keys()) == ["other"]
        # The categorized dict is initialized with "other" category

def test_enrich_rows_propagates_confidence(csv_rows, mapping):
    with patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories and confidence
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("Grocery", 0.95), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("Other", 0.87), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].confidence == 0.95
        assert csv_rows[1].confidence == 0.87
        assert csv_rows[0].category_id == "grocery"
        assert csv_rows[1].category_id == "other"

def test_enrich_rows_handles_none_confidence(csv_rows, mapping):
    with patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories and confidence
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("Grocery", None), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("Other", 0.75), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].confidence is None
        assert csv_rows[1].confidence == 0.75
        assert csv_rows[0].category_id == "grocery"
        assert csv_rows[1].category_id == "other"

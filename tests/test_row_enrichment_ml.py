from unittest.mock import patch
from whatsthedamage.models.csv_row import CsvRow


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
        'category': dummy_prediction.category,
        'account': csv_row.account
    }
    mock_row = CsvRow(row_data, mapping)
    mock_row.confidence = dummy_prediction.confidence
    return mock_row


def test_enrich_rows_sets_type_and_category(csv_rows, mapping):
    # Set one row's type to empty to test the 'card_reservation' logic
    csv_rows[1].type = ""
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("groceries"), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("other"), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].type == "deposit"
        assert csv_rows[1].type == "card_reservation"
        assert csv_rows[0].category == "groceries".upper()
        assert csv_rows[1].category == "other".upper()
        assert "groceries".upper() in enricher.categorized
        assert "other".upper() in enricher.categorized


def test_enrich_rows_category_with_spaces(csv_rows, mapping):
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("online shopping"), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("other"), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].category == "online_shopping".upper()
        assert "online_shopping".upper() in enricher.categorized


def test_enrich_rows_empty_rows():
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.services.ml_service.MLService") as MockMLService:
        MockMLService.return_value.get_predictions.return_value = []
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML([])
        enricher._enrich_rows()
        assert list(enricher.categorized.keys()) == ["other".upper()]

def test_enrich_rows_propagates_confidence(csv_rows, mapping):
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories and confidence
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("groceries", 0.95), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("other", 0.87), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].confidence == 0.95
        assert csv_rows[1].confidence == 0.87
        assert csv_rows[0].category == "groceries".upper()
        assert csv_rows[1].category == "other".upper()

def test_enrich_rows_handles_none_confidence(csv_rows, mapping):
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.services.ml_service.MLService") as MockMLService:

        # Create mock CsvRow objects with the predicted categories and confidence
        mock_rows = [
            _create_mock_csv_row_from_prediction(csv_rows[0], DummyPrediction("groceries", None), mapping),
            _create_mock_csv_row_from_prediction(csv_rows[1], DummyPrediction("other", 0.75), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].confidence is None
        assert csv_rows[1].confidence == 0.75
        assert csv_rows[0].category == "groceries".upper()
        assert csv_rows[1].category == "other".upper()

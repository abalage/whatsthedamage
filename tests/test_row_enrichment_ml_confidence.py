"""Test RowEnrichmentML confidence threshold functionality."""
import pytest
from unittest.mock import patch
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML


class DummyPrediction:
    def __init__(self, category, confidence):
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
    mock_row.category_id = dummy_prediction.category  # Set the category_id directly from ML prediction
    mock_row.confidence = dummy_prediction.confidence
    return mock_row


def test_row_enrichment_ml_confidence_threshold():
    """Test that RowEnrichmentML applies confidence threshold correctly."""

    # Create test rows
    rows = []
    mapping = {
        "date": "date",
        "type": "type",
        "partner": "partner",
        "amount": "amount",
        "currency": "currency",
        "account": "account",
        "category": "category"
    }

    row1 = CsvRow({
        "date": "2023-01-01", "type": "card_reservation", "partner": "Test Merchant 1",
        "amount": "100", "currency": "HUF", "account": "12345", "category": ""
    }, mapping)

    row2 = CsvRow({
        "date": "2023-01-02", "type": "card_reservation", "partner": "Test Merchant 2",
        "amount": "200", "currency": "HUF", "account": "12345", "category": ""
    }, mapping)

    rows = [row1, row2]

    # Test with threshold of 0.5
    with patch('whatsthedamage.services.ml_service.MLService') as MockMLService:

        # Create mock CsvRow objects with the predicted categories and confidence
        mock_rows = [
            _create_mock_csv_row_from_prediction(row1, DummyPrediction('Grocery', 0.9), mapping),
            _create_mock_csv_row_from_prediction(row2, DummyPrediction('Dining Out', 0.4), mapping)
        ]

        MockMLService.return_value.get_predictions.return_value = mock_rows

        # Test with default threshold (0.5)
        enricher = RowEnrichmentML(rows)  # Uses default threshold of 0.5
        enricher.categorize_by_attribute("category_id")

        # Verify results - ML predictions map to category IDs via get_category_id_from_name
        assert row1.category_id == 'grocery'  # High confidence kept original
        assert row2.category_id == 'other'      # Low confidence changed to 'other'
        assert row1.confidence == pytest.approx(0.9)
        assert row2.confidence == pytest.approx(0.4)

        # Verify categorized dict
        assert 'grocery' in enricher.categorized
        assert 'other' in enricher.categorized
        assert len(enricher.categorized['grocery']) == 1
        assert len(enricher.categorized['other']) == 1


def test_row_enrichment_ml_custom_threshold():
    """Test RowEnrichmentML with custom confidence threshold."""

    # Create test row
    mapping = {
        "date": "date", "type": "type", "partner": "partner",
        "amount": "amount", "currency": "currency", "account": "account", "category": "category"
    }

    row = CsvRow({
        "date": "2023-01-01", "type": "card_reservation", "partner": "Test Merchant",
        "amount": "100", "currency": "HUF", "account": "12345", "category": ""
    }, mapping)

    rows = [row]

    with patch('whatsthedamage.services.ml_service.MLService') as MockMLService:

        # Create mock CsvRow with the predicted category and confidence
        mock_row = _create_mock_csv_row_from_prediction(row, DummyPrediction('Grocery', 0.6), mapping)

        MockMLService.return_value.get_predictions.return_value = [mock_row]

        # Test with custom threshold of 0.7
        enricher = RowEnrichmentML(rows, confidence_threshold=0.7)
        enricher.categorize_by_attribute("category_id")
        # 0.6 < 0.7, so should become 'other'
        assert row.category_id == 'other'
        assert row.confidence == pytest.approx(0.6)


def test_row_enrichment_ml_none_confidence():
    """Test RowEnrichmentML handles None confidence correctly."""

    mapping = {
        "date": "date", "type": "type", "partner": "partner",
        "amount": "amount", "currency": "currency", "account": "account", "category": "category"
    }

    row = CsvRow({
        "date": "2023-01-01", "type": "card_reservation", "partner": "Test Merchant",
        "amount": "100", "currency": "HUF", "account": "12345", "category": ""
    }, mapping)

    rows = [row]

    with patch('whatsthedamage.services.ml_service.MLService') as MockMLService:

        # Create mock CsvRow with the predicted category and None confidence
        mock_row = _create_mock_csv_row_from_prediction(row, DummyPrediction('Grocery', None), mapping)

        MockMLService.return_value.get_predictions.return_value = [mock_row]

        enricher = RowEnrichmentML(rows)
        enricher.categorize_by_attribute("category_id")

        # None confidence should keep original category (mapped from ML prediction "Grocery" -> "grocery")
        assert row.category_id == 'grocery'
        assert row.confidence is None

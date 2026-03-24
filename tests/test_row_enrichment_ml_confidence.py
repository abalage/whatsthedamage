"""Test RowEnrichmentML confidence threshold functionality."""
from unittest.mock import patch
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML


class DummyPrediction:
    def __init__(self, category, confidence):
        self.category = category
        self.confidence = confidence


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
        "amount": "100", "currency": "HUF", "account": "12345"
    }, mapping)
    
    row2 = CsvRow({
        "date": "2023-01-02", "type": "card_reservation", "partner": "Test Merchant 2",
        "amount": "200", "currency": "HUF", "account": "12345"
    }, mapping)
    
    rows = [row1, row2]
    
    # Test with threshold of 0.5
    with patch('whatsthedamage.models.row_enrichment_ml.get_category_name', side_effect=lambda x: x.upper()), \
         patch('whatsthedamage.models.row_enrichment_ml.Inference') as MockInference:
        
        # Mock predictions: first high confidence, second low confidence
        MockInference.return_value.get_predictions.return_value = [
            DummyPrediction('groceries', 0.9),  # High confidence - should keep category
            DummyPrediction('dining_out', 0.4)   # Low confidence - should become 'OTHER'
        ]
        
        # Test with default threshold (0.5)
        enricher = RowEnrichmentML(rows)  # Uses default threshold of 0.5
        enricher.categorize_by_attribute("category")
        
        # Verify results
        assert row1.category == 'GROCERIES'  # High confidence kept original
        assert row2.category == 'OTHER'      # Low confidence changed to 'other'
        assert row1.confidence == 0.9
        assert row2.confidence == 0.4
        
        # Verify categorized dict
        assert 'GROCERIES' in enricher.categorized
        assert 'OTHER' in enricher.categorized
        assert len(enricher.categorized['GROCERIES']) == 1
        assert len(enricher.categorized['OTHER']) == 1


def test_row_enrichment_ml_custom_threshold():
    """Test RowEnrichmentML with custom confidence threshold."""
    
    # Create test row
    mapping = {
        "date": "date", "type": "type", "partner": "partner",
        "amount": "amount", "currency": "currency", "account": "account", "category": "category"
    }
    
    row = CsvRow({
        "date": "2023-01-01", "type": "card_reservation", "partner": "Test Merchant",
        "amount": "100", "currency": "HUF", "account": "12345"
    }, mapping)
    
    rows = [row]
    
    with patch('whatsthedamage.models.row_enrichment_ml.get_category_name', side_effect=lambda x: x.upper()), \
         patch('whatsthedamage.models.row_enrichment_ml.Inference') as MockInference:
        
        # Mock prediction with 0.6 confidence
        MockInference.return_value.get_predictions.return_value = [
            DummyPrediction('groceries', 0.6)
        ]
        
        # Test with custom threshold of 0.7
        enricher = RowEnrichmentML(rows, confidence_threshold=0.7)
        enricher.categorize_by_attribute("category")
        
        # 0.6 < 0.7, so should become 'OTHER'
        assert row.category == 'OTHER'
        assert row.confidence == 0.6


def test_row_enrichment_ml_none_confidence():
    """Test RowEnrichmentML handles None confidence correctly."""
    
    mapping = {
        "date": "date", "type": "type", "partner": "partner",
        "amount": "amount", "currency": "currency", "account": "account", "category": "category"
    }
    
    row = CsvRow({
        "date": "2023-01-01", "type": "card_reservation", "partner": "Test Merchant",
        "amount": "100", "currency": "HUF", "account": "12345"
    }, mapping)
    
    rows = [row]
    
    with patch('whatsthedamage.models.row_enrichment_ml.get_category_name', side_effect=lambda x: x.upper()), \
         patch('whatsthedamage.models.row_enrichment_ml.Inference') as MockInference:
        
        # Mock prediction with None confidence
        MockInference.return_value.get_predictions.return_value = [
            DummyPrediction('groceries', None)
        ]
        
        enricher = RowEnrichmentML(rows)
        enricher.categorize_by_attribute("category")
        
        # None confidence should keep original category
        assert row.category == 'GROCERIES'
        assert row.confidence is None

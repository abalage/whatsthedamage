from unittest.mock import patch


class DummyPrediction:
    def __init__(self, category):
        self.category = category


def test_enrich_rows_sets_type_and_category(csv_rows):
    # Set one row's type to empty to test the 'card_reservation' logic
    csv_rows[1].type = ""
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.models.row_enrichment_ml.Inference") as MockInference:
        MockInference.return_value.get_predictions.return_value = [
            DummyPrediction("groceries"),
            DummyPrediction("other")
        ]
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].type == "deposit"
        assert csv_rows[1].type == "card_reservation"
        assert csv_rows[0].category == "groceries".upper()
        assert csv_rows[1].category == "other".upper()
        assert "groceries".upper() in enricher.categorized
        assert "other".upper() in enricher.categorized


def test_enrich_rows_category_with_spaces(csv_rows):
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.models.row_enrichment_ml.Inference") as MockInference:
        MockInference.return_value.get_predictions.return_value = [
            DummyPrediction("online shopping"),
            DummyPrediction("other")
        ]
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML(csv_rows)
        enricher._enrich_rows()
        assert csv_rows[0].category == "online_shopping".upper()
        assert "online_shopping".upper() in enricher.categorized


def test_enrich_rows_empty_rows():
    with patch("whatsthedamage.models.row_enrichment_ml.get_category_name", side_effect=lambda x: x.upper()), \
         patch("whatsthedamage.models.row_enrichment_ml.Inference") as MockInference:
        MockInference.return_value.get_predictions.return_value = []
        from whatsthedamage.models.row_enrichment_ml import RowEnrichmentML
        enricher = RowEnrichmentML([])
        enricher._enrich_rows()
        assert list(enricher.categorized.keys()) == ["other".upper()]

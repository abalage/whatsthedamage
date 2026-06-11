from whatsthedamage.models.domain.row_enrichment import RowEnrichment
from whatsthedamage.config.config import EnricherPatternSets


def test_add_category_attribute_by_partner(csv_rows):
    # Create pattern_sets with only partner patterns
    pattern_sets = EnricherPatternSets(partner={"bank_category": ["bank"]})
    enricher = RowEnrichment(csv_rows, pattern_sets)
    # Both rows have partner 'bank', should be categorized as 'bank_category'
    for row in csv_rows:
        assert getattr(row, "category_id") == "bank_category"


def test_add_category_attribute_by_type(csv_rows):
    # Create pattern_sets with only type patterns
    pattern_sets = EnricherPatternSets(type={"deposit_category": ["deposit"]})
    enricher = RowEnrichment(csv_rows, pattern_sets)
    # Both rows have type 'deposit', should be categorized as 'deposit_category'
    for row in csv_rows:
        assert getattr(row, "category_id") == "deposit_category"


def test_add_category_attribute_no_match_sets_deposit(csv_rows):
    # Change type so it doesn't match any pattern, but amount > 0
    for row in csv_rows:
        row.type = "unknown"
    # Create pattern_sets with only type patterns that won't match
    pattern_sets = EnricherPatternSets(type={"other_category": ["other"]})
    enricher = RowEnrichment(csv_rows, pattern_sets)
    # Should fall back to 'deposit' because amount > 0
    for row in csv_rows:
        assert getattr(row, "category_id") == "deposit"


def test_add_category_attribute_no_match_and_negative_amount(csv_rows):
    # Change type so it doesn't match any pattern, and amount <= 0
    for row in csv_rows:
        row.type = "unknown"
        row.amount = -10
        row.category_id = ""  # Ensure category_id is not set
    # Create pattern_sets with only type patterns that won't match
    pattern_sets = EnricherPatternSets(type={"other_category": ["other"]})
    enricher = RowEnrichment(csv_rows, pattern_sets)
    # Should fall back to 'Other'
    for row in csv_rows:
        assert getattr(row, "category_id") == "other"

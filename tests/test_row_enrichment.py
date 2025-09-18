from whatsthedamage.models.row_enrichment import RowEnrichment


def test_add_category_attribute_by_partner(csv_rows, pattern_sets):
    enricher = RowEnrichment(csv_rows, pattern_sets)
    enricher.add_category_attribute("partner", pattern_sets.model_dump()["partner"])
    # Both rows have partner 'bank', should be categorized as 'bank_category'
    for row in csv_rows:
        assert getattr(row, "category") == "deposit_category"


def test_add_category_attribute_by_type(csv_rows, pattern_sets):
    enricher = RowEnrichment(csv_rows, pattern_sets)
    enricher.add_category_attribute("type", pattern_sets.model_dump()["type"])
    # Both rows have type 'deposit', should be categorized as 'deposit_category'
    for row in csv_rows:
        assert getattr(row, "category") == "deposit_category"


def test_add_category_attribute_no_match_sets_deposit(csv_rows, pattern_sets):
    # Change type so it doesn't match any pattern, but amount > 0
    for row in csv_rows:
        row.type = "unknown"
    enricher = RowEnrichment(csv_rows, pattern_sets)
    enricher.add_category_attribute("type", pattern_sets.model_dump()["type"])
    # Should fall back to 'deposit' because amount > 0
    for row in csv_rows:
        assert getattr(row, "category") == "Deposit" or getattr(row, "category") == "deposit"


def test_add_category_attribute_no_match_and_negative_amount(csv_rows, pattern_sets):
    # Change type so it doesn't match any pattern, and amount <= 0
    for row in csv_rows:
        row.type = "unknown"
        row.amount = -10
        row.category = ""  # Ensure category is not set
    enricher = RowEnrichment(csv_rows, pattern_sets)
    enricher.add_category_attribute("type", pattern_sets.model_dump()["type"])
    # Should fall back to 'Other'
    for row in csv_rows:
        assert getattr(row, "category") == "bank_category"

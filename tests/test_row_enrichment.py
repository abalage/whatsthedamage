import pytest
from whatsthedamage.row_enrichment import RowEnrichment
from whatsthedamage.csv_row import CsvRow


@pytest.fixture
def setup_data():
    rows = [
        CsvRow({"attribute1": "value1", "attribute2": "value2"}),
        CsvRow({"attribute1": "value3", "attribute2": "value4"}),
        CsvRow({"attribute1": "value5", "attribute2": "value6"})
    ]
    pattern_sets = {
        "attribute1": {
            "category1": ["value1", "value3"],
            "category2": ["value5"]
        }
    }
    row_enrichment = RowEnrichment(rows, pattern_sets)
    return rows, pattern_sets, row_enrichment


def test_initialize(setup_data):
    _, _, row_enrichment = setup_data
    assert "category1" in row_enrichment.categorized
    assert "category2" in row_enrichment.categorized
    assert "other" in row_enrichment.categorized


def test_add_category_attribute(setup_data):
    rows, pattern_sets, row_enrichment = setup_data
    row_enrichment.add_category_attribute("attribute1", pattern_sets["attribute1"])
    assert rows[0].category == "category1"
    assert rows[1].category == "category1"
    assert rows[2].category == "category2"


def test_categorize_by_attribute(setup_data):
    _, _, row_enrichment = setup_data
    categorized = row_enrichment.categorize_by_attribute("attribute1")
    assert "value1" in categorized
    assert "value3" in categorized
    assert "value5" in categorized
    assert len(categorized["value1"]) == 1
    assert len(categorized["value3"]) == 1
    assert len(categorized["value5"]) == 1

import pytest
from whatsthedamage.models.rows_processor import RowsProcessor


@pytest.fixture
def rows_processor(app_context):
    return RowsProcessor(app_context)


def test_enrich_and_categorize_rows(rows_processor, csv_rows):
    rows_processor._category = "Test Category"
    categorized_rows = rows_processor._enrich_and_categorize_rows(csv_rows)
    assert isinstance(categorized_rows, dict)
    for category, rows in categorized_rows.items():
        assert isinstance(category, str)
        assert isinstance(rows, list)


def test_apply_filter(rows_processor, csv_rows):
    rows_processor._filter = "type1"
    rows_dict = {"type1": csv_rows, "type2": csv_rows}
    filtered_rows = rows_processor._apply_filter(rows_dict)
    assert "type1" in filtered_rows
    assert "type2" not in filtered_rows

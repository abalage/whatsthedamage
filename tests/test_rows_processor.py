import pytest
from whatsthedamage.models.rows_processor import RowsProcessor
from whatsthedamage.utils.date_converter import DateConverter


@pytest.fixture
def rows_processor(app_context):
    return RowsProcessor(app_context)


def test_filter_rows_by_date(rows_processor, csv_rows):
    rows_processor._start_date = 1672531200  # Example start date (2023-01-01)
    rows_processor._end_date = 1672617600    # Example end date (2023-01-02)
    filtered_rows = rows_processor._filter_rows(csv_rows)
    assert isinstance(filtered_rows, list)
    for filtered_set in filtered_rows:
        for _, rows in filtered_set.items():
            for row in rows:
                row_timestamp = DateConverter.convert_to_epoch(row.date, rows_processor._date_attribute_format)
                assert rows_processor._start_date <= row_timestamp <= rows_processor._end_date


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


def test_process_rows_with_valid_data(app_context, csv_rows):
    """
    Test RowsProcessor.process_rows with valid data.
    """
    processor = RowsProcessor(app_context)
    result = processor.process_rows(csv_rows)

    assert isinstance(result, dict)
    assert len(result) > 0
    for key, value in result.items():
        assert isinstance(key, str)
        assert isinstance(value, dict)
        for sub_key, sub_value in value.items():
            assert isinstance(sub_key, str)
            assert isinstance(sub_value, float)

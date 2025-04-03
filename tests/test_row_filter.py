import pytest
from datetime import datetime
from whatsthedamage.models.row_filter import RowFilter


class MockCsvRow:
    def __init__(self, date):
        self.date = date


@pytest.fixture
def sample_rows():
    return [
        MockCsvRow("2023-01-15"),
        MockCsvRow("2023-02-20"),
        MockCsvRow("2023-03-25"),
        MockCsvRow("2023-04-30"),
        MockCsvRow("2023-05-05"),
        MockCsvRow("2023-06-10"),
        MockCsvRow("2023-07-15"),
        MockCsvRow("2023-08-20"),
        MockCsvRow("2023-09-25"),
        MockCsvRow("2023-10-30"),
        MockCsvRow("2023-11-05"),
        MockCsvRow("2023-12-10"),
    ]


@pytest.fixture
def row_filter(sample_rows):
    return RowFilter(sample_rows, "%Y-%m-%d")


def test_get_month_number(row_filter):
    assert row_filter.get_month_number("2023-01-15") == "01"
    assert row_filter.get_month_number("2023-12-10") == "12"
    with pytest.raises(ValueError, match="Date value cannot be None"):
        row_filter.get_month_number(None)


def test_filter_by_date(row_filter):
    start_date = int(datetime(2023, 1, 1).timestamp())
    end_date = int(datetime(2023, 12, 31).timestamp())
    filtered_rows = row_filter.filter_by_date(start_date, end_date)
    assert len(filtered_rows[0]["99"]) == 12

    start_date = int(datetime(2023, 6, 1).timestamp())
    end_date = int(datetime(2023, 6, 30).timestamp())
    filtered_rows = row_filter.filter_by_date(start_date, end_date)
    assert len(filtered_rows[0]["99"]) == 1
    assert filtered_rows[0]["99"][0].date == "2023-06-10"


def test_filter_by_month(row_filter):
    filtered_months = row_filter.filter_by_month()
    assert len(filtered_months) == 12
    assert len(filtered_months[0]["01"]) == 1
    assert len(filtered_months[1]["02"]) == 1
    assert len(filtered_months[2]["03"]) == 1
    assert len(filtered_months[3]["04"]) == 1
    assert len(filtered_months[4]["05"]) == 1
    assert len(filtered_months[5]["06"]) == 1
    assert len(filtered_months[6]["07"]) == 1
    assert len(filtered_months[7]["08"]) == 1
    assert len(filtered_months[8]["09"]) == 1
    assert len(filtered_months[9]["10"]) == 1
    assert len(filtered_months[10]["11"]) == 1
    assert len(filtered_months[11]["12"]) == 1

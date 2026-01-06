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


def test_filter_by_date(row_filter):
    start_date = int(datetime(2023, 1, 1).timestamp())
    end_date = int(datetime(2023, 12, 31).timestamp())
    filtered_rows = row_filter.filter_by_date(start_date, end_date)
    # New API: filter_by_date returns a list of (DateField, rows) tuples
    assert len(filtered_rows[0][1]) == 12

    start_date = int(datetime(2023, 6, 1).timestamp())
    end_date = int(datetime(2023, 6, 30).timestamp())
    filtered_rows = row_filter.filter_by_date(start_date, end_date)
    assert len(filtered_rows[0][1]) == 1
    assert filtered_rows[0][1][0].date == "2023-06-10"


def test_filter_by_month_v2_grouping_and_display(row_filter):
    # Ensure filter_by_month_v2 groups rows by year-month and builds DateField display
    groups = row_filter.filter_by_month_v2()
    # We expect 12 groups for 12 distinct months
    assert len(groups) == 12

    # Check first group is January 2023 with correct display format
    jan_field, jan_rows = groups[0]
    assert jan_field.display.startswith("2023")
    # Month name appears in display (localized name for January)
    assert "January" in jan_field.display
    assert jan_field.timestamp > 0
    assert len(jan_rows) == 1

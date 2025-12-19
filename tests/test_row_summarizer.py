from whatsthedamage.models.row_summarizer import RowSummarizer
from whatsthedamage.models.csv_row import CsvRow


class MockCsvRow(CsvRow):
    def __init__(self, **kwargs):
        # Skip parent __init__ to avoid needing row and mapping parameters
        # Set attributes directly like before
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_row_summarizer_single_category():
    rows = {
        'category1': [
            MockCsvRow(amount='10.5'),
            MockCsvRow(amount='20.0'),
            MockCsvRow(amount='5.5')
        ]
    }
    summarizer = RowSummarizer(rows)
    result = summarizer.summarize()
    assert result == {'category1': 36.0, 'Balance': 36.0, 'Total Spendings': 0.0}


def test_row_summarizer_multiple_categories():
    rows = {
        'category1': [
            MockCsvRow(amount='10.5'),
            MockCsvRow(amount='20.0')
        ],
        'category2': [
            MockCsvRow(amount='15.0'),
            MockCsvRow(amount='5.0')
        ]
    }
    summarizer = RowSummarizer(rows)
    result = summarizer.summarize()
    assert result == {'category1': 30.5, 'category2': 20.0, 'Balance': 50.5, 'Total Spendings': 0.0}


def test_row_summarizer_invalid_values():
    rows = {
        'category1': [
            MockCsvRow(amount='10.5'),
            MockCsvRow(amount='invalid'),
            MockCsvRow(amount='5.5')
        ]
    }
    summarizer = RowSummarizer(rows)
    result = summarizer.summarize()
    assert result == {'category1': 16.0, 'Balance': 16.0, 'Total Spendings': 0.0}


def test_row_summarizer_missing_attribute():
    rows = {
        'category1': [
            MockCsvRow(amount='10.5'),
            MockCsvRow(),
            MockCsvRow(amount='5.5')
        ]
    }
    summarizer = RowSummarizer(rows)
    result = summarizer.summarize()
    assert result == {'category1': 16.0, 'Balance': 16.0, 'Total Spendings': 0.0}


def test_row_summarizer_empty_rows():
    rows = {}
    summarizer = RowSummarizer(rows)
    result = summarizer.summarize()
    assert result == {'Balance': 0.0, 'Total Spendings': 0.0}

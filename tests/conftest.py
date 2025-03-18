import pytest
from whatsthedamage.csv_row import CsvRow


@pytest.fixture
def mapping():
    return {
        'date': 'date',
        'type': 'type',
        'partner': 'partner',
        'amount': 'amount',
        'currency': 'currency'
    }


@pytest.fixture
def csv_rows(mapping):
    return [
        CsvRow(
            {'date': "2023-01-01", 'type': 'deposit', 'partner': 'bank', 'amount': 100, 'currency': 'EUR'},
            mapping),
        CsvRow(
            {'date': "2023-01-02", 'type': 'deposit', 'partner': 'bank', 'amount': 200, 'currency': 'EUR'},
            mapping),
    ]

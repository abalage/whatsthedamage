from whatsthedamage.models.csv_row import CsvRow
import pytest
import copy


@pytest.fixture
def setup_data():
    return {
        'date': '1990-01-01',
        'type': 'deposit',
        'partner': 'Foo Bar',
        'amount': '1000',
        'currency': 'EUR',
        'category': ''
    }


def test_csv_row_empty(mapping):
    row_data = {}
    csv_row = CsvRow(row_data, mapping)

    assert repr(csv_row) == "CsvRow(date='', type='', partner='', amount=0.0, currency='', category='', account='', notice='', confidence=None)"


def test_csv_row_initialization(setup_data, mapping):
    csv_row = CsvRow(setup_data, mapping)

    assert csv_row.date == '1990-01-01'
    assert csv_row.type == 'deposit'
    assert csv_row.partner == 'Foo Bar'
    assert csv_row.amount == 1000.0
    assert csv_row.currency == 'EUR'
    assert csv_row.category == ''


def test_csv_row_repr(setup_data, mapping):
    csv_row = CsvRow(setup_data, mapping)

    expected_repr = "CsvRow(date='1990-01-01', type='deposit', partner='Foo Bar', amount=1000.0, currency='EUR', category='', account='', notice='', confidence=None)"
    assert repr(csv_row) == expected_repr


def test_csv_row_equality(csv_rows):
    csv_row1 = csv_rows[0]

    csv_row1_copy = copy.deepcopy(csv_row1)

    assert csv_row1 == csv_row1_copy


def test_csv_row_inequality(setup_data, mapping):
    csv_row1 = CsvRow(setup_data, mapping)
    different_data = setup_data.copy()
    different_data['amount'] = '2000'
    csv_row2 = CsvRow(different_data, mapping)

    assert csv_row1 != csv_row2


def test_csv_row_notice_field(mapping):
    """Test that notice field is correctly parsed from CSV row."""
    row_data = {
        'date': '1990-01-01',
        'type': 'deposit',
        'partner': 'Foo Bar',
        'amount': '1000',
        'currency': 'EUR',
        'category': '',
        'notice': 'Payment for invoice #1234'
    }
    csv_row = CsvRow(row_data, mapping)
    assert csv_row.notice == 'Payment for invoice #1234'


def test_csv_row_notice_empty(mapping):
    """Test that notice field defaults to empty string when not present."""
    row_data = {
        'date': '1990-01-01',
        'type': 'deposit',
        'partner': 'Foo Bar',
        'amount': '1000',
        'currency': 'EUR',
        'category': ''
    }
    csv_row = CsvRow(row_data, mapping)
    assert csv_row.notice == ''

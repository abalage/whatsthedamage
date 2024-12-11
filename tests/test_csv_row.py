from whatsthedamage.csv_row import CsvRow
import pytest


@pytest.fixture
def setup_data():
    return {'name': 'John Doe', 'age': '30', 'city': 'New York'}


def test_csv_row_initialization(setup_data):
    csv_row = CsvRow(setup_data)

    assert csv_row.name == 'John Doe'
    assert csv_row.age == '30'
    assert csv_row.city == 'New York'


def test_csv_row_repr(setup_data):
    csv_row = CsvRow(setup_data)

    expected_repr = "<CsvRow(name=John Doe, age=30, city=New York)>"
    assert repr(csv_row) == expected_repr


def test_csv_row_empty():
    row_data = {}
    csv_row = CsvRow(row_data)

    assert repr(csv_row) == "<CsvRow()>"

import os
import pytest
import tempfile
from typing import List, Dict
from whatsthedamage.csv_file_handler import CsvFileHandler
from whatsthedamage.csv_row import CsvRow


def create_sample_csv_from_fixture(csv_rows: List[CsvRow], mapping: Dict[str, str] = {}) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        sample_csv_path = temp_file.name
        writer = CsvFileHandler(sample_csv_path, mapping=mapping)
        writer.write(sample_csv_path, csv_rows)
    return sample_csv_path


def test_csv_file_reader_init():
    filename = 'tests/sample.csv'
    dialect = 'excel'
    delimiter = ','
    mapping = {}

    reader = CsvFileHandler(filename, dialect, delimiter, mapping)

    assert reader._filename == filename
    assert reader._dialect == dialect
    assert reader._delimiter == delimiter
    assert reader._headers == []
    assert reader._rows == []
    assert reader._mapping == {}


def test_csv_file_reader_get_headers(csv_rows, mapping):
    filename = create_sample_csv_from_fixture(csv_rows, mapping)
    static_headers = list(mapping.keys())

    reader = CsvFileHandler(filename, dialect='excel-tab', delimiter='\t', mapping=mapping)

    reader.read()
    headers = reader.get_headers()

    # remove trailing spaces
    headers = [header.rstrip() for header in headers]

    assert headers == static_headers

    os.remove(filename)


def test_csv_file_reader_get_rows(csv_rows, mapping):
    filename = create_sample_csv_from_fixture(csv_rows, mapping)

    reader = CsvFileHandler(filename, dialect='excel-tab', delimiter='\t', mapping=mapping)
    reader.read()
    rows = reader.get_rows()

    assert len(rows) == len(csv_rows)  # Ensure there are rows read
    assert all(isinstance(row, CsvRow) for row in rows)  # Ensure all rows are CsvRow objects
    assert rows == csv_rows  # Ensure the rows match the fixture data

    os.remove(filename)


def test_csv_file_reader_file_not_found():
    filename = 'tests/non_existent_file.csv'
    reader = CsvFileHandler(filename)

    with pytest.raises(FileNotFoundError):
        reader.read()


def test_csv_file_reader_empty_file():
    empty_filename = "tests/empty.csv"
    with open(empty_filename, "w"):
        pass  # Create an empty file

    reader = CsvFileHandler(empty_filename)

    with pytest.raises(ValueError, match="CSV file is empty or missing headers."):
        reader.read()

    os.remove(empty_filename)


# def test_csv_file_reader_different_dialect(csv_rows, mapping):
#     #filename = create_sample_csv_from_fixture(csv_rows, mapping)

#     reader = CsvFileReader(filename, dialect='excel', delimiter=',', mapping=mapping)

#     reader.read()

#     headers = reader.get_headers()
#     rows = reader.get_rows()

#     assert headers == list(mapping.keys())
#     assert len(rows) == 2
#     assert rows[0].data == csv_rows[0].data
#     assert rows[1].data == csv_rows[1].data

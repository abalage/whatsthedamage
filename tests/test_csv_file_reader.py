from whatsthedamage.csv_file_reader import CsvFileReader
from whatsthedamage.csv_row import CsvRow


def test_csv_file_reader_init():
    filename = 'tests/sample.csv'
    dialect = 'excel'
    delimiter = ','

    reader = CsvFileReader(filename, dialect, delimiter)

    assert reader.filename == filename
    assert reader.dialect == dialect
    assert reader.delimiter == delimiter
    assert reader.headers == []
    assert reader.rows == []


def test_csv_file_reader_get_headers():
    filename = 'tests/sample.csv'
    static_headers = [
        "attribute1",
        "attribute2",
        "attribute3",
        "attribute4",
        "attribute5",
        "attribute6",
        "attribute7",
        "attribute8",
        "attribute9",
        "attribute10",
        "attribute11",
        "attribute12",
        "attribute13",
        "attribute14",
        "attribute15",
        "attribute16",
        "attribute17",
        "attribute18",
        "attribute19",
        "attribute20",
        "attribute21"
    ]

    reader = CsvFileReader(filename)

    reader.read()
    headers = reader.get_headers()

    # remove trailing spaces
    headers = [header.rstrip() for header in headers]

    assert headers == static_headers


def test_csv_file_reader_get_rows():
    filename = 'tests/sample.csv'

    reader = CsvFileReader(filename)
    reader.read()
    rows = reader.get_rows()

    assert len(rows) > 0  # Ensure there are rows read
    assert all(isinstance(row, CsvRow) for row in rows)  # Ensure all rows are CsvRow objects

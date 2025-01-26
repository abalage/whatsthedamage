import pytest
from whatsthedamage.rows_processor import RowsProcessor
from whatsthedamage.csv_row import CsvRow
from whatsthedamage.date_converter import DateConverter


@pytest.fixture
def config():
    return {
        'csv': {
            'date_attribute': 'date',
            'date_attribute_format': '%Y-%m-%d',
            'sum_attribute': 'amount'
        },
        'main': {
            'selected_attributes': ['date', 'amount', 'category']
        },
        'enricher_pattern_sets': {
            'patterns': {
                'category1': ['pattern1', 'pattern2'],
                'category2': ['pattern3', 'pattern4']
            }
        }
    }


@pytest.fixture
def rows():
    return [
        CsvRow({'date': '2023-01-01', 'amount': 100, 'category': 'category1'}),
        CsvRow({'date': '2023-01-15', 'amount': 200, 'category': 'category2'}),
        CsvRow({'date': '2023-02-01', 'amount': 150, 'category': 'category1'})
    ]


def test_set_start_date(config):
    processor = RowsProcessor(config)
    processor.set_start_date('2023-01-01')
    assert processor._start_date == DateConverter.convert_to_epoch('2023-01-01', '%Y-%m-%d')


def test_set_end_date(config):
    processor = RowsProcessor(config)
    processor.set_end_date('2023-12-31')
    assert processor._end_date == DateConverter.convert_to_epoch('2023-12-31', '%Y-%m-%d')


def test_set_verbose(config):
    processor = RowsProcessor(config)
    processor.set_verbose(True)
    assert processor._verbose is True


def test_set_category(config):
    processor = RowsProcessor(config)
    processor.set_category('category1')
    assert processor._category == 'category1'


def test_set_filter(config):
    processor = RowsProcessor(config)
    processor.set_filter('category1')
    assert processor._filter == 'category1'


def test_process_rows(config, rows):
    processor = RowsProcessor(config)
    processor.set_category('category')
    processor.set_verbose(False)
    summary = processor.process_rows(rows)
    assert 'January' in summary
    assert 'February' in summary
    assert summary['January']['category1'] == 100
    assert summary['January']['category2'] == 200
    assert summary['February']['category1'] == 150


def test_process_rows_date_filter(config, rows):
    processor = RowsProcessor(config)
    processor.set_start_date('2023-01-01')
    processor.set_end_date('2023-12-31')
    processor.set_category('category')
    processor.set_verbose(True)
    summary = processor.process_rows(rows)
    assert '2023-01-01 - 2023-12-31' in summary
    assert summary['2023-01-01 - 2023-12-31']['category1'] == 250
    assert summary['2023-01-01 - 2023-12-31']['category2'] == 200
    assert summary['2023-01-01 - 2023-12-31']['other'] == 0

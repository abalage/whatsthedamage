import pytest
from whatsthedamage.models.rows_processor import RowsProcessor
from whatsthedamage.models.date_converter import DateConverter
from whatsthedamage.config.config import AppConfig, CsvConfig, MainConfig


@pytest.fixture
def rows_processor():
    return RowsProcessor()


@pytest.fixture
def app_config():
    csv_config = CsvConfig(
        dialect="excel",
        delimiter=",",
        date_attribute_format="%Y-%m-%d",
        attribute_mapping={"date": "date", "amount": "amount"},
    )
    main_config = MainConfig(
        locale="en_US",
        selected_attributes=["date", "amount"]
    )
    enricher_pattern_sets = {
        "category1": {
            "pattern1": ["value1", "value2"],
            "pattern2": ["value3", "value4"]
        }
    }
    return AppConfig(csv=csv_config, main=main_config, enricher_pattern_sets=enricher_pattern_sets)


def test_set_date_attribute_format(rows_processor, app_config):
    rows_processor.set_date_attribute_format(app_config.csv.date_attribute_format)
    assert rows_processor._date_attribute_format == app_config.csv.date_attribute_format


def test_set_cfg_pattern_sets(rows_processor, app_config):
    rows_processor.set_cfg_pattern_sets(app_config.enricher_pattern_sets)
    assert rows_processor._cfg_pattern_sets == app_config.enricher_pattern_sets


def test_set_start_date(rows_processor, app_config):
    rows_processor.set_date_attribute_format(app_config.csv.date_attribute_format)
    rows_processor.set_start_date("2023-01-01")
    assert rows_processor._start_date == DateConverter.convert_to_epoch("2023-01-01", app_config.csv.date_attribute_format)  # noqa: E501


def test_set_end_date(rows_processor, app_config):
    rows_processor.set_date_attribute_format(app_config.csv.date_attribute_format)
    rows_processor.set_end_date("2023-12-31")
    assert rows_processor._end_date == DateConverter.convert_to_epoch("2023-12-31", app_config.csv.date_attribute_format)  # noqa: E501


def test_set_verbose(rows_processor):
    rows_processor.set_verbose(True)
    assert rows_processor._verbose is True


def test_set_category(rows_processor, app_config):
    rows_processor.set_category("category")
    assert rows_processor._category == "category"


def test_set_filter(rows_processor):
    rows_processor.set_filter("filter")
    assert rows_processor._filter == "filter"


def test_print_categorized_rows(capsys, rows_processor, csv_rows):
    rows_processor.set_verbose(True)
    rows_dict = {"type1": csv_rows}
    rows_processor._print_categorized_rows("Test Set", rows_dict)
    captured = capsys.readouterr()
    assert "Set name: Test Set" in captured.out
    assert "Type: type1" in captured.out
    for row in csv_rows:
        assert repr(row) in captured.out


def test_process_rows(rows_processor, app_config, csv_rows, capsys):
    rows_processor.set_date_attribute_format(app_config.csv.date_attribute_format)
    rows_processor.set_cfg_pattern_sets(app_config.enricher_pattern_sets)
    rows_processor.set_start_date("2023-01-01")
    rows_processor.set_end_date("2023-12-31")
    rows_processor.set_category("category")
    rows_processor.set_filter("filter")
    rows_processor.set_verbose(True)

    summary = rows_processor.process_rows(csv_rows)

    assert isinstance(summary, dict)
    assert "January" in summary or "2023-01-01 - 2023-12-31" in summary

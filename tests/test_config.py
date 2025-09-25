import pytest
import yaml
from whatsthedamage.config.config import load_config, AppConfig, AppArgs


def test_load_config_valid_file(tmp_path):
    config_data = {
        "csv": {
            "dialect": "excel",
            "delimiter": ",",
            "date_attribute_format": "%Y-%m-%d",
            "attribute_mapping": {"date": "date", "amount": "sum"}
        },
        "enricher_pattern_sets": {
            "type": {
                "subpattern1": ["value1", "value2"]
            },
            "partner": {}
        }
    }
    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump(config_data))

    config = load_config(config_file)
    assert isinstance(config, AppConfig)
    assert config.csv.dialect == "excel"


def test_load_config_invalid_yaml(tmp_path):
    invalid_yaml = "{invalid_yaml: [}"
    config_file = tmp_path / "config.yml"
    config_file.write_text(invalid_yaml)

    with pytest.raises(SystemExit):
        load_config(config_file)


def test_load_config_file_not_found():
    with pytest.raises(SystemExit):
        load_config("non_existent_config.yml")


def test_app_args_required_fields():
    args: AppArgs = {
        "category": "test_category",
        "config": "test_config",
        "filename": "test_file",
        "no_currency_format": False,
        "nowrap": False,
        "output_format": "csv",
        "verbose": True,
        "end_date": None,
        "filter": None,
        "output": None,
        "start_date": None,
        "lang": None,
        "training_data": False,
        "ml": False,
    }
    assert args["category"] == "test_category"
    assert args["config"] == "test_config"
    assert args["filename"] == "test_file"
    assert args["no_currency_format"] is False
    assert args["nowrap"] is False
    assert args["output_format"] == "csv"
    assert args["verbose"] is True


def test_app_args_optional_fields():
    args: AppArgs = {
        "category": "test_category",
        "config": "test_config",
        "filename": "test_file",
        "no_currency_format": False,
        "nowrap": False,
        "output_format": "csv",
        "verbose": True,
        "end_date": "2023-12-31",
        "filter": "test_filter",
        "output": "test_output",
        "start_date": "2023-01-01",
        "lang": None,
        "training_data": True,
        "ml": True,
    }
    assert args["end_date"] == "2023-12-31"
    assert args["filter"] == "test_filter"
    assert args["output"] == "test_output"
    assert args["start_date"] == "2023-01-01"
    assert args["training_data"] is True
    assert args["ml"] is True

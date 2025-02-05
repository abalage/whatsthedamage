import pytest
import json
from pydantic import ValidationError
from whatsthedamage.config import load_config, AppConfig, CsvConfig, MainConfig

def test_load_config_valid_file(tmp_path):
    config_data = {
        "csv": {
            "dialect": "excel",
            "delimiter": ",",
            "date_attribute": "date",
            "date_attribute_format": "%Y-%m-%d",
            "sum_attribute": "amount"
        },
        "main": {
            "locale": "en_US",
            "selected_attributes": ["attribute1", "attribute2"]
        },
        "enricher_pattern_sets": {
            "pattern1": {
                "subpattern1": ["value1", "value2"]
            }
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    config = load_config(str(config_file))
    assert isinstance(config, AppConfig)
    assert config.csv.dialect == "excel"
    assert config.main.locale == "en_US"

def test_load_config_invalid_json(tmp_path):
    invalid_json = "{invalid_json}"
    config_file = tmp_path / "config.json"
    config_file.write_text(invalid_json)

    with pytest.raises(SystemExit):
        load_config(str(config_file))

def test_load_config_validation_error(tmp_path):
    invalid_config_data = {
        "csv": {
            "dialect": "excel",
            "delimiter": ",",
            "date_attribute": "date",
            "date_attribute_format": "%Y-%m-%d"
            # Missing sum_attribute
        },
        "main": {
            "locale": "en_US",
            "selected_attributes": ["attribute1", "attribute2"]
        },
        "enricher_pattern_sets": {
            "pattern1": {
                "subpattern1": ["value1", "value2"]
            }
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(invalid_config_data))

    with pytest.raises(SystemExit):
        load_config(str(config_file))
'''
The configuration is coming from two directions:
1. arguments passed to the main method (AppArgs object)
2. read from a configuration file (AppConfig object).
'''
from typing import TypedDict, List, Dict
import json
import sys
from pydantic import BaseModel, ValidationError


class AppArgs(TypedDict):
    category: str
    config: str
    end_date: str | None
    filename: str
    filter: str | None
    no_currency_format: bool
    nowrap: bool
    output_format: str
    output: str | None
    start_date: str | None
    verbose: bool


class CsvConfig(BaseModel):
    dialect: str
    delimiter: str
    date_attribute_format: str
    attribute_mapping: Dict[str, str]


class MainConfig(BaseModel):
    locale: str


class AppConfig(BaseModel):
    csv: CsvConfig
    main: MainConfig
    enricher_pattern_sets: Dict[str, Dict[str, List[str]]]


def load_config(config_path: str) -> AppConfig:
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
            config = AppConfig(**config_data)
        return config
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{config_path}' is not a valid JSON.", file=sys.stderr)
        exit(1)
    except ValidationError as e:
        print(f"Error: Configuration validation error: {e}", file=sys.stderr)
        exit(1)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
        exit(1)

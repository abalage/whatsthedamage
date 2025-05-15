'''
The configuration is coming from two directions:
1. arguments passed to the main method (AppArgs object)
2. read from a configuration file (AppConfig object).
'''
from typing import TypedDict, List, Dict
import yaml
import sys
from pydantic import BaseModel, ValidationError, Field
from gettext import gettext as _


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
    lang: str | None


class CsvConfig(BaseModel):
    dialect: str
    delimiter: str
    date_attribute_format: str
    attribute_mapping: Dict[str, str]


class CategoryDefinition(BaseModel):
    id: str
    default_name: str
    patterns: List[str]


AVAILABLE_CATEGORIES = [
    CategoryDefinition(id="grocery", default_name=_("Grocery"), patterns=[]),
    CategoryDefinition(id="clothes", default_name=_("Clothes"), patterns=[]),
    CategoryDefinition(id="health", default_name=_("Health"), patterns=[]),
    CategoryDefinition(id="payment", default_name=_("Payment"), patterns=[]),
    CategoryDefinition(id="vehicle", default_name=_("Vehicle"), patterns=[]),
    CategoryDefinition(id="utility", default_name=_("Utility"), patterns=[]),
    CategoryDefinition(id="home_maintenance", default_name=_("Home Maintenance"), patterns=[]),
    CategoryDefinition(id="loan", default_name=_("Loan"), patterns=[]),
    CategoryDefinition(id="withdrawal", default_name=_("Withdrawal"), patterns=[]),
    CategoryDefinition(id="fee", default_name=_("Fee"), patterns=[]),
    CategoryDefinition(id="deposit", default_name=_("Deposit"), patterns=[]),
    CategoryDefinition(id="refund", default_name=_("Refund"), patterns=[]),
    CategoryDefinition(id="interest", default_name=_("Interest"), patterns=[]),
    CategoryDefinition(id="transfer", default_name=_("Transfer"), patterns=[]),
    CategoryDefinition(id="other", default_name=_("Other"), patterns=[]),
    CategoryDefinition(id="balance", default_name=_("Balance"), patterns=[]),
]


class EnricherPatternSets(BaseModel):
    partner: Dict[str, List[str]] = Field(default_factory=dict)
    type: Dict[str, List[str]] = Field(default_factory=dict)


class AppConfig(BaseModel):
    csv: CsvConfig
    enricher_pattern_sets: EnricherPatternSets


class AppContext:
    """
    AppContext encapsulates the application configuration and arguments.

    Attributes:
        config (AppConfig): The application configuration.
        args (AppArgs): The application arguments.
    """
    def __init__(self, config: AppConfig, args: AppArgs):
        self.config: AppConfig = config
        self.args: AppArgs = args


def load_config(config_path: str) -> AppConfig:
    """
    Load the application configuration from a YAML file.

    :param config_path: Path to the YAML configuration file.
    :return: An AppConfig object.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            config = AppConfig(**config_data)
        return config
    except yaml.YAMLError as e:
        print(f"Error: Configuration file '{config_path}' is not a valid YAML: {e}", file=sys.stderr)
        exit(1)
    except ValidationError as e:
        print(f"Error: Configuration validation error: {e}", file=sys.stderr)
        exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        exit(1)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
        exit(1)


def get_category_name(category_id: str) -> str:
    for cat in AVAILABLE_CATEGORIES:
        if cat.id == category_id:
            return get_localized_category_name(cat.default_name)
    return category_id


def get_localized_category_name(default_name: str) -> str:
    """
    Get the localized name of a category using gettext.

    :param default_name: The default name of the category.
    :return: The localized category name.
    """
    return _(default_name)

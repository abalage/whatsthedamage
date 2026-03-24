'''
The configuration is coming from two directions:
1. arguments passed to the main method (AppArgs object)
2. read from a configuration file (AppConfig object).
'''
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import yaml
from pydantic import BaseModel, ValidationError, Field
from gettext import gettext as _
from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AppArgs:
    """Application arguments dataclass.

    Replaces the original TypedDict with a more flexible dataclass
    that supports methods and better IDE integration.
    """
    category: str
    config: str
    filename: str
    output_format: str
    nowrap: bool
    verbose: bool
    training_data: bool
    ml: bool
    log_level: str = "WARN"
    log_output: str = "stdout"
    log_format: str = "text"
    end_date: Optional[str] = None
    filter: Optional[str] = None
    output: Optional[str] = None
    start_date: Optional[str] = None
    lang: Optional[str] = None

class CsvConfig(BaseModel):
    dialect: str = Field(default="excel-tab")
    delimiter: str = Field(default="\t")
    date_attribute_format: str = Field(default="%Y.%m.%d")
    attribute_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "date": "könyvelés dátuma",
        "type": "típus",
        "partner": "partner elnevezése",
        "amount": "összeg",
        "currency": "összeg devizaneme",
        "account": "könyvelési számla"
    })


class CategoryDefinition(BaseModel):
    id: str
    default_name: str
    patterns: List[str]


AVAILABLE_CATEGORIES = [
    CategoryDefinition(id="grocery", default_name=_("Grocery"), patterns=[]),
    CategoryDefinition(id="clothes", default_name=_("Clothes"), patterns=[]),
    CategoryDefinition(id="dining_out", default_name=_("Dining Out"), patterns=[]),
    CategoryDefinition(id="health", default_name=_("Health"), patterns=[]),
    CategoryDefinition(id="payment", default_name=_("Payment"), patterns=[]),
    CategoryDefinition(id="transportation", default_name=_("Transportation"), patterns=[]),
    CategoryDefinition(id="utility", default_name=_("Utility"), patterns=[]),
    CategoryDefinition(id="home_maintenance", default_name=_("Home Maintenance"), patterns=[]),
    CategoryDefinition(id="entertainment_and_leisure", default_name=_("Entertainment and Leisure"), patterns=[]),
    CategoryDefinition(id="insurance", default_name=_("Insurance"), patterns=[]),
    CategoryDefinition(id="loan", default_name=_("Loan"), patterns=[]),
    CategoryDefinition(id="withdrawal", default_name=_("Withdrawal"), patterns=[]),
    CategoryDefinition(id="fee", default_name=_("Fee"), patterns=[]),
    CategoryDefinition(id="deposit", default_name=_("Deposit"), patterns=[]),
    CategoryDefinition(id="refund", default_name=_("Refund"), patterns=[]),
    CategoryDefinition(id="interest", default_name=_("Interest"), patterns=[]),
    CategoryDefinition(id="electronics_digital_services", default_name=_("Electronics and Digital Services"), patterns=[]),
    CategoryDefinition(id="transfer", default_name=_("Transfer"), patterns=[]),
    CategoryDefinition(id="other", default_name=_("Other"), patterns=[]),
    CategoryDefinition(id="balance", default_name=_("Balance"), patterns=[]),
    CategoryDefinition(id="total_spendings", default_name=_("Total Spendings"), patterns=[]),
]


class EnricherPatternSets(BaseModel):
    type: Dict[str, List[str]] = Field(default_factory=dict)
    partner: Dict[str, List[str]] = Field(default_factory=dict)


class AppConfig(BaseModel):
    csv: CsvConfig
    enricher_pattern_sets: EnricherPatternSets
    text_cleaning: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enabled_statistical_algorithms: List[str] = Field(default_factory=lambda: ['iqr', 'pareto'])
    cache_ttl: int = Field(default=1800)  # 30 minutes in seconds
    ml_config: MLConfig = Field(default_factory=MLConfig)  # ML configuration including confidence threshold


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


def load_config(config_path: str | None) -> AppConfig:
    """
    Load the application configuration from a YAML file.

    :param config_path: Path to the YAML configuration file.
    :return: An AppConfig object.
    """
    if not config_path or config_path == "":
        logger.warning("No configuration file provided, using default settings")
        return AppConfig(
            csv=CsvConfig(),
            enricher_pattern_sets=EnricherPatternSets()
        )
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            config = AppConfig(**config_data)
        return config
    except yaml.YAMLError as e:
        logger.error(f"Configuration file '{config_path}' is not a valid YAML: {e}")
        exit(1)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_path}' not found")
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

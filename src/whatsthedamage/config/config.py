'''
The configuration is coming from two directions:
1. arguments passed to the main method (AppArgs object)
2. read from a configuration file (AppConfig object).
'''
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import yaml
from pydantic import BaseModel, ValidationError, Field
from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AppArgs:
    """Application arguments dataclass.

    Replaces the original TypedDict with a more flexible dataclass
    that supports methods and better IDE integration.
    """
    config: str
    filename: str
    category_id: str
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
        "account": "könyvelési számla",
        "notice": "közlemény"
    })


class CategoryDefinition(BaseModel):
    id: str
    default_name: str
    patterns: List[str]


AVAILABLE_CATEGORIES = [
    CategoryDefinition(id="grocery", default_name="Grocery", patterns=[]),
    CategoryDefinition(id="clothes", default_name="Clothes", patterns=[]),
    CategoryDefinition(id="dining_out", default_name="Dining Out", patterns=[]),
    CategoryDefinition(id="health", default_name="Health", patterns=[]),
    CategoryDefinition(id="payment", default_name="Payment", patterns=[]),
    CategoryDefinition(id="transportation", default_name="Transportation", patterns=[]),
    CategoryDefinition(id="utility", default_name="Utility", patterns=[]),
    CategoryDefinition(id="home_maintenance", default_name="Home Maintenance", patterns=[]),
    CategoryDefinition(id="entertainment_and_leisure", default_name="Entertainment and Leisure", patterns=[]),
    CategoryDefinition(id="insurance", default_name="Insurance", patterns=[]),
    CategoryDefinition(id="loan", default_name="Loan", patterns=[]),
    CategoryDefinition(id="withdrawal", default_name="Withdrawal", patterns=[]),
    CategoryDefinition(id="fee", default_name="Fee", patterns=[]),
    CategoryDefinition(id="deposit", default_name="Deposit", patterns=[]),
    CategoryDefinition(id="refund", default_name="Refund", patterns=[]),
    CategoryDefinition(id="interest", default_name="Interest", patterns=[]),
    CategoryDefinition(id="electronics_digital_services", default_name="Electronics and Digital Services", patterns=[]),
    CategoryDefinition(id="transfer", default_name="Transfer", patterns=[]),
    CategoryDefinition(id="other", default_name="Other", patterns=[]),
    CategoryDefinition(id="balance", default_name="Balance", patterns=[]),
    CategoryDefinition(id="total_spendings", default_name="Total Spendings", patterns=[]),
    CategoryDefinition(id="cost_of_living", default_name="Cost of Living", patterns=[]),
]

# Default categories that constitute Cost of Living
# These are category IDs (lowercase, underscores)
COST_OF_LIVING_CATEGORY_IDS = [
    "grocery",
    "loan",
    "transportation",
    "utility",
    "payment",
    "fee",
    "health"
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


def get_category_by_id(category_id: str) -> Optional[CategoryDefinition]:
    """Get CategoryDefinition by ID.

    Args:
        category_id: The category ID to look up (e.g., 'grocery', 'clothes')

    Returns:
        The CategoryDefinition object if found, None otherwise.
    """
    for cat in AVAILABLE_CATEGORIES:
        if cat.id == category_id:
            return cat
    return None


def get_category_display_name(category_id: str) -> str:
    """Get display name for a category ID.

    Returns the plain English default_name from CategoryDefinition.
    This is used by CLI and any backend code that needs to display category names.
    For frontend display, use category_id as translation key in frontend PO files.

    Args:
        category_id: The category ID to get display name for (e.g., 'grocery')

    Returns:
        The display name, or the category_id if not found.
    """
    category = get_category_by_id(category_id)
    if category:
        return category.default_name
    return category_id  # fallback to ID if not found


def get_category_id_from_name(category_name: str) -> str:
    """Get category ID from a display name.

    This function tries to find a matching category by comparing the input
    against both the default_name and id fields. It also handles common
    transformations like replacing spaces with underscores.

    Args:
        category_name: The display name or ID to look up (e.g., 'Grocery', 'grocery',
                      'Cost of Living', 'cost_of_living', 'Konyha')

    Returns:
        The category ID if found, otherwise returns the lowercased input
        with spaces replaced by underscores as a fallback.
    """
    # First, try exact match on id
    for cat in AVAILABLE_CATEGORIES:
        if cat.id == category_name:
            return cat.id

    # Then, try exact match on default_name
    for cat in AVAILABLE_CATEGORIES:
        if cat.default_name == category_name:
            return cat.id

    # Try case-insensitive match on id
    category_lower = category_name.lower()
    for cat in AVAILABLE_CATEGORIES:
        if cat.id == category_lower:
            return cat.id

    # Try case-insensitive match on default_name
    for cat in AVAILABLE_CATEGORIES:
        if cat.default_name.lower() == category_lower:
            return cat.id

    # Fallback: convert input to ID format (lowercase, underscores for spaces)
    # This handles ML predictions that use display names
    normalized = category_lower.replace(" ", "_")
    for cat in AVAILABLE_CATEGORIES:
        if cat.id == normalized:
            return cat.id

    # If still not found, return the normalized version
    # This could happen with translated names, but we'll use it as-is
    return normalized


def get_localized_category_name(default_name: str) -> str:
    """
    Get the category name.

    Note: This function now returns the plain English name.
    For localized display, frontend should use category_id as translation key.

    :param default_name: The default name of the category.
    :return: The category name.
    """
    return default_name

# src/whatsthedamage/utils/data_loader.py
import json
from typing import Any
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


def load_json_data(filepath: str) -> Any:
    """
    Load JSON data from a file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        The loaded JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON.
        RuntimeError: If an unexpected error occurs.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        error_msg = f"Error: File '{filepath}' not found."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e
    except json.JSONDecodeError as e:
        error_msg = f"Error: File '{filepath}' is not valid JSON."
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Error: An unexpected error occurred while reading '{filepath}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
"""Configuration module for whatsthedamage package.

This module provides utilities for accessing configuration files
that work both during development and after package installation.
"""

from pathlib import Path

def get_config_file_path(filename: str) -> str:
    """Get the absolute path to a configuration file.

    This function works both during development (when files are in the filesystem)
    and after package installation (when files are in the package resources).

    Args:
        filename: Name of the configuration file (e.g., 'config.yml.default')

    Returns:
        Absolute path to the configuration file
    """
    # Get the path relative to this file (works for both development and installed packages)
    current_file_path = Path(__file__).parent
    return str(current_file_path / filename)

# Canonical path constants
DEFAULT_CONFIG_PATH = get_config_file_path('config.yml.default')
DEFAULT_EXCLUSIONS_PATH = get_config_file_path('exclusions.json')

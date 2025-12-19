"""Configuration service for loading and validating application configuration.

This service centralizes configuration management to eliminate duplication
between CLI, web routes, and API endpoints.
"""
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
import os

from whatsthedamage.config.config import AppConfig, load_config as _load_config_internal
from whatsthedamage.utils.validation import ValidationResult


@dataclass
class ConfigLoadResult:
    """Result of a configuration loading operation.

    Attributes:
        config: The loaded configuration object (None if loading failed)
        validation_result: Result of validation
    """
    config: Optional[AppConfig]
    validation_result: ValidationResult

    @classmethod
    def success(cls, config: AppConfig) -> 'ConfigLoadResult':
        """Create a successful config load result."""
        return cls(
            config=config,
            validation_result=ValidationResult.success()
        )

    @classmethod
    def failure(
        cls,
        error_message: str,
        error_code: str = 'CONFIG_LOAD_ERROR'
    ) -> 'ConfigLoadResult':
        """Create a failed config load result."""
        return cls(
            config=None,
            validation_result=ValidationResult.failure(error_message, error_code)
        )


class ConfigurationService:
    """Service for managing application configuration.

    Centralizes configuration loading, validation, and path resolution
    to eliminate duplication across controllers and services.
    """

    def __init__(self) -> None:
        """Initialize configuration service."""
        pass

    def load_config(self, file_path: Optional[str] = None) -> ConfigLoadResult:
        """Load configuration from file or use defaults.

        Args:
            file_path: Path to YAML config file (None for defaults)

        Returns:
            ConfigLoadResult with loaded config or error
        
        Note:
            The internal load_config function calls exit() on error.
            This service wraps it for better error handling in web/API contexts.
        """
        config = _load_config_internal(file_path)
        return ConfigLoadResult.success(config)

    def get_default_config(self) -> AppConfig:
        """Get default configuration.

        Returns:
            AppConfig: Default configuration object
        """
        return _load_config_internal(None)

    def resolve_config_path(
        self,
        user_path: Optional[str],
        ml_enabled: bool,
        default_config_path: Optional[str] = None
    ) -> Optional[str]:
        """Resolve configuration file path with fallback logic.

        Args:
            user_path: User-provided config path (may be empty string or None)
            ml_enabled: Whether ML mode is enabled (doesn't require config)
            default_config_path: Path to default config file (optional)

        Returns:
            Resolved config path or None if ML mode or no config needed

        Raises:
            ValueError: If default config is required but not found
        """
        # If user provided a path, use it
        if user_path:
            return user_path

        # ML mode doesn't require config
        if ml_enabled:
            return None

        # No default config specified, use None (will load defaults)
        if not default_config_path:
            return None

        # Use default config if it exists
        if os.path.exists(default_config_path):
            return default_config_path

        # Default config specified but not found
        raise ValueError('Default config file not found. Please upload one.')

    def validate_config_path(self, file_path: str) -> ValidationResult:
        """Validate that a configuration file exists and is readable.

        Args:
            file_path: Path to configuration file

        Returns:
            ValidationResult indicating success or failure
        """
        if not file_path:
            return ValidationResult.failure(
                "Configuration file path is empty",
                "EMPTY_CONFIG_PATH"
            )

        path = Path(file_path)

        if not path.exists():
            return ValidationResult.failure(
                f"Configuration file not found: {file_path}",
                "CONFIG_FILE_NOT_FOUND"
            )

        if not path.is_file():
            return ValidationResult.failure(
                f"Configuration path is not a file: {file_path}",
                "CONFIG_PATH_NOT_FILE"
            )

        if not os.access(file_path, os.R_OK):
            return ValidationResult.failure(
                f"Configuration file is not readable: {file_path}",
                "CONFIG_FILE_NOT_READABLE"
            )

        return ValidationResult.success()

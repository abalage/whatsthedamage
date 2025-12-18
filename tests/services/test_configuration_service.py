"""Tests for ConfigurationService."""

import yaml

from whatsthedamage.services.configuration_service import (
    ConfigurationService,
    ConfigLoadResult,
)
from whatsthedamage.config.config import AppConfig, CsvConfig, EnricherPatternSets


class TestConfigLoadResult:
    """Tests for ConfigLoadResult dataclass."""

    def test_success_result(self):
        """Test successful config load result."""
        config = AppConfig(
            csv=CsvConfig(delimiter=','),
            enricher_pattern_sets=EnricherPatternSets(type={}, partner={})
        )
        result = ConfigLoadResult.success(config)
        assert result.config is not None
        assert result.validation_result.is_valid is True

    def test_failure_result(self):
        """Test failed config load result."""
        result = ConfigLoadResult.failure("Load failed", "TEST_ERROR")
        assert result.config is None
        assert result.validation_result.is_valid is False
        assert result.validation_result.error_code == "TEST_ERROR"


class TestConfigurationService:
    """Tests for ConfigurationService class."""

    def test_init(self):
        """Test ConfigurationService initialization."""
        service = ConfigurationService()
        # Service is successfully instantiated
        assert isinstance(service, ConfigurationService)

    def test_get_default_config(self):
        """Test getting default configuration."""
        service = ConfigurationService()
        config = service.get_default_config()
        assert isinstance(config, AppConfig)
        assert config.csv.delimiter == "\t"  # Default from CsvConfig

    def test_load_config_with_valid_file(self, tmp_path):
        """Test loading valid config file."""
        config_data = {
            "csv": {
                "dialect": "excel",
                "delimiter": ",",
                "date_attribute_format": "%Y-%m-%d",
                "attribute_mapping": {
                    "date": "date",
                    "amount": "sum"
                }
            },
            "enricher_pattern_sets": {
                "type": {"food": ["grocery", "restaurant"]},
                "partner": {}
            }
        }
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml.dump(config_data))

        service = ConfigurationService()
        result = service.load_config(str(config_file))

        assert result.config is not None
        assert result.validation_result.is_valid is True
        assert result.config.csv.delimiter == ","

    def test_load_config_with_none_returns_defaults(self):
        """Test loading config with None returns defaults."""
        service = ConfigurationService()
        result = service.load_config(None)

        assert result.config is not None
        assert result.validation_result.is_valid is True
        assert result.config.csv.delimiter == "\t"  # Default

    def test_resolve_config_path_with_user_path(self):
        """Test resolve returns user path when provided."""
        service = ConfigurationService()
        result = service.resolve_config_path("/path/to/config.yml", ml_enabled=False)
        assert result == "/path/to/config.yml"

    def test_resolve_config_path_with_ml_enabled(self):
        """Test resolve returns None when ML is enabled."""
        service = ConfigurationService()
        result = service.resolve_config_path("", ml_enabled=True)
        assert result is None

    def test_resolve_config_path_with_default(self, tmp_path):
        """Test resolve returns default path when it exists."""
        default_config = tmp_path / "default_config.yml"
        default_config.write_text("csv:\n  delimiter: ','")

        service = ConfigurationService()
        result = service.resolve_config_path(
            "",
            ml_enabled=False,
            default_config_path=str(default_config)
        )
        assert result == str(default_config)

    def test_resolve_config_path_no_default_returns_none(self):
        """Test resolve returns None when no default specified."""
        service = ConfigurationService()
        result = service.resolve_config_path("", ml_enabled=False)
        assert result is None

    def test_resolve_config_path_missing_default_raises_error(self):
        """Test resolve raises error when default not found."""
        service = ConfigurationService()
        try:
            service.resolve_config_path(
                "",
                ml_enabled=False,
                default_config_path="/nonexistent/config.yml"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Default config file not found" in str(e)

    def test_validate_config_path_success(self, tmp_path):
        """Test validation succeeds for existing file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: config")

        service = ConfigurationService()
        result = service.validate_config_path(str(config_file))

        assert result.is_valid is True

    def test_validate_config_path_empty(self):
        """Test validation fails for empty path."""
        service = ConfigurationService()
        result = service.validate_config_path("")

        assert result.is_valid is False
        assert result.error_code == "EMPTY_CONFIG_PATH"

    def test_validate_config_path_not_found(self):
        """Test validation fails for non-existent file."""
        service = ConfigurationService()
        result = service.validate_config_path("/nonexistent/config.yml")

        assert result.is_valid is False
        assert result.error_code == "CONFIG_FILE_NOT_FOUND"

    def test_validate_config_path_is_directory(self, tmp_path):
        """Test validation fails when path is a directory."""
        service = ConfigurationService()
        result = service.validate_config_path(str(tmp_path))

        assert result.is_valid is False
        assert result.error_code == "CONFIG_PATH_NOT_FILE"

"""Tests for CSV profile service.

This module tests the CsvProfileService which provides business logic
for managing CSV profiles.
"""
import pytest

from whatsthedamage.services.csv_profile_service import CsvProfileService
from whatsthedamage.config.csv_profiles import CsvProfile, AVAILABLE_CSV_PROFILES
from whatsthedamage.config.config import CsvConfig, AppConfig
from whatsthedamage.config.ml_config import MLConfig


@pytest.fixture
def csv_profile_service():
    """Create a fresh CsvProfileService instance for each test."""
    return CsvProfileService()


class TestCsvProfileServiceInitialization:
    """Tests for CsvProfileService initialization."""

    def test_service_initialization(self, csv_profile_service):
        """Test that service initializes with all available profiles."""
        profiles = csv_profile_service.get_all_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) == len(AVAILABLE_CSV_PROFILES)


class TestProfileRetrieval:
    """Tests for profile retrieval methods."""

    def test_get_profile_by_id(self, csv_profile_service):
        """Test retrieving a profile by ID."""
        profile = csv_profile_service.get_profile_by_id("kh-hu")
        assert profile is not None
        assert profile.id == "kh-hu"
        assert profile.name == "K&H Bank"

    def test_get_profile_by_id_nonexistent(self, csv_profile_service):
        """Test retrieving a non-existent profile."""
        profile = csv_profile_service.get_profile_by_id("nonexistent")
        assert profile is None

    def test_get_all_profiles(self, csv_profile_service):
        """Test retrieving all profiles."""
        profiles = csv_profile_service.get_all_profiles()
        assert len(profiles) > 0
        assert any(p.id == "kh-hu" for p in profiles)

    def test_get_default_profile(self, csv_profile_service):
        """Test retrieving the default profile."""
        profile = csv_profile_service.get_default_profile()
        assert profile is not None
        assert profile.id == "kh-hu"  # K&H is the default


class TestProfileValidation:
    """Tests for profile validation methods."""

    def test_validate_and_parse_profile_valid_yaml(self, csv_profile_service):
        """Test validating a valid YAML profile."""
        yaml_content = """
id: test-bank
name: Test Bank
version: "1.0"
csv_config:
  dialect: excel
  delimiter: ","
  date_attribute_format: "%Y-%m-%d"
  attribute_mapping:
    date: Date
    type: Type
    partner: Description
    amount: Amount
    currency: Currency
    account: Account
    notice: Memo
"""
        profile = csv_profile_service.validate_and_parse_profile(yaml_content)
        assert profile.id == "test-bank"
        assert profile.name == "Test Bank"
        assert profile.version == "1.0"
        assert profile.csv_config.dialect == "excel"

    def test_validate_and_parse_profile_empty_yaml(self, csv_profile_service):
        """Test validating empty YAML content."""
        with pytest.raises(ValueError, match="Empty YAML content"):
            csv_profile_service.validate_and_parse_profile("")

    def test_validate_and_parse_profile_invalid_yaml(self, csv_profile_service):
        """Test validating invalid YAML syntax."""
        with pytest.raises(ValueError, match="Invalid YAML syntax"):
            csv_profile_service.validate_and_parse_profile("invalid: yaml: content:")

    def test_validate_and_parse_profile_missing_required_field(self, csv_profile_service):
        """Test validating profile with missing required field."""
        yaml_content = """
name: Test Bank
csv_config:
  dialect: excel
  delimiter: ","
  date_attribute_format: "%Y-%m-%d"
  attribute_mapping:
    date: Date
    type: Type
    partner: Description
    amount: Amount
    currency: Currency
    account: Account
    notice: Memo
"""
        with pytest.raises(ValueError, match="Invalid CSV profile structure"):
            csv_profile_service.validate_and_parse_profile(yaml_content)


class TestConfigCreation:
    """Tests for AppConfig creation from profiles."""

    def test_create_config_from_profile_id(self, csv_profile_service):
        """Test creating AppConfig from a profile ID."""
        config = csv_profile_service.create_config_from_profile(profile_id="kh-hu")
        assert isinstance(config, AppConfig)
        # csv field removed from AppConfig - config no longer contains csv settings
        assert config.enabled_statistical_algorithms == ['iqr', 'pareto']
        assert config.cache_ttl == 1800
        assert isinstance(config.ml_config, MLConfig)

    def test_create_config_from_custom_profile(self, csv_profile_service):
        """Test creating AppConfig from a custom profile object."""
        csv_config = CsvConfig(
            dialect="excel-tab",
            delimiter="\t",
            date_attribute_format="%Y.%m.%d"
        )
        custom_profile = CsvProfile(
            id="custom",
            name="Custom",
            csv_config=csv_config
        )
        config = csv_profile_service.create_config_from_profile(custom_profile=custom_profile)
        # csv field removed from AppConfig - config no longer contains csv settings
        assert isinstance(config, AppConfig)

    def test_create_config_from_profile_nonexistent_id(self, csv_profile_service):
        """Test creating AppConfig from non-existent profile ID."""
        with pytest.raises(ValueError, match="CSV profile not found"):
            csv_profile_service.create_config_from_profile(profile_id="nonexistent")

    def test_create_config_from_profile_no_args(self, csv_profile_service):
        """Test creating AppConfig with no arguments (uses default)."""
        config = csv_profile_service.create_config_from_profile()
        assert isinstance(config, AppConfig)
        # csv field removed from AppConfig - config no longer contains csv settings


class TestProfileResolution:
    """Tests for profile resolution with priority."""

    def test_resolve_profile_default(self, csv_profile_service):
        """Test resolving to default profile."""
        profile = csv_profile_service.resolve_profile()
        assert profile.id == "kh-hu"

    def test_resolve_profile_by_id(self, csv_profile_service):
        """Test resolving by profile ID."""
        profile = csv_profile_service.resolve_profile(profile_id="kh-hu")
        assert profile.id == "kh-hu"

    def test_resolve_profile_by_id_nonexistent(self, csv_profile_service):
        """Test resolving by non-existent profile ID."""
        with pytest.raises(ValueError, match="CSV profile not found"):
            csv_profile_service.resolve_profile(profile_id="nonexistent")

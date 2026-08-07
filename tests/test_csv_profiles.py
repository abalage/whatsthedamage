"""Tests for CSV profile definitions.

This module tests the csv_profiles module which contains pre-defined
CSV profiles for various banks.
"""
import pytest
from whatsthedamage.config.csv_profiles import (
    CsvProfile,
    AVAILABLE_CSV_PROFILES,
    get_csv_profile_by_id,
    get_default_csv_profile,
    get_all_csv_profiles
)
from whatsthedamage.config.config import CsvConfig


class TestCsvProfile:
    """Tests for CsvProfile model."""

    def test_csv_profile_creation(self):
        """Test creating a CsvProfile with required fields."""
        csv_config = CsvConfig(
            dialect="excel",
            delimiter=",",
            date_attribute_format="%Y-%m-%d",
            attribute_mapping={
                "date": "Date",
                "type": "Type",
                "partner": "Description",
                "amount": "Amount",
                "currency": "Currency",
                "account": "Account",
                "notice": "Memo"
            }
        )
        profile = CsvProfile(
            id="test-bank",
            name="Test Bank",
            csv_config=csv_config
        )
        assert profile.id == "test-bank"
        assert profile.name == "Test Bank"
        assert profile.description == ""
        assert profile.version == "1.0"
        assert profile.is_default is False
        assert profile.csv_config.dialect == "excel"

    def test_csv_profile_with_optional_fields(self):
        """Test creating a CsvProfile with all optional fields."""
        csv_config = CsvConfig(
            dialect="excel-tab",
            delimiter="\t",
            date_attribute_format="%Y.%m.%d"
        )
        profile = CsvProfile(
            id="test-bank",
            name="Test Bank",
            description="A test bank profile",
            version="2.0",
            csv_config=csv_config,
            is_default=True
        )
        assert profile.description == "A test bank profile"
        assert profile.version == "2.0"
        assert profile.is_default is True


class TestProfileRetrieval:
    """Tests for profile retrieval functions."""

    def test_get_all_csv_profiles(self):
        """Test retrieving all available profiles."""
        profiles = get_all_csv_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        # All should be CsvProfile instances
        for profile in profiles:
            assert isinstance(profile, CsvProfile)

    def test_get_csv_profile_by_id_existing(self):
        """Test retrieving a profile by valid ID."""
        # Test with known profile IDs
        profile = get_csv_profile_by_id("otp-hu")
        assert profile is not None
        assert profile.id == "otp-hu"
        assert profile.name == "OTP Bank"

    def test_get_csv_profile_by_id_nonexistent(self):
        """Test retrieving a profile by non-existent ID."""
        profile = get_csv_profile_by_id("nonexistent-bank")
        assert profile is None

    def test_get_default_csv_profile(self):
        """Test retrieving the default profile."""
        profile = get_default_csv_profile()
        assert profile is not None
        assert isinstance(profile, CsvProfile)
        # The default profile is K&H Bank
        assert profile.id == "kh-hu"
        assert profile.is_default is True


class TestProfileList:
    """Tests for the AVAILABLE_CSV_PROFILES list."""

    def test_available_profiles_list(self):
        """Test that AVAILABLE_CSV_PROFILES contains expected profiles."""
        assert isinstance(AVAILABLE_CSV_PROFILES, list)
        assert len(AVAILABLE_CSV_PROFILES) >= 5  # We have 5 built-in profiles

    def test_profile_ids_are_unique(self):
        """Test that all profile IDs in AVAILABLE_CSV_PROFILES are unique."""
        ids = [p.id for p in AVAILABLE_CSV_PROFILES]
        assert len(ids) == len(set(ids)), "Duplicate profile IDs found"

    def test_expected_profiles_exist(self):
        """Test that expected bank profiles exist."""
        expected_ids = [
            "otp-hu",
            "kh-hu",
            "erste-hu",
            "unicredit-hu",
            "raiffeisen-hu"
        ]
        available_ids = [p.id for p in AVAILABLE_CSV_PROFILES]
        for expected_id in expected_ids:
            assert expected_id in available_ids, f"Profile {expected_id} not found"

    def test_profiles_have_required_csv_config_fields(self):
        """Test that all profiles have required CSV config fields."""
        required_mapping_keys = ["date", "type", "partner", "amount", "currency", "account", "notice"]
        for profile in AVAILABLE_CSV_PROFILES:
            assert profile.csv_config.dialect is not None
            assert profile.csv_config.delimiter is not None
            assert profile.csv_config.date_attribute_format is not None
            assert profile.csv_config.attribute_mapping is not None
            for key in required_mapping_keys:
                assert key in profile.csv_config.attribute_mapping, \
                    f"Profile {profile.id} missing required mapping key: {key}"


class TestProfileConfiguration:
    """Tests for profile CSV configuration values."""

    def test_otp_profile_configuration(self):
        """Test OTP Bank profile configuration."""
        profile = get_csv_profile_by_id("otp-hu")
        assert profile is not None
        assert profile.csv_config.dialect == "excel-tab"
        assert profile.csv_config.delimiter == "\t"
        assert profile.csv_config.date_attribute_format == "%Y.%m.%d"
        assert "könyvelés dátuma" in profile.csv_config.attribute_mapping.values()

    def test_kh_profile_configuration(self):
        """Test K&H Bank profile configuration."""
        profile = get_csv_profile_by_id("kh-hu")
        assert profile is not None
        assert profile.csv_config.dialect == "excel-tab"
        assert profile.csv_config.delimiter == "\t"
        assert profile.csv_config.date_attribute_format == "%Y.%m.%d"



"""Service for CSV profile management and resolution.

This service provides business logic for managing CSV profiles, including:
- Retrieving built-in profiles
- Validating and parsing custom profile YAML files
- Creating AppConfig from profiles
- Resolving profile selection based on priority rules

The service follows the established dependency injection pattern and
encapsulates all profile-related business logic.
"""
from typing import Optional, List
import yaml
from pydantic import ValidationError

from whatsthedamage.config.csv_profiles import (
    CsvProfile,
    get_csv_profile_by_id,
    get_default_csv_profile,
    get_all_csv_profiles as get_all_csv_profiles_from_config
)
from whatsthedamage.config.config import AppConfig, CsvConfig, EnricherPatternSets
from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


class CsvProfileService:
    """Service for CSV profile management and resolution.

    This service encapsulates all business logic related to CSV profiles,
    including profile retrieval, validation, and configuration creation.

    The service maintains a list of available profiles loaded from the
    csv_profiles module and provides methods to work with them.

    Attributes:
        _profiles: List of all available CSV profiles (cached).
    """

    def __init__(self) -> None:
        """Initialize the CSV profile service.

        Loads all available CSV profiles from the csv_profiles module.
        """
        self._profiles: List[CsvProfile] = list(get_all_csv_profiles_from_config())

    def get_profile_by_id(self, profile_id: str) -> Optional[CsvProfile]:
        """Get a CSV profile by its unique identifier.

        Args:
            profile_id: The unique identifier of the profile to retrieve.

        Returns:
            The CsvProfile object if found, None otherwise.
        """
        return get_csv_profile_by_id(profile_id)

    def get_all_profiles(self) -> List[CsvProfile]:
        """Get all available CSV profiles.

        Returns:
            List of all available CsvProfile objects.
        """
        return self._profiles

    def get_default_profile(self) -> CsvProfile:
        """Get the default CSV profile.

        Returns:
            The default CsvProfile object (the one with is_default=True),
            or the first profile in the list if none is marked as default.
        """
        return get_default_csv_profile()

    def validate_and_parse_profile(self, yaml_content: str) -> CsvProfile:
        """Validate and parse YAML string to CsvProfile.

        Parses a YAML string and validates it against the CsvProfile
        schema. This method is used for validating custom profile uploads.

        Args:
            yaml_content: YAML string containing profile definition.

        Returns:
            Validated CsvProfile object.

        Raises:
            ValueError: If YAML is invalid or profile structure is invalid.
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                raise ValueError("Empty YAML content")
            return CsvProfile(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid CSV profile structure: {e}")

    def validate_and_parse_profile_file(
        self, file_path: str
    ) -> CsvProfile:
        """Validate and parse YAML file to CsvProfile.

        Reads a YAML file from disk and validates it as a CSV profile.

        Args:
            file_path: Path to the YAML file containing profile definition.

        Returns:
            Validated CsvProfile object.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If YAML is invalid or profile structure is invalid.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.validate_and_parse_profile(content)
        except FileNotFoundError:
            logger.error(f"Profile file not found: {file_path}")
            raise

    def create_config_from_profile(
        self,
        profile_id: Optional[str] = None,
        custom_profile: Optional[CsvProfile] = None
    ) -> AppConfig:
        """Create AppConfig from profile with defaults for other settings.

        Creates a complete AppConfig object from a CSV profile, filling
        in default values for other configuration sections (enricher
        patterns, text cleaning, statistical algorithms, cache, ML config).

        Note: This now returns ONLY the AppConfig without csv settings.
        Use get_csv_config_from_profile() to get the CsvConfig separately.

        Args:
            profile_id: Optional profile ID to use. If provided, the
                corresponding built-in profile will be validated (but csv_config not used).
            custom_profile: Optional custom CsvProfile to use. If provided,
                it will be validated (but csv_config not used).

        Returns:
            AppConfig object with defaults for all sections (without csv).

        Raises:
            ValueError: If profile_id is provided but not found.
        """
        # Validate profile_id if provided
        if profile_id:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                raise ValueError(f"CSV profile not found: {profile_id}")
        # Validate custom_profile if provided
        elif custom_profile:
            # If custom_profile is provided, we just validate it exists
            if not isinstance(custom_profile, CsvProfile):
                raise ValueError("custom_profile must be a CsvProfile object")
        # If neither is provided, we'll use defaults (no validation needed)

        return AppConfig(
            enricher_pattern_sets=EnricherPatternSets(),
            text_cleaning={},
            enabled_statistical_algorithms=['iqr', 'pareto'],
            cache_ttl=1800,
            ml_config=MLConfig()
        )

    def get_csv_config_from_profile(
        self,
        profile_id: Optional[str] = None,
        custom_profile: Optional[CsvProfile] = None
    ) -> CsvConfig:
        """Get CsvConfig from a profile.

        Args:
            profile_id: Optional profile ID to use. If provided, the
                corresponding built-in profile's csv_config will be used.
            custom_profile: Optional custom CsvProfile to use. If provided,
                its csv_config will be used directly.

        Returns:
            CsvConfig object from the profile.

        Raises:
            ValueError: If profile_id is provided but not found.
        """
        if custom_profile:
            return custom_profile.csv_config
        elif profile_id:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                raise ValueError(f"CSV profile not found: {profile_id}")
            return profile.csv_config
        else:
            profile = self.get_default_profile()
            return profile.csv_config

    def resolve_profile(
        self,
        profile_id: Optional[str] = None
    ) -> CsvProfile:
        """Resolve profile based on priority: profile ID > default.

        This method implements the configuration priority system for CSV
        profiles:
        1. Built-in profile ID
        2. Default profile (lowest priority)

        Args:
            profile_id: Optional built-in profile ID to use.

        Returns:
            Resolved CsvProfile object.

        Raises:
            ValueError: If profile_id is provided but not found.
        """
        if profile_id:
            profile = self.get_profile_by_id(profile_id)
            if not profile:
                raise ValueError(f"CSV profile not found: {profile_id}")
            return profile
        else:
            return self.get_default_profile()

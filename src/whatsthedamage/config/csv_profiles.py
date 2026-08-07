"""CSV profile definitions for bank transaction processing.

This module defines pre-configured CSV profiles for various banks,
allowing non-technical users to easily configure CSV parsing without
understanding the full YAML structure.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from whatsthedamage.config.config import CsvConfig


class CsvProfile(BaseModel):
    """CSV profile with metadata and version.

    A CSV profile encapsulates all the configuration needed to parse
    bank transaction CSV files from a specific bank. Each profile
    contains a complete CsvConfig along with metadata like name,
    description, and version.

    Attributes:
        id: Unique identifier (e.g., 'otp-hu', 'kh-hu'). Must be lowercase
            letters, numbers, and hyphens only.
        name: Display name for the profile (e.g., 'OTP Bank', 'K&H Bank').
        description: Optional description of the profile.
        version: Profile version string (default: '1.0').
        csv_config: The CsvConfig object containing parsing configuration.
        is_default: Whether this profile should be used as the default.
    """
    id: str = Field(..., description="Unique identifier (e.g., 'otp-hu')")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Optional description")
    version: str = Field(default="1.0", description="Profile version")
    csv_config: CsvConfig = Field(..., description="CSV parsing config")
    is_default: bool = Field(default=False, description="Is default profile")


# Pre-defined CSV profiles for various Hungarian and generic banks
AVAILABLE_CSV_PROFILES: List[CsvProfile] = [
    CsvProfile(
        id="kh-hu",
        name="K&H Bank",
        description="K&H Bank Hungary (tab-delimited)",
        version="1.0",
        csv_config=CsvConfig(
            dialect="excel-tab",
            delimiter="\t",
            date_attribute_format="%Y.%m.%d",
            attribute_mapping={
                "date": "könyvelés dátuma",
                "type": "típus",
                "partner": "partner elnevezése",
                "amount": "összeg",
                "currency": "összeg devizaneme",
                "account": "könyvelési számla",
                "notice": "közlemény"
            }
        ),
        is_default=True
    ),
]


def get_csv_profile_by_id(profile_id: str) -> Optional[CsvProfile]:
    """Get a CSV profile by its ID.

    Args:
        profile_id: The unique identifier of the profile to retrieve.

    Returns:
        The CsvProfile object if found, None otherwise.
    """
    for profile in AVAILABLE_CSV_PROFILES:
        if profile.id == profile_id:
            return profile
    return None


def get_default_csv_profile() -> CsvProfile:
    """Get the default CSV profile.

    Returns:
        The default CsvProfile object (the one with is_default=True),
        or the first profile in the list if none is marked as default.
    """
    for profile in AVAILABLE_CSV_PROFILES:
        if profile.is_default:
            return profile
    return AVAILABLE_CSV_PROFILES[0]


def get_all_csv_profiles() -> List[CsvProfile]:
    """Get all available CSV profiles.

    Returns:
        List of all available CsvProfile objects.
    """
    return AVAILABLE_CSV_PROFILES

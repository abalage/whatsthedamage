"""Tests for Correction database model.

Tests the Correction SQLAlchemy model creation and case-insensitive lookup.
"""

import pytest
from datetime import datetime, UTC

# Import all models to ensure they're registered with SQLAlchemy metadata
from whatsthedamage.models.database.user import User  # noqa: F401
from whatsthedamage.models.database.session import Session  # noqa: F401
from whatsthedamage.models.database.transaction import Transaction  # noqa: F401
from whatsthedamage.models.database.processing_result import ProcessingResult  # noqa: F401
from whatsthedamage.models.database.correction import Correction
from whatsthedamage.models.database.shared_correction import SharedCorrection  # noqa: F401


class TestCorrectionModel:
    """Tests for Correction model."""

    def test_correction_creation(self):
        """Test creating a Correction object."""
        correction = Correction(
            user_id=1,
            original_partner="test merchant",
            corrected_partner="CORRECTED MERCHANT",
            corrected_category_id="grocery"
        )

        assert correction.user_id == 1
        assert correction.original_partner == "test merchant"
        assert correction.corrected_partner == "CORRECTED MERCHANT"
        assert correction.corrected_category_id == "grocery"
        # Note: created_at and updated_at are set by SQLAlchemy defaults
        # They are set when the object is committed to the database, not on creation

    def test_correction_repr(self):
        """Test Correction string representation."""
        correction = Correction(
            user_id=1,
            original_partner="test merchant",
            corrected_partner="CORRECTED MERCHANT"
        )

        repr_str = repr(correction)
        assert "Correction" in repr_str
        assert "id=None" in repr_str or "id=" in repr_str
        assert "user_id=1" in repr_str
        assert "test merchant" in repr_str

    def test_correction_table_name(self):
        """Test that Correction has correct table name."""
        assert Correction.__tablename__ == 'corrections'

    def test_correction_with_nullable_fields(self):
        """Test Correction with nullable fields."""
        correction = Correction(
            user_id=1,
            original_partner="test merchant",
            corrected_partner=None,
            corrected_category_id=None
        )

        assert correction.corrected_partner is None
        assert correction.corrected_category_id is None

    def test_case_insensitive_storage(self):
        """Test that original_partner can be stored with mixed case.

        Note: The model stores the value as provided; case-insensitive
        matching is handled at query time by lowercasing both sides.
        """
        # Create with mixed case - the model accepts it as-is
        correction = Correction(
            user_id=1,
            original_partner="Test Merchant"
        )

        # The model stores it as provided (mixed case)
        assert correction.original_partner == "Test Merchant"

    def test_multiple_corrections_different_original_partners(self):
        """Test creating multiple corrections with different original_partners."""
        correction_1 = Correction(
            user_id=1,
            original_partner="merchant_1"
        )

        correction_2 = Correction(
            user_id=1,
            original_partner="merchant_2"
        )

        assert correction_1.original_partner == "merchant_1"
        assert correction_2.original_partner == "merchant_2"
        assert correction_1.original_partner != correction_2.original_partner

    def test_correction_all_fields(self):
        """Test Correction with all fields populated."""
        correction = Correction(
            user_id=1,
            original_partner="test merchant",
            corrected_partner="Corrected Partner",
            corrected_category_id="category_123"
        )

        assert correction.user_id == 1
        assert correction.original_partner == "test merchant"
        assert correction.corrected_partner == "Corrected Partner"
        assert correction.corrected_category_id == "category_123"

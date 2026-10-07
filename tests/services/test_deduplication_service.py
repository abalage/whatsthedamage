"""Tests for DeduplicationService.

Tests hash generation and duplicate detection functionality.
"""

import pytest

from whatsthedamage.services.deduplication_service import DeduplicationService
from tests.utils.transaction_test_factory import TransactionTestFactory


class TestDeduplicationService:
    """Tests for DeduplicationService."""

    @pytest.fixture
    def service(self):
        """Create a DeduplicationService instance."""
        return DeduplicationService()

    def test_generate_dedup_hash(self, service):
        """Test generating a deduplication hash from individual fields."""
        hash_result = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_result is not None
        assert len(hash_result) == 64  # SHA-256 produces 64 hex characters

    def test_generate_dedup_hash_from_row(self, service):
        """Test generating a deduplication hash from a CsvRow object."""
        csv_row = TransactionTestFactory.create_csv_row()
        hash_result = service.generate_dedup_hash_from_row(csv_row)

        assert hash_result is not None
        assert len(hash_result) == 64

    def test_same_data_produces_same_hash(self, service):
        """Test that same input data produces same hash."""
        hash_1 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        hash_2 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_1 == hash_2

    def test_different_data_produces_different_hash(self, service):
        """Test that different input data produces different hashes."""
        hash_1 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="MERCHANT_1",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        hash_2 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="MERCHANT_2",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_1 != hash_2

    def test_hash_changes_with_amount(self, service):
        """Test that hash changes when amount changes."""
        hash_1 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        hash_2 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-200.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_1 != hash_2

    def test_hash_changes_with_date(self, service):
        """Test that hash changes when date changes."""
        hash_1 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        hash_2 = service.generate_dedup_hash(
            date="2024-01-16",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_1 != hash_2

    def test_hash_changes_with_type(self, service):
        """Test that hash changes when transaction_type changes."""
        hash_1 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        hash_2 = service.generate_dedup_hash(
            date="2024-01-15",
            transaction_type="credit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001"
        )

        assert hash_1 != hash_2

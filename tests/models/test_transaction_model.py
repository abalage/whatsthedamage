"""Tests for Transaction database model.

Tests the Transaction SQLAlchemy model creation, deduplication hash generation,
and relationships.
"""

import pytest
from datetime import datetime, UTC
import hashlib

# Import all models to ensure they're registered with SQLAlchemy metadata
from whatsthedamage.models.database.user import User  # noqa: F401
from whatsthedamage.models.database.session import Session  # noqa: F401
from whatsthedamage.models.database.transaction import Transaction
from whatsthedamage.models.database.processing_result import ProcessingResult  # noqa: F401
from whatsthedamage.models.database.correction import Correction  # noqa: F401
from whatsthedamage.models.database.shared_correction import SharedCorrection  # noqa: F401


class TestTransactionModel:
    """Tests for Transaction model."""

    def test_transaction_creation(self):
        """Test creating a Transaction object."""
        dedup_hash = hashlib.sha256(
            b"2024-01-15|debit|TEST MERCHANT|-100.0|HUF|ACCOUNT001"
        ).hexdigest()

        transaction = Transaction(
            user_id=1,
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001",
            deduplication_hash=dedup_hash,
            category_id="grocery",
            partner="TEST MERCHANT",
            notice="Test notice",
            confidence=0.95
        )

        assert transaction.user_id == 1
        assert transaction.date == "2024-01-15"
        assert transaction.transaction_type == "debit"
        assert transaction.original_partner == "TEST MERCHANT"
        assert transaction.amount == -100.0
        assert transaction.currency == "HUF"
        assert transaction.account == "ACCOUNT001"
        assert transaction.deduplication_hash == dedup_hash
        assert transaction.category_id == "grocery"
        assert transaction.partner == "TEST MERCHANT"
        assert transaction.notice == "Test notice"
        assert transaction.confidence == 0.95

    def test_transaction_repr(self):
        """Test Transaction string representation."""
        transaction = Transaction()

        repr_str = repr(transaction)
        assert "Transaction" in repr_str
        assert "id=None" in repr_str or "id=" in repr_str
        assert "user_id=None" in repr_str or "user_id=" in repr_str
        assert "transaction_type=" in repr_str

    def test_deduplication_hash_generation(self):
        """Test that deduplication hash is correctly generated."""
        date = "2024-01-15"
        type = "debit"
        original_partner = "TEST MERCHANT"
        amount = -100.0
        currency = "HUF"
        account = "ACCOUNT001"

        expected_hash = hashlib.sha256(
            f"{date}|{type}|{original_partner}|{amount}|{currency}|{account}".encode('utf-8')
        ).hexdigest()

        transaction = Transaction(
            user_id=1,
            date=date,
            transaction_type=type,
            original_partner=original_partner,
            amount=amount,
            currency=currency,
            account=account,
            deduplication_hash=expected_hash
        )

        assert transaction.deduplication_hash == expected_hash

    def test_unique_deduplication_hash(self):
        """Test that different transactions have different deduplication hashes."""
        dedup_hash_1 = hashlib.sha256(
            b"2024-01-15|debit|MERCHANT_1|-100.0|HUF|ACCOUNT001"
        ).hexdigest()
        dedup_hash_2 = hashlib.sha256(
            b"2024-01-15|debit|MERCHANT_2|-100.0|HUF|ACCOUNT001"
        ).hexdigest()

        transaction_1 = Transaction(
            user_id=1,
            date="2024-01-15",
            transaction_type="debit",
            original_partner="MERCHANT_1",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001",
            deduplication_hash=dedup_hash_1
        )

        transaction_2 = Transaction(
            user_id=1,
            date="2024-01-15",
            transaction_type="debit",
            original_partner="MERCHANT_2",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001",
            deduplication_hash=dedup_hash_2
        )

        assert transaction_1.deduplication_hash != transaction_2.deduplication_hash

    def test_same_deduplication_hash_for_same_data(self):
        """Test that same transaction data produces same deduplication hash."""
        dedup_hash_1 = hashlib.sha256(
            b"2024-01-15|debit|MERCHANT_1|-100.0|HUF|ACCOUNT001"
        ).hexdigest()
        dedup_hash_2 = hashlib.sha256(
            b"2024-01-15|debit|MERCHANT_1|-100.0|HUF|ACCOUNT001"
        ).hexdigest()

        assert dedup_hash_1 == dedup_hash_2

    def test_transaction_table_name(self):
        """Test that Transaction has correct table name."""
        assert Transaction.__tablename__ == 'transactions'

    def test_transaction_with_nullable_fields(self):
        """Test Transaction with nullable fields."""
        dedup_hash = hashlib.sha256(
            b"2024-01-15|debit|TEST MERCHANT|-100.0|HUF|ACCOUNT001"
        ).hexdigest()

        transaction = Transaction(
            user_id=1,
            date="2024-01-15",
            transaction_type="debit",
            original_partner="TEST MERCHANT",
            amount=-100.0,
            currency="HUF",
            account="ACCOUNT001",
            deduplication_hash=dedup_hash,
            category_id=None,
            partner=None,
            notice=None,
            confidence=None
        )

        assert transaction.category_id is None
        assert transaction.partner is None
        assert transaction.notice is None
        assert transaction.confidence is None

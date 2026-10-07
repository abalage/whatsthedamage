"""Deduplication service.

Service for generating and validating transaction deduplication keys.
Ensures that each transaction is stored only once per user.
"""

import hashlib
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from whatsthedamage.models.repositories.transaction_repository import TransactionRepository
    from whatsthedamage.models.database.transaction import Transaction


class DeduplicationService:
    """Service for generating and validating transaction deduplication keys.

    The deduplication key is based on the immutable transaction fields:
    date + type + original_partner + amount + currency + account

    This service generates SHA-256 hashes of these keys for fast lookup
    and prevention of duplicate transactions.

    Attributes:
        No attributes - stateless service.
    """

    def generate_dedup_hash(
        self,
        date: str | datetime,
        transaction_type: str,
        original_partner: str,
        amount: float,
        currency: str,
        account: str
    ) -> str:
        """Generate SHA-256 hash of deduplication key.

        Creates a deterministic hash from the immutable transaction fields.
        The key format is: "date|transaction_type|original_partner|amount|currency|account"

        Args:
            date: Transaction date string or datetime object.
            transaction_type: Transaction type (debit/credit).
            original_partner: Original partner name from CSV.
            amount: Transaction amount.
            currency: Currency code.
            account: Account identifier.

        Returns:
            SHA-256 hash as hexadecimal string (64 characters).
        """
        # Convert datetime to epoch timestamp string for consistency with existing hashes
        # This ensures deduplication works for both old (string epoch) and new (datetime) transactions
        if isinstance(date, datetime):
            date_str = str(int(date.timestamp()))
        else:
            date_str = str(date)

        # Create the deduplication key string
        # Use string representation of amount to avoid floating point precision issues
        key = f"{date_str}|{transaction_type}|{original_partner}|{amount}|{currency}|{account}"

        # Generate SHA-256 hash
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def check_duplicate(
        self,
        user_id: int,
        dedup_hash: str,
        transaction_repo: 'TransactionRepository'
    ) -> bool:
        """Check if a transaction with this dedup hash already exists for user.

        Performs user-specific deduplication check. The deduplication key
        (date + type + original_partner + amount + currency + account) is unique
        per user, allowing different users to upload the same transaction.

        Args:
            user_id: User identifier for user-specific deduplication.
            dedup_hash: SHA-256 deduplication hash to check.
            transaction_repo: Transaction repository for database access.

        Returns:
            True if a transaction with this hash already exists for the user,
            False otherwise.
        """
        existing = transaction_repo.find_by_user_and_dedup_hash(user_id, dedup_hash)
        return existing is not None

    def generate_dedup_hash_from_row(self, csv_row: Any) -> str:
        """Generate deduplication hash from a CsvRow object.

        Convenience method that extracts fields from a CsvRow.

        Args:
            csv_row: CsvRow object with transaction data.

        Returns:
            SHA-256 hash as hexadecimal string.
        """
        return self.generate_dedup_hash(
            date=csv_row.date,
            transaction_type=csv_row.type,
            original_partner=csv_row.partner,
            amount=csv_row.amount,
            currency=csv_row.currency,
            account=csv_row.account
        )

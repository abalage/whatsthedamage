"""Test factory for creating test Transaction and CsvRow objects.

Provides helper functions for creating test data for transaction persistence tests.
"""

# Import all models to ensure they're registered with SQLAlchemy metadata
from whatsthedamage.models.database.user import User  # noqa: F401
from whatsthedamage.models.database.session import Session  # noqa: F401
from whatsthedamage.models.database.transaction import Transaction
from whatsthedamage.models.database.processing_result import ProcessingResult  # noqa: F401
from whatsthedamage.models.database.correction import Correction
from whatsthedamage.models.database.shared_correction import SharedCorrection
from whatsthedamage.models.domain.csv_row import CsvRow
from datetime import datetime, UTC
import hashlib


class TransactionTestFactory:
    """Factory for creating test Transaction objects."""

    @staticmethod
    def create_csv_row(
        date: str = "2024-01-15",
        transaction_type: str = "debit",
        partner: str = "TEST MERCHANT",
        amount: float = -100.0,
        currency: str = "HUF",
        category_id: str = "grocery",
        account: str = "ACCOUNT001",
        notice: str = "Test transaction",
        confidence: float | None = None
    ) -> CsvRow:
        """Create a test CsvRow object.

        Args:
            date: Transaction date.
            type: Transaction type.
            partner: Partner/merchant name.
            amount: Transaction amount.
            currency: Currency code.
            category_id: Category identifier.
            account: Account identifier.
            notice: Transaction notice.
            confidence: ML confidence score.

        Returns:
            CsvRow object with test data.
        """
        # Create a dict that CsvRow expects
        row_dict = {
            'date': date,
            'type': transaction_type,
            'partner': partner,
            'amount': str(amount),
            'currency': currency,
            'category_id': category_id,
            'account': account,
            'notice': notice
        }
        mapping = {
            'date': 'date',
            'type': 'type',
            'partner': 'partner',
            'amount': 'amount',
            'currency': 'currency',
            'category_id': 'category_id',
            'account': 'account',
            'notice': 'notice'
        }
        csv_row = CsvRow(row_dict, mapping)
        csv_row.confidence = confidence
        return csv_row

    @staticmethod
    def generate_dedup_hash(
        date: str = "2024-01-15",
        transaction_type: str = "debit",
        original_partner: str = "TEST MERCHANT",
        amount: float = -100.0,
        currency: str = "HUF",
        account: str = "ACCOUNT001"
    ) -> str:
        """Generate a deduplication hash for test data.

        Args:
            date: Transaction date.
            transaction_type: Transaction type.
            original_partner: Original partner name.
            amount: Transaction amount.
            currency: Currency code.
            account: Account identifier.

        Returns:
            SHA-256 hash string.
        """
        key = f"{date}|{transaction_type}|{original_partner}|{amount}|{currency}|{account}"
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    @staticmethod
    def create_transaction(
        user_id: int = 1,
        date: str = "2024-01-15",
        transaction_type: str = "debit",
        original_partner: str = "TEST MERCHANT",
        amount: float = -100.0,
        currency: str = "HUF",
        account: str = "ACCOUNT001",
        category_id: str = "grocery",
        partner: str | None = None,
        notice: str | None = None,
        confidence: float | None = None
    ) -> Transaction:
        """Create a test Transaction object.

        Args:
            user_id: User identifier.
            date: Transaction date.
            transaction_type: Transaction type.
            original_partner: Original partner name.
            amount: Transaction amount.
            currency: Currency code.
            account: Account identifier.
            category_id: Category identifier.
            partner: Corrected partner name.
            notice: Transaction notice.
            confidence: ML confidence score.

        Returns:
            Transaction object with test data.
        """
        dedup_hash = TransactionTestFactory.generate_dedup_hash(
            date, transaction_type, original_partner, amount, currency, account
        )
        return Transaction(
            user_id=user_id,
            date=date,
            transaction_type=transaction_type,
            original_partner=original_partner,
            amount=amount,
            currency=currency,
            account=account,
            deduplication_hash=dedup_hash,
            category_id=category_id,
            partner=partner or original_partner,
            notice=notice,
            confidence=confidence,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

    @staticmethod
    def create_correction(
        user_id: int = 1,
        original_partner: str = "test merchant",
        corrected_partner: str | None = "CORRECTED MERCHANT",
        corrected_category_id: str | None = "grocery",
        corrected_notice: str | None = "Corrected notice"
    ) -> Correction:
        """Create a test Correction object.

        Args:
            user_id: User identifier.
            original_partner: Original partner name (will be stored in lowercase).
            corrected_partner: Corrected partner name.
            corrected_category_id: Corrected category identifier.
            corrected_notice: Corrected notice.

        Returns:
            Correction object with test data.
        """
        return Correction(
            user_id=user_id,
            original_partner=original_partner.lower(),
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id,
            corrected_notice=corrected_notice,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

    @staticmethod
    def create_shared_correction(
        original_partner: str = "test merchant",
        corrected_category_id: str = "grocery",
        corrected_partner: str | None = "CORRECTED MERCHANT",
        corrected_notice: str | None = "Shared notice"
    ) -> SharedCorrection:
        """Create a test SharedCorrection object.

        Args:
            original_partner: Original partner name (will be hashed).
            corrected_category_id: Corrected category identifier.
            corrected_partner: Corrected partner name.
            corrected_notice: Corrected notice.

        Returns:
            SharedCorrection object with test data.
        """
        import hashlib
        partner_hash = hashlib.sha256(
            original_partner.lower().encode('utf-8')
        ).hexdigest()
        return SharedCorrection(
            original_partner_hash=partner_hash,
            corrected_partner=corrected_partner,
            corrected_category_id=corrected_category_id,
            corrected_notice=corrected_notice,
            contributed_at=datetime.now(UTC),
            contribution_count=1
        )

    @staticmethod
    def create_csv_rows(count: int = 5) -> list[CsvRow]:
        """Create multiple test CsvRow objects.

        Args:
            count: Number of rows to create.

        Returns:
            List of CsvRow objects.
        """
        rows = []
        for i in range(count):
            row = TransactionTestFactory.create_csv_row(
                date=f"2024-01-{15 + i}",
                transaction_type="debit" if i % 2 == 0 else "credit",
                partner=f"MERCHANT_{i}",
                amount=-100.0 * (i + 1),
                category_id=f"category_{i}"
            )
            rows.append(row)
        return rows
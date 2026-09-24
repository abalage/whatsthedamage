"""Transaction persistence service.

Service for persisting transactions to the database with deduplication support.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from whatsthedamage.models.repositories.transaction_repository import TransactionRepository
    from whatsthedamage.models.repositories.correction_repository import CorrectionRepository
    from whatsthedamage.models.database.transaction import Transaction
    from whatsthedamage.models.domain.csv_row import CsvRow
    from whatsthedamage.services.deduplication_service import DeduplicationService


class TransactionPersistenceService:
    """Service for persisting transactions to database.

    Orchestrates the saving of transactions from CSV processing results
    to the database, with deduplication and correction support.

    Attributes:
        transaction_repo: Repository for transaction database operations.
        correction_repo: Repository for correction database operations.
    """

    def __init__(
        self,
        transaction_repo: 'TransactionRepository',
        correction_repo: 'CorrectionRepository'
    ) -> None:
        """Initialize the transaction persistence service.

        Args:
            transaction_repo: Repository for transaction database operations.
            correction_repo: Repository for correction database operations.
        """
        self.transaction_repo = transaction_repo
        self.correction_repo = correction_repo

    def save_transaction(
        self,
        user_id: int,
        csv_row: 'CsvRow',
        dedup_service: 'DeduplicationService',
        corrected_partner: Optional[str] = None,
        corrected_category_id: Optional[str] = None,
        corrected_notice: Optional[str] = None
    ) -> tuple['Transaction', bool]:
        """Save a transaction for a user.

        Checks for duplicates using the deduplication service. If a duplicate
        is found, returns the existing transaction. Otherwise, creates a new
        transaction with the provided corrections applied.

        Args:
            user_id: Authenticated user ID.
            csv_row: Processed CSV row with transaction data.
            dedup_service: Deduplication service for hash generation.
            corrected_partner: User correction for partner name (optional).
            corrected_category_id: User correction for category (optional).
            corrected_notice: User correction for notice (optional).

        Returns:
            Tuple of (saved Transaction, is_new)
            is_new is False if transaction already existed (duplicate)
        """
        from whatsthedamage.models.database.transaction import Transaction
        from whatsthedamage.utils.date_converter import DateConverter

        # Generate deduplication hash
        dedup_hash = dedup_service.generate_dedup_hash_from_row(csv_row)

        # Check for duplicate
        existing = self.transaction_repo.find_by_dedup_hash(dedup_hash)
        if existing:
            return existing, False

        # Create new transaction with corrections applied
        transaction = Transaction(
            user_id=user_id,
            date=DateConverter.parse_to_datetime_utc(csv_row.date),
            transaction_type=csv_row.type,
            original_partner=csv_row.partner,
            amount=csv_row.amount,
            currency=csv_row.currency,
            account=csv_row.account,
            deduplication_hash=dedup_hash,
            category_id=corrected_category_id or csv_row.category_id,
            partner=corrected_partner or csv_row.partner,
            notice=corrected_notice or csv_row.notice,
            confidence=csv_row.confidence
        )

        saved = self.transaction_repo.create(transaction)
        return saved, True

    def save_transactions_from_csv(
        self,
        user_id: int,
        csv_rows: list['CsvRow'],
        dedup_service: 'DeduplicationService',
        correction_repo: Optional['CorrectionRepository'] = None
    ) -> tuple[list['Transaction'], int]:
        """Save multiple transactions from CSV processing.

        Applies user corrections from the correction repository (if provided)
        and handles deduplication for each transaction.

        Args:
            user_id: Authenticated user ID.
            csv_rows: List of processed CSV rows.
            dedup_service: Deduplication service for hash generation.
            correction_repo: Optional correction repository for applying user corrections.

        Returns:
            Tuple of (list of saved transactions, count of new transactions)
        """
        from whatsthedamage.models.database.transaction import Transaction

        new_count = 0
        saved_transactions: list[Transaction] = []

        # Use provided correction_repo or fall back to instance variable
        repo = correction_repo or self.correction_repo

        for csv_row in csv_rows:
            # Apply corrections if repository is available
            corrected_partner = None
            corrected_category_id = None
            corrected_notice = None

            if repo:
                correction = repo.find_by_user_and_original_partner(
                    user_id, csv_row.partner
                )
                if correction:
                    corrected_partner = (
                        str(correction.corrected_partner) if correction.corrected_partner else None
                    )
                    corrected_category_id = (
                        str(correction.corrected_category_id) if correction.corrected_category_id else None
                    )
                    corrected_notice = (
                        str(correction.corrected_notice) if correction.corrected_notice else None
                    )

            transaction, is_new = self.save_transaction(
                user_id,
                csv_row,
                dedup_service,
                corrected_partner,
                corrected_category_id,
                corrected_notice
            )
            saved_transactions.append(transaction)
            if is_new:
                new_count += 1

        return saved_transactions, new_count

    def get_transactions_for_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> tuple[list['Transaction'], int]:
        """Get transactions for a user with optional date filtering.

        Args:
            user_id: User identifier.
            limit: Maximum number of transactions to return.
            offset: Pagination offset.
            start_date: Start date filter (inclusive, YYYY-MM-DD format).
            end_date: End date filter (inclusive, YYYY-MM-DD format).

        Returns:
            Tuple of (list of transactions, total count).
        """
        if start_date or end_date:
            transactions = self.transaction_repo.find_by_user_and_date_range(
                user_id, start_date, end_date, limit, offset
            )
        else:
            transactions = self.transaction_repo.find_by_user_id(
                user_id, limit, offset
            )

        total_count = self.transaction_repo.get_count_by_user(user_id)
        return transactions, total_count

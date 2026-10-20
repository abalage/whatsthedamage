"""Transaction repository.

Provides data access for Transaction entities using SQLAlchemy ORM.
Implements the repository pattern for transaction persistence and retrieval.
"""

from datetime import datetime, UTC
from typing import Any, Optional, cast
from sqlalchemy import or_, func, extract
from sqlalchemy.orm import Query, Session as SqlAlchemySession

from whatsthedamage.utils.date_converter import DateConverter

from whatsthedamage.models.database.transaction import Transaction as TransactionDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


class SqlAlchemyTransactionRepository(SqlAlchemyBaseRepository[TransactionDB]):
    """SQLAlchemy implementation of the SqlAlchemyTransactionRepository contract.

    Provides concrete data access operations for Transaction entities
    using SQLAlchemy ORM.
    """

    def create(self, transaction: TransactionDB) -> TransactionDB:
        """Create a new transaction in the database.

        Args:
            transaction: Transaction entity to create.

        Returns:
            The created Transaction entity.

        Raises:
            ValueError: If a transaction with the same deduplication hash already exists.
        """
        with self._write() as session:
            # Check if deduplication hash already exists for this user
            existing = session.query(TransactionDB).filter(
                TransactionDB.user_id == transaction.user_id,
                TransactionDB.deduplication_hash == transaction.deduplication_hash
            ).first()
            if existing:
                raise ValueError(
                    f"Transaction with deduplication hash "
                    f"'{transaction.deduplication_hash}' already exists for this user"
                )

            session.add(transaction)
            return transaction

    def add_all(self, transactions: list[TransactionDB]) -> list[TransactionDB]:
        """Add transactions to the session without committing.

        Intended for use inside a unit of work, which owns the session
        and controls commit and rollback so multi-entity writes stay
        atomic. The session is not closed here.

        Args:
            transactions: Transaction entities to add.

        Returns:
            The added Transaction entities.
        """
        session = self._get_session()
        session.add_all(transactions)
        return transactions

    def find_existing_dedup_hashes(
        self, user_id: int, dedup_hashes: list[str]
    ) -> set[str]:
        """Find which deduplication hashes already exist for a user.

        Replaces one lookup per transaction with a single batched query
        (chunked to respect SQLite's variable limit). Matches the
        per-user scope of find_by_user_and_dedup_hash. The session is
        not closed so the method can run inside a unit of work.

        Args:
            user_id: User identifier scoping the lookup.
            dedup_hashes: SHA-256 deduplication hashes to check.

        Returns:
            The subset of hashes that already exist.
        """
        existing: set[str] = set()
        unique_hashes = list(set(dedup_hashes))
        if not unique_hashes:
            return existing

        session = self._get_session()
        chunk_size = 500
        for start in range(0, len(unique_hashes), chunk_size):
            chunk = unique_hashes[start:start + chunk_size]
            rows = session.query(TransactionDB.deduplication_hash).filter(
                TransactionDB.user_id == user_id,
                TransactionDB.deduplication_hash.in_(chunk)
            ).all()
            existing.update(cast(str, row[0]) for row in rows)
        return existing

    def find_by_id(self, transaction_id: int) -> Optional[TransactionDB]:
        """Find transaction by ID.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Transaction entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.id == transaction_id
            ).first()

    def find_by_user_and_id(
        self,
        user_id: int,
        transaction_id: int
    ) -> Optional[TransactionDB]:
        """Find a transaction by ID, scoped to the owning user.

        Args:
            user_id: User identifier scoping the lookup.
            transaction_id: Transaction identifier.

        Returns:
            Transaction entity if found and owned by the user,
            None otherwise.
        """
        with self._read() as session:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id,
                TransactionDB.id == transaction_id
            ).first()


    def find_by_user_and_dedup_hash(
        self,
        user_id: int,
        dedup_hash: str
    ) -> Optional[TransactionDB]:
        """Find transaction by user ID and deduplication hash.

        Args:
            user_id: User identifier.
            dedup_hash: SHA-256 deduplication hash.

        Returns:
            Transaction entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id,
                TransactionDB.deduplication_hash == dedup_hash
            ).first()

    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[TransactionDB]:
        """Find transactions by user ID with pagination.

        Args:
            user_id: User identifier.
            limit: Maximum number of transactions to return (default 100).
            offset: Pagination offset (default 0).

        Returns:
            List of Transaction entities for the user.
        """
        with self._read() as session:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id
            ).order_by(TransactionDB.created_at.desc()).offset(offset).limit(limit).all()

    def find_by_user_and_date_range(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[TransactionDB]:
        """Find transactions by user and date range.

        Args:
            user_id: User identifier.
            start_date: Start date filter (inclusive, YYYY-MM-DD format).
            end_date: End date filter (inclusive, YYYY-MM-DD format).
            limit: Maximum number of transactions to return (default 100).
            offset: Pagination offset (default 0).

        Returns:
            List of Transaction entities matching criteria.
        """
        with self._read() as session:
            query = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            )

            if start_date:
                try:
                    start_dt = DateConverter.parse_to_datetime_utc(start_date)
                    query = query.filter(TransactionDB.date >= start_dt)
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = DateConverter.parse_to_datetime_utc(end_date)
                    query = query.filter(TransactionDB.date <= end_dt)
                except ValueError:
                    pass

            return query.order_by(  # type: ignore[no-any-return]
                TransactionDB.date.desc()
            ).offset(offset).limit(limit).all()

    def update(self, transaction_id: int, **kwargs: Any) -> bool:
        """Update a transaction.

        Args:
            transaction_id: Transaction identifier.
            **kwargs: Attributes to update.

        Returns:
            True if transaction was found and updated, False otherwise.
        """
        with self._write() as session:
            transaction = session.query(TransactionDB).filter(
                TransactionDB.id == transaction_id
            ).first()
            if transaction:
                for key, value in kwargs.items():
                    setattr(transaction, key, value)
                return True
            return False

    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            True if transaction was found and deleted, False otherwise.
        """
        with self._write() as session:
            transaction = session.query(TransactionDB).filter(
                TransactionDB.id == transaction_id
            ).first()
            if transaction:
                session.delete(transaction)
                return True
            return False

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of transactions deleted.
        """
        with self._write() as session:
            result = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            ).delete()
            return result  # type: ignore[no-any-return]

    def delete_by_user_id_in_session(
        self, session: SqlAlchemySession, user_id: int
    ) -> int:
        """Delete a user's transactions inside an existing session.

        The caller owns the session and controls commit and rollback,
        so this method never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            Number of transactions deleted.
        """
        result = session.query(TransactionDB).filter(
            TransactionDB.user_id == user_id
        ).delete()
        return result  # type: ignore[no-any-return]


    def get_date_ranges_by_result_ids(
        self,
        user_id: int,
        result_ids: list[str]
    ) -> dict[str, tuple[datetime, datetime]]:
        """Get the min and max transaction dates for each result ID.

        Args:
            user_id: User identifier.
            result_ids: Processing result identifiers to aggregate.

        Returns:
            Dictionary mapping result ID to (min_date, max_date).
            Results with no linked transactions are absent.
        """
        if not result_ids:
            return {}
        with self._read() as session:
            rows = (
                session.query(
                    TransactionDB.result_id,
                    func.min(TransactionDB.date),
                    func.max(TransactionDB.date)
                )
                .filter(
                    TransactionDB.user_id == user_id,
                    TransactionDB.result_id.in_(result_ids)
                )
                .group_by(TransactionDB.result_id)
                .all()
            )
            return {
                cast(str, row[0]): (row[1], row[2]) for row in rows
            }

    def find_all_by_user(
        self,
        user_id: int,
        result_id: Optional[str] = None,
        account: Optional[str] = None
    ) -> list[TransactionDB]:
        """Find all transactions for a user without pagination.

        Used by statistical analysis, which requires the complete dataset.

        Args:
            user_id: User identifier.
            result_id: Optional processing result filter.
            account: Optional account filter.

        Returns:
            List of Transaction entities.
        """
        with self._read() as session:
            query = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            )
            if result_id:
                query = query.filter(TransactionDB.result_id == result_id)
            if account:
                query = query.filter(TransactionDB.account == account)
            return query.all()  # type: ignore[no-any-return]

    def _apply_account_filter(
        self,
        query: 'Query[Any]',
        account: Optional[str] = None
    ) -> 'Query[Any]':
        """Apply the account filter to a transaction query.

        The 'unknown' account also covers legacy rows persisted with an
        empty account.

        Args:
            query: Query to filter.
            account: Filter by account.

        Returns:
            The filtered query.
        """
        if not account:
            return query
        if account == 'unknown':
            return query.filter(
                or_(
                    TransactionDB.account == 'unknown',
                    TransactionDB.account == ''
                )
            )
        return query.filter(TransactionDB.account == account)

    def _apply_result_filters(
        self,
        query: 'Query[Any]',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[str] = None,
        account: Optional[str] = None,
        partner: Optional[str] = None,
        transaction_type: Optional[str] = None,
        month: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        result_id: Optional[str] = None
    ) -> 'Query[Any]':
        """Apply the optional filters of find_by_user_with_filters to a query.

        Args:
            query: Query already filtered by user.
            start_date: Start date filter (inclusive, YYYY-MM-DD format).
            end_date: End date filter (inclusive, YYYY-MM-DD format).
            category_id: Filter by category ID.
            account: Filter by account.
            partner: Filter by partner name (searches both original_partner
                and partner).
            transaction_type: Filter by transaction type (debit/credit).
            month: Filter by month (YYYY-MM format).
            min_amount: Minimum amount filter.
            max_amount: Maximum amount filter.
            result_id: Filter by processing result.

        Returns:
            The query with all applicable filters applied.
        """
        for column, value in (
            (TransactionDB.category_id, category_id),
            (TransactionDB.transaction_type, transaction_type),
            (TransactionDB.result_id, result_id),
        ):
            if value:
                query = query.filter(column == value)

        query = self._apply_account_filter(query, account)

        if min_amount is not None:
            query = query.filter(TransactionDB.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(TransactionDB.amount <= max_amount)

        if start_date:
            try:
                start_dt = DateConverter.parse_to_datetime_utc(start_date)
                query = query.filter(TransactionDB.date >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = DateConverter.parse_to_datetime_utc(end_date)
                query = query.filter(TransactionDB.date <= end_dt)
            except ValueError:
                pass

        if month:
            # Filter by month (supports both YYYY-MM and YYYY.MM formats)
            # Normalize month format to YYYY-MM
            normalized_month = month.replace('.', '-') if '.' in month else month
            query = query.filter(
                extract('year', TransactionDB.date) == int(normalized_month[:4]),
                extract('month', TransactionDB.date) == int(normalized_month[5:7])
            )
        if partner:
            # Search in both original_partner and partner fields
            query = query.filter(
                or_(
                    TransactionDB.original_partner.ilike(f'%{partner}%'),
                    TransactionDB.partner.ilike(f'%{partner}%')
                )
            )

        return query

    def find_by_user_with_filters(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[str] = None,
        account: Optional[str] = None,
        partner: Optional[str] = None,
        transaction_type: Optional[str] = None,
        month: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        result_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = 'date',
        sort_order: str = 'desc'
    ) -> tuple[list[TransactionDB], int]:
        """Find transactions with comprehensive filtering and pagination.

        Args:
            user_id: User identifier.
            start_date: Start date filter (inclusive, YYYY-MM-DD format).
            end_date: End date filter (inclusive, YYYY-MM-DD format).
            category_id: Filter by category ID.
            account: Filter by account.
            partner: Filter by partner name (searches both original_partner and partner).
            transaction_type: Filter by transaction type (debit/credit).
            month: Filter by month (YYYY-MM format).
            min_amount: Minimum amount filter.
            max_amount: Maximum amount filter.
            result_id: Filter by processing result.
            limit: Maximum number of transactions to return (default 100).
            offset: Pagination offset (default 0).
            sort_by: Field to sort by (date, amount, partner, account, category).
            sort_order: Sort order (asc or desc, default: desc).

        Returns:
            Tuple of (transactions, total_count) for pagination metadata.
        """
        with self._read() as session:
            # Build query with user filter
            query: Query[Any] = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            )

            # Apply filters
            query = self._apply_result_filters(
                query,
                start_date=start_date,
                end_date=end_date,
                category_id=category_id,
                account=account,
                partner=partner,
                transaction_type=transaction_type,
                month=month,
                min_amount=min_amount,
                max_amount=max_amount,
                result_id=result_id
            )

            # Get total count for pagination
            total_count = query.count()

            # Apply sorting
            sort_field_map = {
                'date': TransactionDB.date,
                'amount': TransactionDB.amount,
                'partner': TransactionDB.partner,
                'account': TransactionDB.account,
                'category': TransactionDB.category_id
            }
            sort_field = cast(Any, sort_field_map.get(sort_by, TransactionDB.date))
            if sort_order == 'asc':
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())

            # Apply pagination
            transactions = query.offset(offset).limit(limit).all()

            return transactions, total_count  # type: ignore[no-any-return]

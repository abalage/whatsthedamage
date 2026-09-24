"""Transaction repository.

Provides data access for Transaction entities using SQLAlchemy ORM.
Implements the repository pattern for transaction persistence and retrieval.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable
from sqlalchemy import or_, func, extract

from whatsthedamage.utils.date_converter import DateConverter
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.transaction import Transaction as TransactionDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class TransactionRepository(Protocol):
    """Transaction repository protocol.

    Defines the interface for transaction data access operations.
    """

    def create(self, transaction: TransactionDB) -> TransactionDB:
        """Create a new transaction.

        Args:
            transaction: Transaction entity to create.

        Returns:
            The created Transaction entity.
        """
        ...

    def find_by_id(self, transaction_id: int) -> Optional[TransactionDB]:
        """Find transaction by ID.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Transaction entity if found, None otherwise.
        """
        ...

    def find_by_dedup_hash(self, dedup_hash: str) -> Optional[TransactionDB]:
        """Find transaction by deduplication hash.

        Args:
            dedup_hash: SHA-256 deduplication hash.

        Returns:
            Transaction entity if found, None otherwise.
        """
        ...

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
        ...

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
        ...

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
        ...

    def update(self, transaction_id: int, **kwargs: Any) -> bool:
        """Update a transaction.

        Args:
            transaction_id: Transaction identifier.
            **kwargs: Attributes to update.

        Returns:
            True if transaction was found and updated, False otherwise.
        """
        ...

    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            True if transaction was found and deleted, False otherwise.
        """
        ...

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of transactions deleted.
        """
        ...

    def get_count_by_user(self, user_id: int) -> int:
        """Get the total count of transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Total number of transactions for the user.
        """
        ...

    def find_by_processing_result_id(
        self,
        result_id: str,
        user_id: Optional[int] = None
    ) -> list[TransactionDB]:
        """Find all transactions for a specific processing result.

        Args:
            result_id: The processing result ID to filter by.
            user_id: Optional user ID for additional filtering (security).

        Returns:
            List of Transaction entities.
        """
        ...

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

        This is the main method for the GET /transactions endpoint.
        Combines all filter criteria and returns paginated results with total count.

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
        ...


class SqlAlchemyTransactionRepository(SqlAlchemyBaseRepository[TransactionDB]):
    """SQLAlchemy implementation of TransactionRepository.

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
        session = self._get_session()
        try:
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
            session.commit()
            return transaction
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_by_id(self, transaction_id: int) -> Optional[TransactionDB]:
        """Find transaction by ID.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            Transaction entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.id == transaction_id
            ).first()
        finally:
            session.close()

    def find_by_dedup_hash(self, dedup_hash: str) -> Optional[TransactionDB]:
        """Find transaction by deduplication hash.

        Args:
            dedup_hash: SHA-256 deduplication hash.

        Returns:
            Transaction entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.deduplication_hash == dedup_hash
            ).first()
        finally:
            session.close()

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
        session = self._get_session()
        try:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id,
                TransactionDB.deduplication_hash == dedup_hash
            ).first()
        finally:
            session.close()

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
        session = self._get_session()
        try:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id
            ).order_by(TransactionDB.created_at.desc()).offset(offset).limit(limit).all()
        finally:
            session.close()

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
        session = self._get_session()
        try:
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
        finally:
            session.close()

    def update(self, transaction_id: int, **kwargs: Any) -> bool:
        """Update a transaction.

        Args:
            transaction_id: Transaction identifier.
            **kwargs: Attributes to update.

        Returns:
            True if transaction was found and updated, False otherwise.
        """
        session = self._get_session()
        try:
            transaction = session.query(TransactionDB).filter(
                TransactionDB.id == transaction_id
            ).first()
            if transaction:
                for key, value in kwargs.items():
                    setattr(transaction, key, value)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            True if transaction was found and deleted, False otherwise.
        """
        session = self._get_session()
        try:
            transaction = session.query(TransactionDB).filter(
                TransactionDB.id == transaction_id
            ).first()
            if transaction:
                session.delete(transaction)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of transactions deleted.
        """
        session = self._get_session()
        try:
            result = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            ).delete()
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_count_by_user(self, user_id: int) -> int:
        """Get the total count of transactions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Total number of transactions for the user.
        """
        session = self._get_session()
        try:
            return session.query(TransactionDB).filter(  # type: ignore[no-any-return]
                TransactionDB.user_id == user_id
            ).count()
        finally:
            session.close()

    def find_by_processing_result_id(
        self,
        result_id: str,
        user_id: Optional[int] = None
    ) -> list[TransactionDB]:
        """Find all transactions for a specific processing result."""
        session = self._get_session()
        try:
            query = session.query(TransactionDB).filter(
                TransactionDB.result_id == result_id
            )
            if user_id is not None:
                query = query.filter(TransactionDB.user_id == user_id)
            return query.all()  # type: ignore[no-any-return]
        finally:
            session.close()

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
        session = self._get_session()
        try:
            # Build query with user filter
            query = session.query(TransactionDB).filter(
                TransactionDB.user_id == user_id
            )

            # Apply filters
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
            if category_id:
                query = query.filter(TransactionDB.category_id == category_id)
            if account:
                query = query.filter(TransactionDB.account == account)
            if transaction_type:
                query = query.filter(TransactionDB.transaction_type == transaction_type)
            if min_amount is not None:
                query = query.filter(TransactionDB.amount >= min_amount)
            if max_amount is not None:
                query = query.filter(TransactionDB.amount <= max_amount)
            if result_id:
                query = query.filter(TransactionDB.result_id == result_id)
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
            sort_field = sort_field_map.get(sort_by, TransactionDB.date)
            if sort_order == 'asc':
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())

            # Apply pagination
            transactions = query.offset(offset).limit(limit).all()

            return transactions, total_count  # type: ignore[no-any-return]
        finally:
            session.close()

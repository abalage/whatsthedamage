"""Correction repository.

Provides data access for Correction entities using SQLAlchemy ORM.
Implements the repository pattern for correction persistence and retrieval.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable, cast
from sqlalchemy import func
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.correction import Correction as CorrectionDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class CorrectionRepository(Protocol):
    """Correction repository protocol.

    Defines the interface for correction data access operations.
    """

    def create(self, correction: CorrectionDB) -> CorrectionDB:
        """Create a new correction.

        Args:
            correction: Correction entity to create.

        Returns:
            The created Correction entity.
        """
        ...

    def find_by_id(self, correction_id: int) -> Optional[CorrectionDB]:
        """Find correction by ID.

        Args:
            correction_id: Correction identifier.

        Returns:
            Correction entity if found, None otherwise.
        """
        ...

    def find_by_user_and_original_partner(
        self,
        user_id: int,
        original_partner: str
    ) -> Optional[CorrectionDB]:
        """Find correction by user and original_partner (case-insensitive).

        Args:
            user_id: User identifier.
            original_partner: Original partner name to look up.

        Returns:
            Correction entity if found, None otherwise.
        """
        ...

    def find_by_user_id(self, user_id: int) -> list[CorrectionDB]:
        """Find all corrections for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Correction entities for the user.
        """
        ...

    def update(self, correction_id: int, **kwargs: Any) -> bool:
        """Update a correction.

        Args:
            correction_id: Correction identifier.
            **kwargs: Attributes to update.

        Returns:
            True if correction was found and updated, False otherwise.
        """
        ...

    def delete(self, correction_id: int) -> bool:
        """Delete a correction.

        Args:
            correction_id: Correction identifier.

        Returns:
            True if correction was found and deleted, False otherwise.
        """
        ...

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all corrections for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of corrections deleted.
        """
        ...


class SqlAlchemyCorrectionRepository(SqlAlchemyBaseRepository[CorrectionDB]):
    """SQLAlchemy implementation of CorrectionRepository.

    Provides concrete data access operations for Correction entities
    using SQLAlchemy ORM.
    """

    def create(self, correction: CorrectionDB) -> CorrectionDB:
        """Create a new correction in the database.

        Args:
            correction: Correction entity to create.

        Returns:
            The created Correction entity.
        """
        session = self._get_session()
        try:
            session.add(correction)
            session.commit()
            return correction
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_by_id(self, correction_id: int) -> Optional[CorrectionDB]:
        """Find correction by ID.

        Args:
            correction_id: Correction identifier.

        Returns:
            Correction entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(CorrectionDB).filter(  # type: ignore[no-any-return]
                CorrectionDB.id == correction_id
            ).first()
        finally:
            session.close()

    def find_by_user_and_original_partner(
        self,
        user_id: int,
        original_partner: str
    ) -> Optional[CorrectionDB]:
        """Find correction by user and original_partner (case-insensitive).

        Performs case-insensitive lookup by comparing lowercase versions
        of the original_partner values.

        Args:
            user_id: User identifier.
            original_partner: Original partner name to look up.

        Returns:
            Correction entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(CorrectionDB).filter(  # type: ignore[no-any-return]
                CorrectionDB.user_id == user_id,
                func.lower(CorrectionDB.original_partner) == original_partner.lower()
            ).first()
        finally:
            session.close()

    def find_by_user_id(self, user_id: int) -> list[CorrectionDB]:
        """Find all corrections for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Correction entities for the user.
        """
        session = self._get_session()
        try:
            return session.query(CorrectionDB).filter(  # type: ignore[no-any-return]
                CorrectionDB.user_id == user_id
            ).order_by(CorrectionDB.original_partner.asc()).all()
        finally:
            session.close()

    def find_all_by_user(self, user_id: int) -> list[CorrectionDB]:
        """Find all corrections for a user without closing the session.

        Intended for use inside a unit of work, which owns the session and
        controls its lifecycle. Loads a user's corrections in a single query
        so they can be applied to a batch of transactions.

        Args:
            user_id: User identifier.

        Returns:
            List of Correction entities for the user.
        """
        session = self._get_session()
        return session.query(CorrectionDB).filter(  # type: ignore[no-any-return]
            CorrectionDB.user_id == user_id
        ).all()

    def update(self, correction_id: int, **kwargs: Any) -> bool:
        """Update a correction.

        Args:
            correction_id: Correction identifier.
            **kwargs: Attributes to update.

        Returns:
            True if correction was found and updated, False otherwise.
        """
        session = self._get_session()
        try:
            correction = session.query(CorrectionDB).filter(
                CorrectionDB.id == correction_id
            ).first()
            if correction:
                for key, value in kwargs.items():
                    setattr(correction, key, value)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, correction_id: int) -> bool:
        """Delete a correction.

        Args:
            correction_id: Correction identifier.

        Returns:
            True if correction was found and deleted, False otherwise.
        """
        session = self._get_session()
        try:
            correction = session.query(CorrectionDB).filter(
                CorrectionDB.id == correction_id
            ).first()
            if correction:
                session.delete(correction)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all corrections for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of corrections deleted.
        """
        session = self._get_session()
        try:
            result = session.query(CorrectionDB).filter(
                CorrectionDB.user_id == user_id
            ).delete()
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

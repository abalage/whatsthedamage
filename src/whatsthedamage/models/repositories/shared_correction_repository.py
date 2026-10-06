"""Shared correction repository.

Provides data access for SharedCorrection entities using SQLAlchemy ORM.
Implements the repository pattern for shared correction persistence and retrieval.
This is the foundation for US-6 (sharing corrections across users).
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable, cast
from sqlalchemy import func
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.shared_correction import (
    SharedCorrection as SharedCorrectionDB
)
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class SharedCorrectionRepository(Protocol):
    """Shared correction repository protocol.

    Defines the interface for shared correction data access operations.
    """

    def create(self, shared_correction: SharedCorrectionDB) -> SharedCorrectionDB:
        """Create a new shared correction.

        Args:
            shared_correction: SharedCorrection entity to create.

        Returns:
            The created SharedCorrection entity.
        """
        ...

    def find_by_id(self, shared_correction_id: int) -> Optional[SharedCorrectionDB]:
        """Find shared correction by ID.

        Args:
            shared_correction_id: Shared correction identifier.

        Returns:
            SharedCorrection entity if found, None otherwise.
        """
        ...

    def find_by_original_partner_hash(
        self,
        partner_hash: str
    ) -> Optional[SharedCorrectionDB]:
        """Find shared correction by original partner hash.

        Args:
            partner_hash: SHA-256 hash of the original partner name.

        Returns:
            SharedCorrection entity if found, None otherwise.
        """
        ...

    def find_all(self) -> list[SharedCorrectionDB]:
        """Find all shared corrections.

        Returns:
            List of all SharedCorrection entities.
        """
        ...

    def create_or_update(
        self,
        original_partner: str,
        corrected_category_id: str,
        corrected_partner: Optional[str] = None
    ) -> SharedCorrectionDB:
        """Create or update a shared correction.

        If a shared correction with the same partner hash already
        exists, updates the contributed values to the latest ones and
        increments the contribution_count only when the values
        actually changed; identical re-contributions are no-ops.
        Otherwise, creates a new one.

        Args:
            original_partner: Original partner name (will be hashed).
            corrected_category_id: Category identifier for the correction.
            corrected_partner: Corrected partner name (optional).

        Returns:
            The created or updated SharedCorrection entity.
        """
        ...

    def delete(self, shared_correction_id: int) -> bool:
        """Delete a shared correction.

        Args:
            shared_correction_id: Shared correction identifier.

        Returns:
            True if shared correction was found and deleted, False otherwise.
        """
        ...


class SqlAlchemySharedCorrectionRepository(
    SqlAlchemyBaseRepository[SharedCorrectionDB]
):
    """SQLAlchemy implementation of SharedCorrectionRepository.

    Provides concrete data access operations for SharedCorrection entities
    using SQLAlchemy ORM.
    """

    def create(self, shared_correction: SharedCorrectionDB) -> SharedCorrectionDB:
        """Create a new shared correction in the database.

        Args:
            shared_correction: SharedCorrection entity to create.

        Returns:
            The created SharedCorrection entity.
        """
        session = self._get_session()
        try:
            session.add(shared_correction)
            session.commit()
            return shared_correction
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_by_id(self, shared_correction_id: int) -> Optional[SharedCorrectionDB]:
        """Find shared correction by ID.

        Args:
            shared_correction_id: Shared correction identifier.

        Returns:
            SharedCorrection entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(SharedCorrectionDB).filter(  # type: ignore[no-any-return]
                SharedCorrectionDB.id == shared_correction_id
            ).first()
        finally:
            session.close()

    def find_by_original_partner_hash(
        self,
        partner_hash: str
    ) -> Optional[SharedCorrectionDB]:
        """Find shared correction by original partner hash.

        Args:
            partner_hash: SHA-256 hash of the original partner name.

        Returns:
            SharedCorrection entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(SharedCorrectionDB).filter(  # type: ignore[no-any-return]
                SharedCorrectionDB.original_partner_hash == partner_hash
            ).first()
        finally:
            session.close()

    def find_all(self) -> list[SharedCorrectionDB]:
        """Find all shared corrections.

        Returns:
            List of all SharedCorrection entities.
        """
        session = self._get_session()
        try:
            return session.query(SharedCorrectionDB).all()  # type: ignore[no-any-return]
        finally:
            session.close()

    def create_or_update(
        self,
        original_partner: str,
        corrected_category_id: str,
        corrected_partner: Optional[str] = None
    ) -> SharedCorrectionDB:
        """Create or update a shared correction.

        If a shared correction with the same partner hash already
        exists, updates the contributed values to the latest ones and
        increments the contribution_count only when the values
        actually changed; identical re-contributions are no-ops so
        the count reflects distinct value revisions. Otherwise,
        creates a new one. A concurrent insert racing the unique
        partner hash index is retried as an update.

        Args:
            original_partner: Original partner name (will be hashed).
            corrected_category_id: Category identifier for the correction.
            corrected_partner: Corrected partner name (optional).

        Returns:
            The created or updated SharedCorrection entity.
        """
        import hashlib
        from sqlalchemy.exc import IntegrityError

        # Generate hash of lowercase original_partner
        partner_hash = hashlib.sha256(
            original_partner.lower().encode('utf-8')
        ).hexdigest()

        session = self._get_session()
        try:
            # Try to find existing shared correction
            existing = session.query(SharedCorrectionDB).filter(
                SharedCorrectionDB.original_partner_hash == partner_hash
            ).first()

            if existing:
                self._apply_contribution(
                    existing,
                    corrected_partner,
                    corrected_category_id
                )
                session.commit()
                return existing  # type: ignore[no-any-return]

            # Create new shared correction; a concurrent insert may
            # win the unique index race, in which case the row is
            # updated instead
            shared_correction = SharedCorrectionDB(
                original_partner_hash=partner_hash,
                corrected_partner=corrected_partner,
                corrected_category_id=corrected_category_id
            )
            session.add(shared_correction)
            try:
                session.commit()
                return shared_correction
            except IntegrityError:
                session.rollback()
                existing = session.query(SharedCorrectionDB).filter(
                    SharedCorrectionDB.original_partner_hash == partner_hash
                ).first()
                if existing is None:
                    raise
                self._apply_contribution(
                    existing,
                    corrected_partner,
                    corrected_category_id
                )
                session.commit()
                return existing  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _apply_contribution(
        shared_correction: SharedCorrectionDB,
        corrected_partner: Optional[str],
        corrected_category_id: str
    ) -> None:
        """Apply a contribution to an existing shared correction.

        Updates the contributed values and increments the
        contribution_count only when the values actually changed.

        Args:
            shared_correction: Existing shared correction entity.
            corrected_partner: Corrected partner name (optional).
            corrected_category_id: Category identifier for the correction.
        """
        values_changed = (
            shared_correction.corrected_partner != corrected_partner
            or shared_correction.corrected_category_id
            != corrected_category_id
        )
        if not values_changed:
            return

        setattr(shared_correction, 'corrected_partner', corrected_partner)
        setattr(
            shared_correction, 'corrected_category_id', corrected_category_id
        )
        setattr(
            shared_correction, 'contribution_count',
            int(shared_correction.contribution_count) + 1
        )

    def delete(self, shared_correction_id: int) -> bool:
        """Delete a shared correction.

        Args:
            shared_correction_id: Shared correction identifier.

        Returns:
            True if shared correction was found and deleted, False otherwise.
        """
        session = self._get_session()
        try:
            shared_correction = session.query(SharedCorrectionDB).filter(
                SharedCorrectionDB.id == shared_correction_id
            ).first()
            if shared_correction:
                session.delete(shared_correction)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

"""Shared correction repository.

Provides data access for SharedCorrection entities using SQLAlchemy ORM.
Implements the repository pattern for shared correction persistence.
Shared corrections are written on opt-in sharing and withdrawn on
account deletion; no application read path exists yet (US-6).
"""

import hashlib
from datetime import datetime, UTC
from typing import Optional, cast
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.shared_correction import (
    SharedCorrection as SharedCorrectionDB
)
from whatsthedamage.models.database.shared_correction_contribution import (
    SharedCorrectionContribution as ContributionDB
)
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


class SqlAlchemySharedCorrectionRepository(
    SqlAlchemyBaseRepository[SharedCorrectionDB]
):
    """SQLAlchemy implementation of the shared correction repository.

    Provides concrete data access operations for SharedCorrection
    entities using SQLAlchemy ORM.
    """

    def find_by_original_partner_hash(
        self,
        partner_hash: str
    ) -> Optional[SharedCorrectionDB]:
        """Find shared correction by original partner hash.

        Args:
            partner_hash: SHA-256 hash of the original partner name.

        Returns:
            Shared correction entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(SharedCorrectionDB).filter(  # type: ignore[no-any-return]
                SharedCorrectionDB.original_partner_hash == partner_hash
            ).first()

    def create_or_update(
        self,
        original_partner: str,
        corrected_category_id: str,
        corrected_partner: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> SharedCorrectionDB:
        """Create or update a shared correction.

        If a shared correction with the same partner hash already
        exists, updates the contributed values to the latest ones and
        increments the contribution_count only when the values
        actually changed; identical re-contributions are no-ops so
        the count reflects distinct value revisions. Otherwise,
        creates a new one. A concurrent insert racing the unique
        partner hash index is retried as an update. When user_id is
        given, the user's contribution is recorded in the
        contribution link table so it can be withdrawn on account
        deletion (GDPR Art. 7(3)); the link is never exposed via
        the API.

        Args:
            original_partner: Original partner name (will be hashed).
            corrected_category_id: Category identifier for the correction.
            corrected_partner: Corrected partner name (optional).
            user_id: Contributing user identifier (optional).

        Returns:
            The created or updated SharedCorrection entity.
        """
        partner_hash = hashlib.sha256(
            original_partner.lower().encode('utf-8')
        ).hexdigest()

        with self._write() as session:
            existing = self._find_by_partner_hash(session, partner_hash)
            if existing:
                return self._apply_existing_contribution(
                    session,
                    existing,
                    corrected_partner,
                    corrected_category_id,
                    user_id
                )

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
                session.flush()
                if user_id is not None:
                    self._record_contribution(
                        session, user_id, cast(int, shared_correction.id)
                    )
                return shared_correction
            except IntegrityError:
                session.rollback()
                existing = self._find_by_partner_hash(session, partner_hash)
                if existing is None:
                    raise
                return self._apply_existing_contribution(
                    session,
                    existing,
                    corrected_partner,
                    corrected_category_id,
                    user_id
                )

    def _find_by_partner_hash(
        self,
        session: SqlAlchemySession,
        partner_hash: str
    ) -> Optional[SharedCorrectionDB]:
        """Find a shared correction by partner hash inside a session.

        Args:
            session: Active SQLAlchemy session.
            partner_hash: SHA-256 hash of the original partner name.

        Returns:
            Shared correction entity if found, None otherwise.
        """
        return session.query(SharedCorrectionDB).filter(  # type: ignore[no-any-return]
            SharedCorrectionDB.original_partner_hash == partner_hash
        ).first()

    def _apply_existing_contribution(
        self,
        session: SqlAlchemySession,
        existing: SharedCorrectionDB,
        corrected_partner: Optional[str],
        corrected_category_id: str,
        user_id: Optional[int]
    ) -> SharedCorrectionDB:
        """Apply a contribution to an existing shared correction.

        Updates the contributed values, records the user's
        contribution link when the values changed, and commits.

        Args:
            session: Active SQLAlchemy session.
            existing: Existing shared correction entity.
            corrected_partner: Corrected partner name (optional).
            corrected_category_id: Category identifier for the correction.
            user_id: Contributing user identifier (optional).

        Returns:
            The updated SharedCorrection entity.
        """
        changed = self._apply_contribution(
            existing,
            corrected_partner,
            corrected_category_id
        )
        if changed and user_id is not None:
            self._record_contribution(session, user_id, cast(int, existing.id))
        session.commit()
        return existing

    @staticmethod
    def _record_contribution(
        session: SqlAlchemySession,
        user_id: int,
        shared_correction_id: Optional[int]
    ) -> None:
        """Record or increment a user's contribution link row.

        Args:
            session: Active SQLAlchemy session.
            user_id: Contributing user identifier.
            shared_correction_id: Shared correction identifier.
        """
        if shared_correction_id is None:
            return
        link = session.query(ContributionDB).filter(
            ContributionDB.user_id == user_id,
            ContributionDB.shared_correction_id == shared_correction_id
        ).first()
        if link:
            setattr(
                link, 'contribution_count',
                int(link.contribution_count) + 1
            )
        else:
            session.add(ContributionDB(
                user_id=user_id,
                shared_correction_id=shared_correction_id,
                contribution_count=1,
                contributed_at=datetime.now(UTC)
            ))

    def withdraw_links_in_session(
        self, session: SqlAlchemySession, user_id: int
    ) -> int:
        """Withdraw a user's contributions inside an existing session.

        Subtracts the user's recorded revision counts from the
        shared corrections' contribution_count values and deletes
        every shared correction whose count reaches zero, then
        removes the user's contribution link rows. The caller owns
        the session and controls commit and rollback, so this method
        never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            Number of contribution link rows withdrawn.
        """
        links = session.query(ContributionDB).filter(
            ContributionDB.user_id == user_id
        ).all()

        for link in links:
            shared_correction = session.query(
                SharedCorrectionDB
            ).filter(
                SharedCorrectionDB.id == link.shared_correction_id
            ).first()
            if shared_correction is None:
                continue
            remaining = int(shared_correction.contribution_count) \
                - int(link.contribution_count)
            if remaining <= 0:
                session.delete(shared_correction)
            else:
                setattr(
                    shared_correction, 'contribution_count', remaining
                )
            session.delete(link)

        return len(links)

    def delete_links_in_session(
        self, session: SqlAlchemySession, user_id: int
    ) -> int:
        """Delete a user's contribution links inside an existing session.

        Used when an account is deleted without a withdrawal request:
        the user linkage is personal data and is removed with the
        account, while the anonymized shared corrections are retained.
        The caller owns the session and controls commit and rollback,
        so this method never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            Number of contribution link rows deleted.
        """
        result = session.query(ContributionDB).filter(
            ContributionDB.user_id == user_id
        ).delete(synchronize_session=False)
        return result  # type: ignore[no-any-return]

    @staticmethod
    def _apply_contribution(
        shared_correction: SharedCorrectionDB,
        corrected_partner: Optional[str],
        corrected_category_id: str
    ) -> bool:
        """Apply a contribution to an existing shared correction.

        Updates the contributed values and increments the
        contribution_count only when the values actually changed.

        Args:
            shared_correction: Existing shared correction entity.
            corrected_partner: Corrected partner name (optional).
            corrected_category_id: Category identifier for the correction.

        Returns:
            True when the values changed, False otherwise.
        """
        values_changed = (
            shared_correction.corrected_partner != corrected_partner
            or shared_correction.corrected_category_id
            != corrected_category_id
        )
        if not values_changed:
            return False

        setattr(shared_correction, 'corrected_partner', corrected_partner)
        setattr(
            shared_correction, 'corrected_category_id', corrected_category_id
        )
        setattr(
            shared_correction, 'contribution_count',
            int(shared_correction.contribution_count) + 1
        )
        return True

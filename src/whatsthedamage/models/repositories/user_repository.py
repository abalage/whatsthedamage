"""User repository.

Provides data access for User entities using SQLAlchemy ORM.
Implements the repository pattern for user account management.
"""

from datetime import datetime, UTC
from typing import Any, Optional, cast
from sqlalchemy import func
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


class SqlAlchemyUserRepository(SqlAlchemyBaseRepository[UserDB]):
    """SQLAlchemy implementation of the SqlAlchemyUserRepository contract.

    Provides concrete data access operations for User entities
    using SQLAlchemy ORM.
    """

    def create(
        self,
        username: str,
        password_hash: str,
        recovery_code_hash: str
    ) -> UserDB:
        """Create a new user in the database.

        Args:
            username: Unique username.
            password_hash: Argon2id hashed password.
            recovery_code_hash: Argon2id hashed recovery code.

        Returns:
            The created User entity.

        Raises:
            ValueError: If username already exists.
        """
        with self._write() as session:
            # Check if username already exists
            existing = session.query(UserDB).filter(
                UserDB.username == username
            ).first()
            if existing:
                raise ValueError(f"Username '{username}' already exists")

            user = UserDB(
                username=username,
                password_hash=password_hash,
                recovery_code_hash=recovery_code_hash,
                created_at=datetime.now(UTC)
            )
            session.add(user)
            return user

    def find_by_username(self, username: str) -> Optional[UserDB]:
        """Find user by username.

        Args:
            username: Username to search for.

        Returns:
            User entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.username == username
            ).first()

    def find_by_id(self, user_id: int) -> Optional[UserDB]:
        """Find user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.id == user_id
            ).first()

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User identifier.
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.last_login_at = cast(Any, datetime.now(UTC))


    def set_opt_in_sharing(self, user_id: int, opt_in_sharing: bool) -> bool:
        """Set user's correction sharing opt-in preference.

        Records the consent timestamp for demonstrability (GDPR
        Art. 7(1)): opting in stamps opted_in_at and clears
        opted_out_at; opting out stamps opted_out_at.

        Args:
            user_id: User identifier.
            opt_in_sharing: Whether the user opts in to sharing
                corrections.

        Returns:
            True if the preference was updated, False if the user
            was not found.
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                now = datetime.now(UTC)
                user.opt_in_sharing = cast(Any, opt_in_sharing)
                if opt_in_sharing:
                    user.opted_in_at = cast(Any, now)
                    user.opted_out_at = cast(Any, None)
                else:
                    user.opted_out_at = cast(Any, now)
                return True
            return False

    def update_username(self, user_id: int, username: str) -> bool:
        """Update the user's username (right to rectification).

        Args:
            user_id: User identifier.
            username: New unique username (max 255 characters).

        Returns:
            True if the username was updated, False if the user
            was not found.

        Raises:
            ValueError: If the username is already taken.
        """
        with self._write() as session:
            existing = session.query(UserDB).filter(
                UserDB.username == username,
                UserDB.id != user_id
            ).first()
            if existing:
                raise ValueError(f"Username '{username}' already exists")

            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.username = cast(Any, username)
                return True
            return False

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update the user's password hash.

        Args:
            user_id: User identifier.
            new_password_hash: New Argon2id hashed password.

        Returns:
            True if the password was updated, False if the user
            was not found.
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.password_hash = cast(Any, new_password_hash)
                return True
            return False

    def update_password_and_recovery_code(
        self,
        user_id: int,
        new_password_hash: str,
        new_recovery_code_hash: str
    ) -> bool:
        """Atomic update of both password and recovery code hashes for a user.

        Updates both the password hash and recovery code hash in a single
        database transaction to ensure atomicity.

        Args:
            user_id: User identifier.
            new_password_hash: New Argon2id hashed password.
            new_recovery_code_hash: New Argon2id hashed recovery code.

        Returns:
            True if update was successful, False if user not found.

        Raises:
            Exception: On database errors (rollback performed automatically).
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.password_hash = cast(Any, new_password_hash)
                user.recovery_code_hash = cast(Any, new_recovery_code_hash)
                return True
            return False

    def schedule_deletion(
        self,
        user_id: int,
        scheduled_deletion_at: datetime,
        revoke_shared_corrections: bool = False
    ) -> bool:
        """Schedule the user's account deletion.

        Args:
            user_id: User identifier.
            scheduled_deletion_at: UTC timestamp after which the
                retention job deletes the account.
            revoke_shared_corrections: Whether the user's shared
                correction contributions must be withdrawn when the
                account is deleted.

        Returns:
            True if the deletion was scheduled, False if the user
            was not found.
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.scheduled_deletion_at = cast(
                    Any, scheduled_deletion_at
                )
                user.revoke_shared_corrections = cast(
                    Any, revoke_shared_corrections
                )
                return True
            return False

    def cancel_deletion(self, user_id: int) -> bool:
        """Cancel a scheduled account deletion.

        Args:
            user_id: User identifier.

        Returns:
            True if a scheduled deletion was canceled, False if the
            user was not found or had no deletion scheduled.
        """
        with self._write() as session:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user and user.scheduled_deletion_at is not None:
                user.scheduled_deletion_at = cast(Any, None)
                user.revoke_shared_corrections = cast(Any, False)
                return True
            return False

    def find_due_for_deletion(self, now: datetime) -> list[UserDB]:
        """Find users whose scheduled deletion is due.

        Args:
            now: Current UTC timestamp.

        Returns:
            Users with a scheduled_deletion_at at or before now.
        """
        with self._read() as session:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.scheduled_deletion_at.isnot(None),
                UserDB.scheduled_deletion_at <= now
            ).all()

    def find_inactive_since(self, before: datetime) -> list[UserDB]:
        """Find users inactive since the given timestamp.

        A user is inactive when neither their last login nor their
        account creation happened after the given cutoff. Users with
        a scheduled deletion are excluded; they are handled by the
        account deletion purge.

        Args:
            before: UTC timestamp; users with no activity after it
                are considered inactive.

        Returns:
            Users whose last activity is at or before the cutoff.
        """
        with self._read() as session:
            last_activity = func.coalesce(
                UserDB.last_login_at, UserDB.created_at
            )
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                last_activity <= before,
                UserDB.scheduled_deletion_at.is_(None)
            ).all()

    def delete(self, user_id: int) -> bool:
        """Delete a user and all of their data.

        Cascades to sessions, processing results, corrections, and
        transactions. Shared correction contributions are withdrawn
        separately by the retention job when the user requested
        revocation; otherwise they are retained.

        Args:
            user_id: User identifier.

        Returns:
            True if the user was found and deleted, False otherwise.
        """
        with self._write() as session:
            result = self.delete_in_session(session, user_id)
            return result

    def delete_in_session(
        self, session: SqlAlchemySession, user_id: int
    ) -> bool:
        """Delete a user inside an existing session.

        The caller owns the session and controls commit and rollback,
        so this method never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            True if the user was found and deleted, False otherwise.
        """
        user = session.query(UserDB).filter(
            UserDB.id == user_id
        ).first()
        if user:
            session.delete(user)
            return True
        return False


"""User repository.

Provides data access for User entities using SQLAlchemy ORM.
Implements the repository pattern for user account management.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable, cast
from sqlalchemy import func
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class UserRepository(Protocol):
    """User repository protocol.

    Defines the interface for user data access operations.
    """

    def create(
        self,
        username: str,
        password_hash: str,
        recovery_code_hash: str
    ) -> UserDB:
        """Create a new user.

        Args:
            username: Unique username.
            password_hash: Argon2id hashed password.
            recovery_code_hash: Argon2id hashed recovery code.

        Returns:
            The created User entity.
        """
        ...

    def find_by_username(self, username: str) -> Optional[UserDB]:
        """Find user by username.

        Args:
            username: Username to search for.

        Returns:
            User entity if found, None otherwise.
        """
        ...

    def find_by_id(self, user_id: int) -> Optional[UserDB]:
        """Find user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User entity if found, None otherwise.
        """
        ...

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User identifier.
        """
        ...

    def set_active(self, user_id: int, is_active: bool) -> None:
        """Set user's active status.

        Args:
            user_id: User identifier.
            is_active: Whether the user should be active.
        """
        ...

    def set_opt_in_sharing(self, user_id: int, opt_in_sharing: bool) -> bool:
        """Set user's correction sharing opt-in preference.

        Args:
            user_id: User identifier.
            opt_in_sharing: Whether the user opts in to sharing
                corrections.

        Returns:
            True if the preference was updated, False if the user
            was not found.
        """
        ...

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
        ...

    def schedule_deletion(
        self,
        user_id: int,
        scheduled_deletion_at: datetime
    ) -> bool:
        """Schedule the user's account deletion.

        Args:
            user_id: User identifier.
            scheduled_deletion_at: UTC timestamp after which the
                retention job deletes the account.

        Returns:
            True if the deletion was scheduled, False if the user
            was not found.
        """
        ...

    def cancel_deletion(self, user_id: int) -> bool:
        """Cancel a scheduled account deletion.

        Args:
            user_id: User identifier.

        Returns:
            True if a scheduled deletion was canceled, False if the
            user was not found or had no deletion scheduled.
        """
        ...

    def find_due_for_deletion(self, now: datetime) -> list[UserDB]:
        """Find users whose scheduled deletion is due.

        Args:
            now: Current UTC timestamp.

        Returns:
            Users with a scheduled_deletion_at at or before now.
        """
        ...

    def find_inactive_since(self, before: datetime) -> list[UserDB]:
        """Find users inactive since the given timestamp.

        A user is inactive when neither their last login nor their
        account creation happened after the given cutoff.

        Args:
            before: UTC timestamp; users with no activity after it
                are considered inactive.

        Returns:
            Users whose last activity is at or before the cutoff.
        """
        ...

    def delete(self, user_id: int) -> bool:
        """Delete a user and all of their data.

        Cascades to sessions, processing results, corrections, and
        transactions. Shared corrections are not linked to users and
        are never affected.

        Args:
            user_id: User identifier.

        Returns:
            True if the user was found and deleted, False otherwise.
        """
        ...


class SqlAlchemyUserRepository(SqlAlchemyBaseRepository[UserDB]):
    """SQLAlchemy implementation of UserRepository.

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
        session = self._get_session()
        try:
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
            session.commit()
            return user
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_by_username(self, username: str) -> Optional[UserDB]:
        """Find user by username.

        Args:
            username: Username to search for.

        Returns:
            User entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.username == username
            ).first()
        finally:
            session.close()

    def find_by_id(self, user_id: int) -> Optional[UserDB]:
        """Find user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.id == user_id
            ).first()
        finally:
            session.close()

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User identifier.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.last_login_at = cast(Any, datetime.now(UTC))
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_active(self, user_id: int, is_active: bool) -> None:
        """Set user's active status.

        Args:
            user_id: User identifier.
            is_active: Whether the user should be active.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.is_active = cast(Any, is_active)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_opt_in_sharing(self, user_id: int, opt_in_sharing: bool) -> bool:
        """Set user's correction sharing opt-in preference.

        Args:
            user_id: User identifier.
            opt_in_sharing: Whether the user opts in to sharing
                corrections.

        Returns:
            True if the preference was updated, False if the user
            was not found.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.opt_in_sharing = cast(Any, opt_in_sharing)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.password_hash = cast(Any, new_password_hash)
                user.recovery_code_hash = cast(Any, new_recovery_code_hash)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def schedule_deletion(
        self,
        user_id: int,
        scheduled_deletion_at: datetime
    ) -> bool:
        """Schedule the user's account deletion.

        Args:
            user_id: User identifier.
            scheduled_deletion_at: UTC timestamp after which the
                retention job deletes the account.

        Returns:
            True if the deletion was scheduled, False if the user
            was not found.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                user.scheduled_deletion_at = cast(
                    Any, scheduled_deletion_at
                )
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def cancel_deletion(self, user_id: int) -> bool:
        """Cancel a scheduled account deletion.

        Args:
            user_id: User identifier.

        Returns:
            True if a scheduled deletion was canceled, False if the
            user was not found or had no deletion scheduled.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user and user.scheduled_deletion_at is not None:
                user.scheduled_deletion_at = cast(Any, None)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_due_for_deletion(self, now: datetime) -> list[UserDB]:
        """Find users whose scheduled deletion is due.

        Args:
            now: Current UTC timestamp.

        Returns:
            Users with a scheduled_deletion_at at or before now.
        """
        session = self._get_session()
        try:
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                UserDB.scheduled_deletion_at.isnot(None),
                UserDB.scheduled_deletion_at <= now
            ).all()
        finally:
            session.close()

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
        session = self._get_session()
        try:
            last_activity = func.coalesce(
                UserDB.last_login_at, UserDB.created_at
            )
            return session.query(UserDB).filter(  # type: ignore[no-any-return]
                last_activity <= before,
                UserDB.scheduled_deletion_at.is_(None)
            ).all()
        finally:
            session.close()

    def delete(self, user_id: int) -> bool:
        """Delete a user and all of their data.

        Cascades to sessions, processing results, corrections, and
        transactions. Shared corrections are not linked to users and
        are never affected.

        Args:
            user_id: User identifier.

        Returns:
            True if the user was found and deleted, False otherwise.
        """
        session = self._get_session()
        try:
            user = session.query(UserDB).filter(
                UserDB.id == user_id
            ).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_all(self) -> list[UserDB]:
        """Find all users.

        Returns:
            List of all User entities.
        """
        session = self._get_session()
        try:
            return session.query(UserDB).all()  # type: ignore[no-any-return]
        finally:
            session.close()

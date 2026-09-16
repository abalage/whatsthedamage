"""User repository.

Provides data access for User entities using SQLAlchemy ORM.
Implements the repository pattern for user account management.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable, cast
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
                user.password_hash = new_password_hash
                user.recovery_code_hash = new_recovery_code_hash
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

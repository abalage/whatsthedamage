"""User domain model.

Plain Python domain model for user authentication and account management.
Contains business logic for password and recovery code management.
"""

from datetime import datetime, UTC
from typing import Any, Optional

from whatsthedamage.services.password_service import PasswordService


class User:
    """User domain model for authentication operations.

    Represents a user account with business logic for password and recovery
    code management. This is a plain Python class (not a SQLAlchemy model)
    that encapsulates domain logic.

    Attributes:
        id: Unique identifier for the user.
        username: User's unique username.
        password_hash: Argon2id hashed password.
        recovery_code_hash: Argon2id hashed recovery code.
        created_at: Account creation timestamp.
        last_login_at: Last successful login timestamp.
        is_active: Whether the account is active.
        opt_in_sharing: Whether user opts in to sharing corrections.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        username: Optional[str] = None,
        password_hash: Optional[str] = None,
        recovery_code_hash: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_login_at: Optional[datetime] = None,
        is_active: bool = True,
        opt_in_sharing: bool = False
    ):
        """Initialize User domain model.

        Args:
            id: Unique identifier (optional, set on persistence).
            username: Unique username.
            password_hash: Argon2id hashed password.
            recovery_code_hash: Argon2id hashed recovery code.
            created_at: Account creation timestamp.
            last_login_at: Last login timestamp.
            is_active: Account active status.
            opt_in_sharing: Opt-in for sharing corrections.
        """
        self.id = id
        self.username = username
        self._password_hash = password_hash
        self._recovery_code_hash = recovery_code_hash
        self.created_at = created_at or datetime.now(UTC)
        self.last_login_at = last_login_at
        self.is_active = is_active
        self.opt_in_sharing = opt_in_sharing

    @property
    def password_hash(self) -> Optional[str]:
        """Get the password hash."""
        return self._password_hash

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        """Set the password hash directly (for database loading)."""
        self._password_hash = value

    def set_password(self, password: str, password_service: PasswordService) -> None:
        """Hash and set the user's password.

        Args:
            password: Plain text password to hash and store.
            password_service: PasswordService instance for hashing.
        """
        self._password_hash = password_service.hash_password(password)

    def check_password(self, password: str, password_service: PasswordService) -> bool:
        """Verify a password against the stored hash.

        Args:
            password: Plain text password to verify.
            password_service: PasswordService instance for verification.

        Returns:
            True if password matches, False otherwise.
        """
        if self._password_hash is None:
            return False
        return password_service.verify_password(password, self._password_hash)

    @property
    def recovery_code_hash(self) -> Optional[str]:
        """Get the recovery code hash."""
        return self._recovery_code_hash

    @recovery_code_hash.setter
    def recovery_code_hash(self, value: str) -> None:
        """Set the recovery code hash directly (for database loading)."""
        self._recovery_code_hash = value

    def set_recovery_code(self, code: str, password_service: PasswordService) -> None:
        """Hash and set the user's recovery code.

        Args:
            code: Plain text recovery code to hash and store.
            password_service: PasswordService instance for hashing.
        """
        self._recovery_code_hash = password_service.hash_password(code)

    def check_recovery_code(self, code: str, password_service: PasswordService) -> bool:
        """Verify a recovery code against the stored hash.

        Args:
            code: Plain text recovery code to verify.
            password_service: PasswordService instance for verification.

        Returns:
            True if code matches, False otherwise.
        """
        if self._recovery_code_hash is None:
            return False
        return password_service.verify_password(code, self._recovery_code_hash)

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary (excluding sensitive hashes).

        Returns:
            Dictionary representation of user without sensitive data.
        """
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'is_active': self.is_active,
            'opt_in_sharing': self.opt_in_sharing,
        }

    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"

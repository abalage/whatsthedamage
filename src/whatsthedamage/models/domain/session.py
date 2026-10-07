"""Session domain model.

Plain Python domain model for session management with business logic
for validation, expiration, and revocation.
"""

from datetime import datetime, UTC
from typing import Any, Optional


class Session:
    """Session domain model for authentication token management.

    Represents a user session with business logic for validation,
    expiration checking, and revocation. This is a plain Python class
    (not a SQLAlchemy model) that encapsulates domain logic.

    Attributes:
        id: Unique identifier for the session.
        user_id: ID of the associated user.
        token_hash: SHA-256 hash of the session token.
        token_hash_prefix: First 8 characters of token_hash for fast lookup.
        expires_at: Token expiration timestamp.
        created_at: Token creation timestamp.
        ip_address: IP address of the client.
        user_agent: User agent of the client.
        is_revoked: Whether the session has been revoked.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        token_hash: Optional[str] = None,
        token_hash_prefix: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_revoked: bool = False
    ):
        """Initialize Session domain model.

        Args:
            id: Unique identifier (optional, set on persistence).
            user_id: Associated user ID.
            token_hash: SHA-256 hash of the session token.
            token_hash_prefix: First 8 characters of token_hash.
            expires_at: Token expiration timestamp.
            created_at: Token creation timestamp.
            ip_address: Client IP address.
            user_agent: Client user agent.
            is_revoked: Whether session is revoked.
        """
        self.id = id
        self.user_id = user_id
        self.token_hash = token_hash
        self.token_hash_prefix = token_hash_prefix
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now(UTC)
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.is_revoked = is_revoked

    def is_valid(self) -> bool:
        """Check if the session is valid (not expired and not revoked).

        Returns:
            True if session is valid, False otherwise.
        """
        return not self.is_expired() and not self.is_revoked

    def is_expired(self) -> bool:
        """Check if the session has expired.

        Returns:
            True if session has expired, False otherwise.
        """
        if self.expires_at is None:
            return True
        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(UTC)
        expires_at = self.expires_at
        # If expires_at is naive (no timezone), assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return now > expires_at

    def revoke(self) -> None:
        """Mark the session as revoked."""
        self.is_revoked = True

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation of session.
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_revoked': self.is_revoked,
        }

    def __repr__(self) -> str:
        """Return string representation of Session."""
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"expires={self.expires_at}, revoked={self.is_revoked})>"
        )

"""Session database model.

SQLAlchemy ORM model for storing user session tokens with security
hashing. Only SHA-256 hashes of tokens are stored, never raw tokens.
"""

from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.user import User


class Session(Base):
    """Session database model for authentication token management.

    Represents a user session with cryptographically secure token hashing.
    Only SHA-256 hashes of tokens are stored (one-way, secure). Raw tokens
    are never stored in the database.

    Attributes:
        id: Primary key, auto-incrementing.
        user_id: Foreign key to User (required).
        token_hash: SHA-256 hash of the session token (64 char hex).
        token_hash_prefix: First 8 characters of token_hash for fast lookup.
        expires_at: Token expiration timestamp.
        created_at: Token creation timestamp.
        ip_address: IP address of the client that created the session.
        user_agent: User agent string of the client.
        is_revoked: Whether the session has been explicitly revoked.
        user: Many-to-one relationship with User model.
    """

    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(64), nullable=False)
    token_hash_prefix = Column(String(8), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    is_revoked = Column(Boolean, nullable=False, default=False)

    # Relationship to user (many-to-one)
    user = relationship('User', back_populates='sessions')

    # Indexes for performance
    __table_args__ = (
        Index('ix_sessions_token_hash', 'token_hash'),
        Index('ix_sessions_token_hash_prefix', 'token_hash_prefix'),
        Index('ix_sessions_user_id', 'user_id'),
        Index('ix_sessions_expires_at', 'expires_at'),
    )

    def __repr__(self) -> str:
        """Return string representation of Session."""
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"expires={self.expires_at}, revoked={self.is_revoked})>"
        )

    @classmethod
    def generate_expiry(cls, remember_me: bool = False, session_timeout: int = 3600) -> datetime:
        """Generate session expiration timestamp.

        Args:
            remember_me: If True, use extended session duration (7 days).
            session_timeout: Default session timeout in seconds (default 3600 = 1 hour).

        Returns:
            datetime object representing the expiration time.
        """
        if remember_me:
            # 7 days for "remember me" sessions
            return datetime.now(UTC) + timedelta(days=7)
        # Default session timeout (1 hour)
        return datetime.now(UTC) + timedelta(seconds=session_timeout)

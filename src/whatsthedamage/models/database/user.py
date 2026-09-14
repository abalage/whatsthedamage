"""User database model.

SQLAlchemy ORM model for storing user account information including
authentication credentials (hashed).
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.session import Session


class User(Base):
    """User database model for authentication and account management.

    Represents a user account with authentication credentials stored as
    Argon2id hashes. This model follows the SQLAlchemy ORM pattern with
    declarative table definition.

    Attributes:
        id: Primary key, auto-incrementing.
        username: Unique username for authentication (max 255 chars).
        password_hash: Argon2id hashed password (stored as TEXT).
        recovery_code_hash: Argon2id hashed recovery code (stored as TEXT).
        created_at: Timestamp of account creation.
        last_login_at: Timestamp of last successful login (nullable).
        is_active: Whether the account is active (default True).
        opt_in_sharing: Whether user opts in to sharing corrections (default False).
        sessions: One-to-many relationship with Session model.
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    recovery_code_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    opt_in_sharing = Column(Boolean, nullable=False, default=False)

    # Relationship to sessions (one-to-many)
    sessions = relationship(
        'Session',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"

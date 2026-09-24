"""Correction database model.

SQLAlchemy ORM model for storing user-specific corrections for transaction
partner names, categories, and notices.
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.user import User


class Correction(Base):
    """Correction database model for user-specific transaction corrections.

    Stores user corrections for merchant/partner names, allowing case-insensitive
    lookup. Corrections are applied during transaction upload to ensure consistent
    categorization and naming across a user's transaction history.

    Attributes:
        id: Primary key, auto-incrementing.
        user_id: Foreign key to User (required, with CASCADE delete).
        original_partner: Original partner name from CSV, stored in lowercase for
            case-insensitive lookup (max 255 chars).
        corrected_partner: User-specified corrected partner name (max 255 chars, nullable).
        corrected_category_id: User-specified category override (max 50 chars, nullable).
        corrected_notice: User-specified notice/comment (max 500 chars, nullable).
        created_at: Timestamp of correction creation.
        updated_at: Timestamp of last update.
        user: Many-to-one relationship with User model.
    """

    __tablename__ = 'corrections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Lookup key (case-insensitive matching handled via lowercase storage)
    original_partner = Column(String(255), nullable=False)

    # Correction values (all nullable)
    corrected_partner = Column(String(255), nullable=True)
    corrected_category_id = Column(String(50), nullable=True)
    corrected_notice = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=datetime.now(UTC)
    )

    # Relationship to user (many-to-one)
    user = relationship('User', back_populates='corrections')

    # Indexes for performance
    __table_args__ = (
        Index('ix_corrections_user_id', 'user_id'),
        Index('ix_corrections_original_partner', 'original_partner'),
    )

    def __repr__(self) -> str:
        """Return string representation of Correction."""
        return (
            f"<Correction(id={self.id}, user_id={self.user_id}, "
            f"original_partner='{self.original_partner}', "
            f"corrected_partner='{self.corrected_partner}')>"
        )

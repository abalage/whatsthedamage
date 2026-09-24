"""Shared correction database model.

SQLAlchemy ORM model for storing anonymized shared corrections that can be
used across users (foundation for US-6).
"""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Index

from whatsthedamage.models.database.base import Base


class SharedCorrection(Base):
    """Shared correction database model for anonymized correction sharing.

    Stores corrections that have been shared by users (when they opt-in to sharing).
    These corrections are anonymized - they contain no user-specific information
    and are identified by SHA-256 hashes of the original partner names.

    Attributes:
        id: Primary key, auto-incrementing.
        original_partner_hash: SHA-256 hash of lowercase original_partner (64 char hex).
        corrected_partner: Shared corrected partner name (max 255 chars, nullable).
        corrected_category_id: Shared category identifier (max 50 chars, required).
        corrected_notice: Shared notice/comment (max 500 chars, nullable).
        contributed_at: Timestamp when this correction was first contributed.
        contribution_count: Number of users who have contributed this correction.
    """

    __tablename__ = 'shared_corrections'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Anonymized lookup key - SHA-256 hash of lowercase original_partner
    original_partner_hash = Column(String(64), nullable=False)

    # Correction values
    corrected_partner = Column(String(255), nullable=True)
    corrected_category_id = Column(String(50), nullable=False)
    corrected_notice = Column(String(500), nullable=True)

    # Contribution metadata (anonymized)
    contributed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    contribution_count = Column(Integer, nullable=False, default=1)

    # Indexes for performance
    __table_args__ = (
        Index('ix_shared_corrections_original_hash', 'original_partner_hash', unique=True),
        Index('ix_shared_corrections_category', 'corrected_category_id'),
        Index('ix_shared_corrections_contributed_at', 'contributed_at'),
    )

    def __repr__(self) -> str:
        """Return string representation of SharedCorrection."""
        return (
            f"<SharedCorrection(id={self.id}, "
            f"original_partner_hash='{self.original_partner_hash[:16]}...', "
            f"corrected_category_id='{self.corrected_category_id}', "
            f"contribution_count={self.contribution_count})>"
        )

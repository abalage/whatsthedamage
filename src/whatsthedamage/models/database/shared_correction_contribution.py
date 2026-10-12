"""Shared correction contribution database model.

SQLAlchemy ORM model linking users to the shared corrections they
contributed to. The linkage exists solely to honor the right to
withdraw consent (GDPR Art. 7(3)) and the right to erasure: it is
never exposed via the API and shared corrections otherwise remain
anonymous.
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, ForeignKey, Integer, DateTime, UniqueConstraint
)
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.user import User
    from whatsthedamage.models.database.shared_correction import (
        SharedCorrection
    )


class SharedCorrectionContribution(Base):
    """Shared correction contribution database model.

    Records that a user contributed value revisions to a shared
    correction, together with the number of revisions attributable to
    the user. On withdrawal the user's revision count is subtracted
    from the shared correction's contribution_count; a shared
    correction whose count reaches zero is deleted.

    Attributes:
        id: Primary key, auto-incrementing.
        user_id: Foreign key to the contributing user.
        shared_correction_id: Foreign key to the shared correction.
        contribution_count: Number of value revisions this user
            contributed to the shared correction.
        contributed_at: Timestamp of the user's first contribution.
    """

    __tablename__ = 'shared_correction_contributions'
    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'shared_correction_id',
            name='uq_contribution_user_shared_correction'
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey('users.id'), nullable=False, index=True
    )
    shared_correction_id = Column(
        Integer, ForeignKey('shared_corrections.id'), nullable=False
    )
    contribution_count = Column(Integer, nullable=False, default=1)
    contributed_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    user = relationship('User', back_populates='contributions')
    shared_correction = relationship(
        'SharedCorrection', back_populates='contributions'
    )

    def __repr__(self) -> str:
        """Return string representation of SharedCorrectionContribution."""
        return (
            f"<SharedCorrectionContribution(id={self.id}, "
            f"user_id={self.user_id}, "
            f"shared_correction_id={self.shared_correction_id}, "
            f"contribution_count={self.contribution_count})>"
        )

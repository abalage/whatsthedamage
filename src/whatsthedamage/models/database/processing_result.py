"""ProcessingResult database model for storing CSV processing metadata.

SQLAlchemy ORM model for storing processing results metadata in the database.
Note: This is now a metadata-only entity. All transaction data is stored
in the Transaction table and linked via result_id.
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.user import User
    from whatsthedamage.models.database.transaction import Transaction


class ProcessingResult(Base):
    """ProcessingResult database model for storing CSV processing metadata.

    Note: This is now a metadata-only entity. All transaction data is stored
    in the Transaction table and linked via result_id.

    Attributes:
        result_id: Primary key, UUID string (36 chars). Serves as the batch/import identifier.
        user_id: Foreign key to User (required, with CASCADE delete).
        csv_profile_id: The CSV profile ID used for processing.
        row_count: Number of rows processed in this import.
        processing_time: Time taken to process in seconds.
        ml_enabled: Whether ML categorization was enabled for this import.
        start_date: Start date of the date range filter used during processing.
        end_date: End date of the date range filter used during processing.
        created_at: Timestamp of when the result was created.
        user: Many-to-one relationship with User model.
        transactions: One-to-many relationship with Transaction model.
    """

    __tablename__ = 'processing_results'

    result_id = Column(String(36), primary_key=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    csv_profile_id = Column(String(36), nullable=True)
    row_count = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    ml_enabled = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationship to user (many-to-one)
    user = relationship('User', back_populates='processing_results')

    # Relationship to transactions (one-to-many)
    transactions = relationship('Transaction', back_populates='processing_result')

    # Indexes for performance
    __table_args__ = (
        Index('ix_processing_results_user_id', 'user_id'),
        Index('ix_processing_results_created_at', 'created_at'),
        Index('ix_processing_results_csv_profile_id', 'csv_profile_id'),
        Index('ix_processing_results_start_date', 'start_date'),
        Index('ix_processing_results_end_date', 'end_date'),
    )

    def __repr__(self) -> str:
        """Return string representation of ProcessingResult."""
        return (
            f"<ProcessingResult(result_id={self.result_id}, user_id={self.user_id}, "
            f"created_at={self.created_at.isoformat()})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert ProcessingResult to dictionary.

        Returns:
            Dictionary representation of the ProcessingResult.
        """
        return {
            'result_id': self.result_id,
            'user_id': self.user_id,
            'csv_profile_id': self.csv_profile_id,
            'row_count': self.row_count,
            'processing_time': self.processing_time,
            'ml_enabled': self.ml_enabled,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

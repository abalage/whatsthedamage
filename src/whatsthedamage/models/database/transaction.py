"""Transaction database model.

SQLAlchemy ORM model for storing persisted bank transactions linked to users.
Implements deduplication based on immutable transaction fields.
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, \
    Index
from sqlalchemy.orm import relationship

from whatsthedamage.models.database.base import Base

if TYPE_CHECKING:
    from whatsthedamage.models.database.user import User
    from whatsthedamage.models.database.processing_result import ProcessingResult


class Transaction(Base):
    """Transaction database model for persisting bank transactions.

    Represents a bank transaction with full deduplication support based on
    the immutable deduplication key: date + type + original_partner + amount +
    currency + account.

    The deduplication_hash is a SHA-256 hash of the deduplication key for fast
    lookup and prevention of duplicate transactions.

    Attributes:
        id: Primary key, auto-incrementing.
        user_id: Foreign key to User (required, with CASCADE delete).
        date: Transaction date as DateTime object (UTC).
        transaction_type: Transaction type - debit or credit (max 10 chars).
        original_partner: Original partner name from CSV, immutable
            (max 255 chars).
        amount: Transaction amount.
        currency: Currency code (max 3 chars).
        account: Account identifier (max 100 chars).
        deduplication_hash: SHA-256 hash of deduplication key (64 char hex,
            unique).
        category_id: Assigned category identifier (max 50 chars, nullable).
        partner: Corrected partner name (max 255 chars, nullable,
            can be updated).
        notice: Transaction notice/comment (max 500 chars, nullable,
            can be updated).
        confidence: Categorization confidence score (nullable, can be updated).
        created_at: Timestamp of transaction creation.
        updated_at: Timestamp of last update.
        user: Many-to-one relationship with User model.
    """

    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    result_id = Column(String(36), ForeignKey('processing_results.result_id'), nullable=True)

    # Deduplication key fields (immutable)
    date = Column(DateTime, nullable=False)
    transaction_type = Column(String(10), nullable=False)
    original_partner = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    account = Column(String(100), nullable=False)

    # Dedup key hash for fast lookup
    deduplication_hash = Column(String(64), nullable=False, unique=True)

    # Processed/categorized fields (can be updated)
    category_id = Column(String(50), nullable=True)
    partner = Column(String(255), nullable=True)
    notice = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=True)

    # Metadata
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=datetime.now(UTC)
    )

    # Relationship to user (many-to-one)
    user = relationship('User', back_populates='transactions')

    # Relationship to processing result (many-to-one)
    processing_result = relationship('ProcessingResult', back_populates='transactions')

    # Indexes for performance
    __table_args__ = (
        Index('ix_transactions_user_id', 'user_id'),
        Index('ix_transactions_user_dedup', 'user_id', 'deduplication_hash', unique=True),
        Index('ix_transactions_date', 'date'),
        Index('ix_transactions_transaction_type', 'transaction_type'),
        Index('ix_transactions_account', 'account'),
        Index('ix_transactions_created_at', 'created_at'),
        Index('ix_transactions_result_id', 'result_id'),
    )

    def __repr__(self) -> str:
        """Return string representation of Transaction."""
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, "
            f"result_id={self.result_id}, date='{self.date}', "
            f"transaction_type='{self.transaction_type}', "
            f"original_partner='{self.original_partner}', "
            f"amount={self.amount}, currency='{self.currency}')>"
        )

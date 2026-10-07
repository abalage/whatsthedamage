"""Base SQLAlchemy model.

Provides the foundational Base class for all SQLAlchemy models using
declarative base pattern.
"""

from sqlalchemy.orm import declarative_base

# SQLAlchemy declarative base for all database models
Base = declarative_base()

__all__ = ['Base']

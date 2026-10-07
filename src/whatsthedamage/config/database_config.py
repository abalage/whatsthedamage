"""Database configuration for SQLAlchemy ORM.

This module provides configuration and initialization for the SQLAlchemy
database layer used throughout the application.
"""

import os
from typing import Any, Optional, Tuple, cast
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine, URL

# Import Base from models to ensure consistency across the application
from whatsthedamage.models.database.base import Base

# Import all models to ensure they're registered with SQLAlchemy metadata
# This is necessary to resolve circular dependencies in relationships
from whatsthedamage.models.database.user import User  # noqa: F401
from whatsthedamage.models.database.session import Session  # noqa: F401
from whatsthedamage.models.database.transaction import Transaction  # noqa: F401
from whatsthedamage.models.database.processing_result import ProcessingResult  # noqa: F401
from whatsthedamage.models.database.correction import Correction  # noqa: F401
from whatsthedamage.models.database.shared_correction import SharedCorrection  # noqa: F401

__all__ = ['DatabaseConfig', 'get_database_config', 'Base']


class DatabaseConfig:
    """Database configuration manager.

    Handles database URI configuration, engine creation, and session
    management for SQLAlchemy ORM.

    Attributes:
        database_uri: The database connection URI.
        engine: SQLAlchemy engine instance.
        Session: SQLAlchemy session factory.
    """

    def __init__(self, database_uri: Optional[str] = None) -> None:
        """Initialize database configuration.

        Args:
            database_uri: Optional database URI. If not provided, uses
                WHATSTHEDAMAGE_DATABASE_URI environment variable or defaults
                to sqlite:///app.db.
        """
        self.database_uri = database_uri or os.getenv(
            'WHATSTHEDAMAGE_DATABASE_URI',
            'sqlite:///app.db'
        )
        self.engine: Optional[Engine] = None
        self.Session: Optional[sessionmaker[Any]] = None

    def init_db(self) -> Tuple[Engine, sessionmaker[Any]]:
        """Initialize database engine and session factory.

        Creates a SQLAlchemy engine with connection pooling and a session
        factory for creating database sessions.

        Returns:
            Tuple of (engine, Session) for immediate use.
        """
        uri: str | URL = cast(str, self.database_uri)
        self.engine = create_engine(
            uri,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        self.Session = sessionmaker(bind=self.engine)
        return self.engine, self.Session

    def get_session(self) -> Any:
        """Get a new database session.

        Returns:
            A new SQLAlchemy session instance.

        Raises:
            RuntimeError: If database has not been initialized.
        """
        if self.Session is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        session_factory = self.Session
        return session_factory()


def get_database_config() -> DatabaseConfig:
    """Get a configured DatabaseConfig instance.

    Returns:
        A DatabaseConfig instance with URI from environment or default.
    """
    return DatabaseConfig()

"""Base repository.

Provides the shared base class for all SQLAlchemy repository
implementations.
"""

from contextlib import contextmanager
from typing import Any, Generic, TypeVar
from sqlalchemy.orm import Session as SqlAlchemySession

T = TypeVar('T')


class SqlAlchemyBaseRepository(Generic[T]):
    """Base SQLAlchemy repository implementation.

    Provides common database operations using SQLAlchemy sessions.
    Concrete repositories should inherit from this class.
    """

    def __init__(self, session_factory: Any) -> None:
        """Initialize repository with session factory.

        Args:
            session_factory: Callable that returns a SQLAlchemy session.
        """
        self.session_factory = session_factory

    def _get_session(self) -> SqlAlchemySession:
        """Get a new database session.

        Returns:
            A new SQLAlchemy session with expire_on_commit=False to keep
            objects accessible after commit.
        """
        session: SqlAlchemySession = self.session_factory()
        # Keep objects accessible after commit for repository operations
        session.expire_on_commit = False
        return session

    @contextmanager
    def _read(self) -> Any:
        """Provide a session for read-only work, closing it after.

        Yields:
            A SQLAlchemy session that is always closed afterwards.
        """
        session = self._get_session()
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def _write(self) -> Any:
        """Provide a session for atomic write work.

        Commits on success; rolls back and re-raises on failure;
        always closes the session.

        Yields:
            A SQLAlchemy session whose transaction is controlled by
            the context manager.
        """
        session = self._get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

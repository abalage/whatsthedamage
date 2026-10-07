"""Base repository interface.

Provides the abstract base class for all repository implementations.
Uses Python's Protocol for structural subtyping.
"""

from typing import Any, Generic, Optional, Protocol, TypeVar
from sqlalchemy.orm import Session as SqlAlchemySession

T = TypeVar('T')


class BaseRepository(Protocol, Generic[T]):
    """Base repository protocol.

    Defines the common interface for all repository implementations.
    Repositories provide data access abstraction for domain models.
    """

    def create(self, **kwargs: Any) -> T:
        """Create a new entity.

        Args:
            **kwargs: Entity attributes.

        Returns:
            The created entity.
        """
        ...

    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID.

        Args:
            id: Entity identifier.

        Returns:
            The entity if found, None otherwise.
        """
        ...

    def find_all(self) -> list[T]:
        """Find all entities.

        Returns:
            List of all entities.
        """
        ...

    def update(self, entity: T, **kwargs: Any) -> T:  # noqa
        """Update an entity.

        Args:
            entity: Entity to update.
            **kwargs: Attributes to update.

        Returns:
            The updated entity.
        """
        ...

    def delete(self, entity: T) -> None:  # noqa
        """Delete an entity.

        Args:
            entity: Entity to delete.
        """
        ...


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

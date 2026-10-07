"""ProcessingResult repository.

Provides data access for ProcessingResult entities using SQLAlchemy ORM.
Implements the repository pattern for processing result persistence and retrieval.
"""

from typing import Any, Optional, Protocol, runtime_checkable, cast
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.processing_result import ProcessingResult as ProcessingResultDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class ProcessingResultRepository(Protocol):
    """ProcessingResult repository protocol.

    Defines the interface for processing result data access operations.
    """

    def create(self, processing_result: ProcessingResultDB) -> ProcessingResultDB:
        """Create a new processing result.

        Args:
            processing_result: ProcessingResult entity to create.

        Returns:
            The created ProcessingResult entity.
        """
        ...

    def add(self, processing_result: ProcessingResultDB) -> ProcessingResultDB:
        """Add a processing result without committing.

        Args:
            processing_result: ProcessingResult entity to add.

        Returns:
            The added ProcessingResult entity.
        """
        ...

    def find_by_id(self, result_id: str) -> Optional[ProcessingResultDB]:
        """Find processing result by ID.

        Args:
            result_id: Processing result identifier (UUID string).

        Returns:
            ProcessingResult entity if found, None otherwise.
        """
        ...

    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[ProcessingResultDB]:
        """Find processing results by user ID with pagination.

        Args:
            user_id: User identifier.
            limit: Maximum number of results to return (default 100).
            offset: Pagination offset (default 0).

        Returns:
            List of ProcessingResult entities for the user.
        """
        ...

    def find_by_user_and_result_id(
        self,
        user_id: int,
        result_id: str
    ) -> Optional[ProcessingResultDB]:
        """Find processing result by user ID and result ID.

        Args:
            user_id: User identifier.
            result_id: Processing result identifier.

        Returns:
            ProcessingResult entity if found and belongs to user, None otherwise.
        """
        ...

    def update(self, result_id: str, **kwargs: Any) -> bool:
        """Update a processing result.

        Args:
            result_id: Processing result identifier.
            **kwargs: Attributes to update.

        Returns:
            True if processing result was found and updated, False otherwise.
        """
        ...

    def delete(self, result_id: str) -> bool:
        """Delete a processing result.

        Args:
            result_id: Processing result identifier.

        Returns:
            True if processing result was found and deleted, False otherwise.
        """
        ...

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all processing results for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of processing results deleted.
        """
        ...

    def get_count_by_user(self, user_id: int) -> int:
        """Get the total count of processing results for a user.

        Args:
            user_id: User identifier.

        Returns:
            Total number of processing results for the user.
        """
        ...


class SqlAlchemyProcessingResultRepository(SqlAlchemyBaseRepository[ProcessingResultDB]):
    """SQLAlchemy implementation of ProcessingResultRepository.

    Provides concrete data access operations for ProcessingResult entities
    using SQLAlchemy ORM.
    """

    def create(self, processing_result: ProcessingResultDB) -> ProcessingResultDB:
        """Create a new processing result in the database.

        Args:
            processing_result: ProcessingResult entity to create.

        Returns:
            The created ProcessingResult entity.

        Raises:
            ValueError: If a processing result with the same result_id already exists.
        """
        session = self._get_session()
        try:
            # Check if result_id already exists
            existing = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == processing_result.result_id
            ).first()
            if existing:
                raise ValueError(
                    f"ProcessingResult with result_id '{processing_result.result_id}' already exists"
                )

            session.add(processing_result)
            session.commit()
            return processing_result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add(self, processing_result: ProcessingResultDB) -> ProcessingResultDB:
        """Add a processing result to the session without committing.

        Intended for use inside a unit of work, which owns the session
        and controls commit and rollback so multi-entity writes stay
        atomic. The session is not closed here.

        Args:
            processing_result: ProcessingResult entity to add.

        Returns:
            The added ProcessingResult entity.
        """
        session = self._get_session()
        session.add(processing_result)
        session.flush()
        return processing_result

    def find_by_id(self, result_id: str) -> Optional[ProcessingResultDB]:
        """Find processing result by result_id.

        Args:
            result_id: Processing result identifier.

        Returns:
            ProcessingResult entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.result_id == result_id
            ).first()
        finally:
            session.close()

    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[ProcessingResultDB]:
        """Find processing results by user ID with pagination.

        Args:
            user_id: User identifier.
            limit: Maximum number of results to return (default 100).
            offset: Pagination offset (default 0).

        Returns:
            List of ProcessingResult entities for the user.
        """
        session = self._get_session()
        try:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.user_id == user_id
            ).order_by(ProcessingResultDB.created_at.desc()).offset(offset).limit(limit).all()
        finally:
            session.close()

    def find_by_user_and_result_id(
        self,
        user_id: int,
        result_id: str
    ) -> Optional[ProcessingResultDB]:
        """Find processing result by user ID and result_id.

        Args:
            user_id: User identifier.
            result_id: Processing result identifier.

        Returns:
            ProcessingResult entity if found and belongs to user, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.result_id == result_id,
                ProcessingResultDB.user_id == user_id
            ).first()
        finally:
            session.close()

    def update(self, result_id: str, **kwargs: Any) -> bool:
        """Update a processing result.

        Args:
            result_id: Processing result identifier.
            **kwargs: Attributes to update.

        Returns:
            True if processing result was found and updated, False otherwise.
        """
        session = self._get_session()
        try:
            processing_result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == result_id
            ).first()
            if processing_result:
                for key, value in kwargs.items():
                    setattr(processing_result, key, value)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, result_id: str) -> bool:
        """Delete a processing result.

        Args:
            result_id: Processing result identifier.

        Returns:
            True if processing result was found and deleted, False otherwise.
        """
        session = self._get_session()
        try:
            processing_result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == result_id
            ).first()
            if processing_result:
                session.delete(processing_result)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all processing results for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of processing results deleted.
        """
        session = self._get_session()
        try:
            result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.user_id == user_id
            ).delete()
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_count_by_user(self, user_id: int) -> int:
        """Get the total count of processing results for a user.

        Args:
            user_id: User identifier.

        Returns:
            Total number of processing results for the user.
        """
        session = self._get_session()
        try:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.user_id == user_id
            ).count()
        finally:
            session.close()

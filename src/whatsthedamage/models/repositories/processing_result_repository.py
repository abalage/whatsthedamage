"""ProcessingResult repository.

Provides data access for ProcessingResult entities using SQLAlchemy ORM.
Implements the repository pattern for processing result persistence and retrieval.
"""

from typing import Any, Optional, cast
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.processing_result import ProcessingResult as ProcessingResultDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


class SqlAlchemyProcessingResultRepository(SqlAlchemyBaseRepository[ProcessingResultDB]):
    """SQLAlchemy implementation of the SqlAlchemyProcessingResultRepository contract.

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
        with self._write() as session:
            # Check if result_id already exists
            existing = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == processing_result.result_id
            ).first()
            if existing:
                raise ValueError(
                    f"ProcessingResult with result_id '{processing_result.result_id}' already exists"
                )

            session.add(processing_result)
            return processing_result

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
        with self._read() as session:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.result_id == result_id
            ).first()

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
        with self._read() as session:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.user_id == user_id
            ).order_by(ProcessingResultDB.created_at.desc()).offset(offset).limit(limit).all()

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
        with self._read() as session:
            return session.query(ProcessingResultDB).filter(  # type: ignore[no-any-return]
                ProcessingResultDB.result_id == result_id,
                ProcessingResultDB.user_id == user_id
            ).first()

    def update(self, result_id: str, **kwargs: Any) -> bool:
        """Update a processing result.

        Args:
            result_id: Processing result identifier.
            **kwargs: Attributes to update.

        Returns:
            True if processing result was found and updated, False otherwise.
        """
        with self._write() as session:
            processing_result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == result_id
            ).first()
            if processing_result:
                for key, value in kwargs.items():
                    setattr(processing_result, key, value)
                return True
            return False

    def delete(self, result_id: str) -> bool:
        """Delete a processing result.

        Args:
            result_id: Processing result identifier.

        Returns:
            True if processing result was found and deleted, False otherwise.
        """
        with self._write() as session:
            processing_result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.result_id == result_id
            ).first()
            if processing_result:
                session.delete(processing_result)
                return True
            return False

    def delete_by_user_id(self, user_id: int) -> int:
        """Delete all processing results for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of processing results deleted.
        """
        with self._write() as session:
            result = session.query(ProcessingResultDB).filter(
                ProcessingResultDB.user_id == user_id
            ).delete()
            return result  # type: ignore[no-any-return]

    def delete_by_user_id_in_session(
        self, session: SqlAlchemySession, user_id: int
    ) -> int:
        """Delete a user's processing results inside an existing session.

        The caller owns the session and controls commit and rollback,
        so this method never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            Number of processing results deleted.
        """
        result = session.query(ProcessingResultDB).filter(
            ProcessingResultDB.user_id == user_id
        ).delete()
        return result  # type: ignore[no-any-return]


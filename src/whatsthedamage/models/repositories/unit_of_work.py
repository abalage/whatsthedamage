"""Unit of work for atomic multi-entity database writes.

Binds repositories to a single SQLAlchemy session so that several
repository operations participate in one database transaction. The
repositories exposed by the unit of work never commit or close the
session; commit and rollback are controlled by the unit of work,
making multi-entity writes atomic.
"""

from types import TracebackType
from typing import Any, Callable, Optional, Type

from whatsthedamage.models.repositories.processing_result_repository import (
    SqlAlchemyProcessingResultRepository,
)
from whatsthedamage.models.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)


class SqlAlchemyUnitOfWork:
    """Unit of work sharing one session and transaction across repositories.

    Usage:
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.processing_results.add(processing_result)
            uow.transactions.add_all(transactions)
            uow.commit()

    Leaving the with block rolls back uncommitted changes, so a failure
    anywhere inside leaves no partial data behind.
    """

    def __init__(self, session_factory: Any) -> None:
        """Initialize the unit of work.

        Args:
            session_factory: Callable returning a SQLAlchemy session;
                the same factory the repositories are built from.
        """
        self._session_factory = session_factory
        self._session: Any = None

    def __enter__(self) -> 'SqlAlchemyUnitOfWork':
        """Open the shared session and bind repositories to it.

        Returns:
            The unit of work with processing_results and transactions
            repositories operating on the shared session.
        """
        session = self._session_factory()
        session.expire_on_commit = False
        shared_factory: Callable[..., Any] = lambda: session
        self.processing_results: SqlAlchemyProcessingResultRepository = (
            SqlAlchemyProcessingResultRepository(shared_factory)
        )
        self.transactions: SqlAlchemyTransactionRepository = (
            SqlAlchemyTransactionRepository(shared_factory)
        )
        self._session = session
        return self

    def commit(self) -> None:
        """Commit the single transaction spanning all repository writes."""
        if self._session is None:
            raise RuntimeError("Unit of work has not been started")
        self._session.commit()

    def rollback(self) -> None:
        """Roll back the current transaction, discarding pending writes."""
        if self._session is not None:
            self._session.rollback()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        _exc_value: Optional[BaseException],
        _traceback: Optional[TracebackType]
    ) -> None:
        """Roll back pending changes and release the shared session."""
        if self._session is None:
            return
        try:
            if exc_type is not None:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

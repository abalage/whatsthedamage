"""Unit of work for atomic multi-entity database writes.

Binds repositories to a single SQLAlchemy session so that several
repository operations participate in one database transaction. The
repositories exposed by the unit of work never commit or close the
session; commit and rollback are controlled by the unit of work,
making multi-entity writes atomic.
"""

from types import TracebackType
from typing import Any, Callable, Optional, Type

from whatsthedamage.models.repositories.correction_repository import (
    SqlAlchemyCorrectionRepository,
)
from whatsthedamage.models.repositories.processing_result_repository import (
    SqlAlchemyProcessingResultRepository,
)
from whatsthedamage.models.repositories.session_repository import (
    SqlAlchemySessionRepository,
)
from whatsthedamage.models.repositories.shared_correction_repository import (
    SqlAlchemySharedCorrectionRepository,
)
from whatsthedamage.models.repositories.transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from whatsthedamage.models.repositories.user_repository import (
    SqlAlchemyUserRepository,
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
            The unit of work with processing_results, transactions,
            corrections, shared_corrections, sessions and users
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
        self.corrections: SqlAlchemyCorrectionRepository = (
            SqlAlchemyCorrectionRepository(shared_factory)
        )
        self.shared_corrections: SqlAlchemySharedCorrectionRepository = (
            SqlAlchemySharedCorrectionRepository(shared_factory)
        )
        self.sessions: SqlAlchemySessionRepository = (
            SqlAlchemySessionRepository(shared_factory)
        )
        self.users: SqlAlchemyUserRepository = (
            SqlAlchemyUserRepository(shared_factory)
        )
        self._session = session
        return self

    def commit(self) -> None:
        """Commit the single transaction spanning all repository writes."""
        if self._session is None:
            raise RuntimeError("Unit of work has not been started")
        self._session.commit()

    def purge_user(self, user_id: int, revoke_shared_corrections: bool) -> dict[str, int]:
        """Delete a user with all of their personal data in one transaction.

        Shared correction contributions are withdrawn (with their
        contribution counts subtracted) when revoke_shared_corrections
        is true; otherwise only the user's contribution link rows are
        deleted and the anonymized shared corrections are retained.
        The personal data is deleted explicitly before the user row so
        the purge also works on databases without foreign-key cascade
        enforcement. This method never commits on its own; the caller
        controls the transaction via commit().

        Args:
            user_id: User identifier.
            revoke_shared_corrections: Whether the user's shared
                correction contributions must be withdrawn.

        Returns:
            Mapping of purge result counts: contributions_withdrawn
            (or contribution_links_deleted when nothing was withdrawn),
            transactions_deleted, corrections_deleted,
            processing_results_deleted, and sessions_revoked.
        """
        if self._session is None:
            raise RuntimeError("Unit of work has not been started")

        counts: dict[str, int] = {}
        if revoke_shared_corrections:
            counts['contributions_withdrawn'] = (
                self.shared_corrections.withdraw_links_in_session(
                    self._session, user_id
                )
            )
        else:
            counts['contribution_links_deleted'] = (
                self.shared_corrections.delete_links_in_session(
                    self._session, user_id
                )
            )
        counts['transactions_deleted'] = (
            self.transactions.delete_by_user_id_in_session(
                self._session, user_id
            )
        )
        counts['corrections_deleted'] = (
            self.corrections.delete_by_user_id_in_session(
                self._session, user_id
            )
        )
        counts['processing_results_deleted'] = (
            self.processing_results.delete_by_user_id_in_session(
                self._session, user_id
            )
        )
        counts['sessions_revoked'] = (
            self.sessions.revoke_by_user_id_in_session(
                self._session, user_id
            )
        )
        self.users.delete_in_session(self._session, user_id)
        return counts

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

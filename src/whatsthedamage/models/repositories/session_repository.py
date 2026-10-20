"""Session repository.

Provides data access for Session entities using SQLAlchemy ORM.
Implements the repository pattern for session management with lazy cleanup.
"""

from datetime import datetime, UTC
from typing import Any, Optional, cast
from sqlalchemy import or_

from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


class SqlAlchemySessionRepository(SqlAlchemyBaseRepository[SessionDB]):
    """SQLAlchemy implementation of the SqlAlchemySessionRepository contract.

    Provides concrete data access operations for Session entities
    using SQLAlchemy ORM. Implements lazy cleanup of expired sessions.
    """

    def __init__(self, session_factory: Any) -> None:
        """Initialize repository with session factory.

        Args:
            session_factory: Callable that returns a SQLAlchemy session.
        """
        super().__init__(session_factory)

    def create(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        csrf_token_hash: Optional[str] = None
    ) -> SessionDB:
        """Create a new session in the database.

        Args:
            user_id: Associated user ID.
            token_hash: SHA-256 hash of session token.
            expires_at: Token expiration timestamp.
            ip_address: Client IP address.
            user_agent: Client user agent.
            csrf_token_hash: SHA-256 hash of the CSRF token.

        Returns:
            The created Session entity.

        Note:
            Concurrent session limits are a business rule enforced by
            the authentication service, not by the repository.
        """
        with self._write() as session:
            db_session = SessionDB(
                user_id=user_id,
                token_hash=token_hash,
                csrf_token_hash=csrf_token_hash,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
                ip_address=ip_address,
                user_agent=user_agent,
                is_revoked=False
            )
            session.add(db_session)
            return db_session

    def find_by_token_hash(self, token_hash: str) -> Optional[SessionDB]:
        """Find session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            Session entity if found, None otherwise.
        """
        with self._read() as session:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.token_hash == token_hash
            ).first()

    def find_active_by_user_id(self, user_id: int) -> list[SessionDB]:
        """Find the active sessions of a user.

        Args:
            user_id: User identifier.

        Returns:
            Active (non-revoked, non-expired) sessions of the user,
            oldest first.
        """
        with self._read() as session:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.user_id == user_id,
                SessionDB.is_revoked == False,
                SessionDB.expires_at > datetime.now(UTC)
            ).order_by(SessionDB.created_at.asc()).all()

    def find_by_user_id(self, user_id: int) -> list[SessionDB]:
        """Find all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Session entities for the user.
        """
        with self._read() as session:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.user_id == user_id
            ).all()

    def revoke_by_token_hash(self, token_hash: str) -> bool:
        """Revoke a session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            True if session was found and revoked, False otherwise.
        """
        with self._write() as session:
            db_session = session.query(SessionDB).filter(
                SessionDB.token_hash == token_hash
            ).first()  # type: ignore[no-any-return]
            if db_session:
                db_session.is_revoked = cast(Any, True)
                return True
            return False

    def revoke_by_user_id(self, user_id: int) -> int:
        """Revoke all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of sessions revoked.
        """
        with self._write() as session:
            result = self.revoke_by_user_id_in_session(session, user_id)
            return result

    def revoke_by_user_id_in_session(
        self, session: Any, user_id: int
    ) -> int:
        """Revoke all of a user's sessions inside an existing session.

        The caller owns the session and controls commit and rollback,
        so this method never commits on its own.

        Args:
            session: SQLAlchemy session to operate on.
            user_id: User identifier.

        Returns:
            Number of sessions revoked.
        """
        result = session.query(SessionDB).filter(
            SessionDB.user_id == user_id
        ).update({'is_revoked': True})
        return result  # type: ignore[no-any-return]

    def revoke_by_user_id_except(
        self, user_id: int, session_id: int
    ) -> int:
        """Revoke all sessions for a user except one.

        Args:
            user_id: User identifier.
            session_id: Session identifier to keep active.

        Returns:
            Number of sessions revoked.
        """
        with self._write() as session:
            result = session.query(SessionDB).filter(
                SessionDB.user_id == user_id,
                SessionDB.id != session_id,
                SessionDB.is_revoked == False
            ).update({'is_revoked': True})
            return result  # type: ignore[no-any-return]

    def revoke_by_ids(self, session_ids: list[int]) -> int:
        """Revoke sessions by their IDs.

        Args:
            session_ids: Session identifiers to revoke.

        Returns:
            Number of sessions revoked.
        """
        if not session_ids:
            return 0
        with self._write() as session:
            result = session.query(SessionDB).filter(
                SessionDB.id.in_(session_ids)
            ).update({'is_revoked': True})
            return result  # type: ignore[no-any-return]

    def cleanup_expired_and_revoked(self) -> int:
        """Delete expired and revoked sessions.

        Physical cleanup of sessions that are both expired and revoked.
        This should be called periodically or during maintenance.

        Returns:
            Number of sessions deleted.
        """
        with self._write() as session:
            result = session.query(SessionDB).filter(
                or_(
                    SessionDB.expires_at <= datetime.now(UTC),
                    SessionDB.is_revoked == True
                )
            ).delete()
            return result  # type: ignore[no-any-return]

    def find_by_id(self, session_id: int) -> Optional[SessionDB]:
        """Find session by ID."""
        with self._read() as session:
            result = session.query(SessionDB).filter(
                SessionDB.id == session_id
            ).first()
            return result  # type: ignore[no-any-return]

    def update_csrf_token_hash(self, session_id: int, csrf_token_hash: str) -> bool:
        """Update the CSRF token hash for a session."""
        with self._write() as session:
            db_session = session.query(SessionDB).filter(
                SessionDB.id == session_id
            ).first()
            if db_session:
                db_session.csrf_token_hash = csrf_token_hash  # type: ignore[assignment]
                return True
            return False

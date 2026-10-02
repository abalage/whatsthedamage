"""Session repository.

Provides data access for Session entities using SQLAlchemy ORM.
Implements the repository pattern for session management with lazy cleanup.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Protocol, runtime_checkable, cast
from sqlalchemy import or_
from sqlalchemy.orm import Session as SqlAlchemySession

from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.repositories.base_repository import SqlAlchemyBaseRepository


@runtime_checkable
class SessionRepository(Protocol):
    """Session repository protocol.

    Defines the interface for session data access operations.
    """

    def create(
        self,
        user_id: int,
        token_hash: str,
        token_hash_prefix: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        csrf_token_hash: Optional[str] = None
    ) -> SessionDB:
        """Create a new session.

        Args:
            user_id: Associated user ID.
            token_hash: SHA-256 hash of session token.
            token_hash_prefix: First 8 characters of token_hash.
            expires_at: Token expiration timestamp.
            ip_address: Client IP address.
            user_agent: Client user agent.
            csrf_token_hash: SHA-256 hash of the CSRF token.

        Returns:
            The created Session entity.
        """
        ...

    def find_by_token_hash(self, token_hash: str) -> Optional[SessionDB]:
        """Find session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            Session entity if found, None otherwise.
        """
        ...

    def find_by_token_hash_prefix(self, prefix: str) -> Optional[SessionDB]:
        """Find session by token hash prefix (for performance).

        Args:
            prefix: First 8 characters of token_hash.

        Returns:
            Session entity if found, None otherwise.
        """
        ...

    def find_by_user_id(self, user_id: int) -> list[SessionDB]:
        """Find all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Session entities for the user.
        """
        ...

    def revoke_by_token_hash(self, token_hash: str) -> bool:
        """Revoke a session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            True if session was found and revoked, False otherwise.
        """
        ...

    def revoke_by_user_id(self, user_id: int) -> int:
        """Revoke all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of sessions revoked.
        """
        ...

    def revoke_expired(self) -> int:
        """Revoke all expired sessions.

        Returns:
            Number of sessions revoked.
        """
        ...

    def update_csrf_token_hash(self, session_id: int, csrf_token_hash: str) -> bool:
        """Update the CSRF token hash for a session.

        Args:
            session_id: The session identifier.
            csrf_token_hash: The new CSRF token hash.

        Returns:
            True if session was found and updated, False otherwise.
        """
        ...

    def find_by_id(self, session_id: int) -> Optional[SessionDB]:
        """Find session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            Session entity if found, None otherwise.
        """
        ...


class SqlAlchemySessionRepository(SqlAlchemyBaseRepository[SessionDB]):
    """SQLAlchemy implementation of SessionRepository.

    Provides concrete data access operations for Session entities
    using SQLAlchemy ORM. Implements lazy cleanup of expired sessions.
    """

    def __init__(
        self,
        session_factory: Any,
        max_concurrent_sessions: int = 5
    ) -> None:
        """Initialize repository with session factory.

        Args:
            session_factory: Callable that returns a SQLAlchemy session.
            max_concurrent_sessions: Maximum concurrent sessions per user.
        """
        super().__init__(session_factory)
        self.max_concurrent_sessions = max_concurrent_sessions

    def create(
        self,
        user_id: int,
        token_hash: str,
        token_hash_prefix: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        csrf_token_hash: Optional[str] = None
    ) -> SessionDB:
        """Create a new session in the database.

        Args:
            user_id: Associated user ID.
            token_hash: SHA-256 hash of session token.
            token_hash_prefix: First 8 characters of token_hash.
            expires_at: Token expiration timestamp.
            ip_address: Client IP address.
            user_agent: Client user agent.
            csrf_token_hash: SHA-256 hash of the CSRF token.

        Returns:
            The created Session entity.

        Note:
            Enforces concurrent session limit by revoking oldest sessions
            if the limit is exceeded.
        """
        session = self._get_session()
        try:
            # Check and enforce concurrent session limit
            self._enforce_concurrent_limit(session, user_id)

            db_session = SessionDB(
                user_id=user_id,
                token_hash=token_hash,
                token_hash_prefix=token_hash_prefix,
                csrf_token_hash=csrf_token_hash,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
                ip_address=ip_address,
                user_agent=user_agent,
                is_revoked=False
            )
            session.add(db_session)
            session.commit()
            return db_session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _enforce_concurrent_limit(self, session: SqlAlchemySession, user_id: int) -> None:
        """Enforce concurrent session limit for a user.

        If user has more sessions than the limit, revoke the oldest ones.

        Args:
            session: SQLAlchemy session.
            user_id: User identifier.
        """
        # Count active (non-revoked, non-expired) sessions
        active_sessions = session.query(SessionDB).filter(
            SessionDB.user_id == user_id,
            SessionDB.is_revoked == False,
            SessionDB.expires_at > datetime.now(UTC)
        ).order_by(SessionDB.created_at.asc()).all()

        # Revoke oldest sessions if limit exceeded
        while len(active_sessions) >= self.max_concurrent_sessions:
            oldest = active_sessions.pop(0)
            oldest.is_revoked = cast(Any, True)
            session.add(oldest)  # Add to session for update

    def find_by_token_hash(self, token_hash: str) -> Optional[SessionDB]:
        """Find session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            Session entity if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.token_hash == token_hash
            ).first()
        finally:
            session.close()

    def find_by_token_hash_prefix(self, prefix: str) -> Optional[SessionDB]:
        """Find session by token hash prefix.

        Args:
            prefix: First 8 characters of token_hash.

        Returns:
            Session entity if found, None otherwise.

        Note:
            This is a performance optimization for fast lookups without
            needing Redis or other external services.
        """
        session = self._get_session()
        try:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.token_hash_prefix == prefix
            ).first()
        finally:
            session.close()

    def find_by_user_id(self, user_id: int) -> list[SessionDB]:
        """Find all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of Session entities for the user.
        """
        session = self._get_session()
        try:
            return session.query(SessionDB).filter(  # type: ignore[no-any-return]
                SessionDB.user_id == user_id
            ).all()
        finally:
            session.close()

    def revoke_by_token_hash(self, token_hash: str) -> bool:
        """Revoke a session by token hash.

        Args:
            token_hash: SHA-256 hash of session token.

        Returns:
            True if session was found and revoked, False otherwise.
        """
        session = self._get_session()
        try:
            db_session = session.query(SessionDB).filter(
                SessionDB.token_hash == token_hash
            ).first()  # type: ignore[no-any-return]
            if db_session:
                db_session.is_revoked = cast(Any, True)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def revoke_by_user_id(self, user_id: int) -> int:
        """Revoke all sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            Number of sessions revoked.
        """
        session = self._get_session()
        try:
            result = session.query(SessionDB).filter(
                SessionDB.user_id == user_id
            ).update({'is_revoked': True})
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def revoke_expired(self) -> int:
        """Revoke all expired sessions.

        Lazy cleanup: mark expired sessions as revoked.

        Returns:
            Number of sessions revoked.
        """
        session = self._get_session()
        try:
            result = session.query(SessionDB).filter(
                SessionDB.expires_at <= datetime.now(UTC),
                SessionDB.is_revoked == False
            ).update({'is_revoked': True})
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def cleanup_expired_and_revoked(self) -> int:
        """Delete expired and revoked sessions.

        Physical cleanup of sessions that are both expired and revoked.
        This should be called periodically or during maintenance.

        Returns:
            Number of sessions deleted.
        """
        session = self._get_session()
        try:
            result = session.query(SessionDB).filter(
                or_(
                    SessionDB.expires_at <= datetime.now(UTC),
                    SessionDB.is_revoked == True
                )
            ).delete()
            session.commit()
            return result  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def find_by_id(self, session_id: int) -> Optional[SessionDB]:
        """Find session by ID."""
        session = self._get_session()
        try:
            result = session.query(SessionDB).filter(
                SessionDB.id == session_id
            ).first()
            return result  # type: ignore[no-any-return]
        finally:
            session.close()

    def update_csrf_token_hash(self, session_id: int, csrf_token_hash: str) -> bool:
        """Update the CSRF token hash for a session."""
        session = self._get_session()
        try:
            db_session = session.query(SessionDB).filter(
                SessionDB.id == session_id
            ).first()
            if db_session:
                db_session.csrf_token_hash = csrf_token_hash  # type: ignore[assignment]
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

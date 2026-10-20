"""Authenticated session service.

Implements the session lifecycle of the API authentication flow:
session creation (with the concurrent session limit), validation,
revocation, and CSRF token minting. Account-level operations
(registration, login, password management) live in the AccountService.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Tuple, cast

from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.session_repository import (
    SqlAlchemySessionRepository
)
from whatsthedamage.models.repositories.user_repository import (
    SqlAlchemyUserRepository
)
from whatsthedamage.services.csrf_service import CsrfService
from whatsthedamage.services.token_service import TokenService
from whatsthedamage.utils.date_converter import DateConverter


class AuthSessionService:
    """Service for the session lifecycle of authenticated users.

    Attributes:
        user_repository: Repository for user data access.
        session_repository: Repository for session data access.
        token_service: Service for token generation and hashing.
        csrf_service: Service for CSRF token generation.
        session_timeout: Default session timeout in seconds.
        remember_me_duration: Duration for "remember me" sessions in
            seconds.
        max_concurrent_sessions: Maximum concurrent sessions per user.
    """

    def __init__(
        self,
        user_repository: SqlAlchemyUserRepository,
        session_repository: SqlAlchemySessionRepository,
        token_service: TokenService,
        csrf_service: CsrfService,
        session_timeout: int = 3600,
        remember_me_duration: int = 604800,
        max_concurrent_sessions: int = 5
    ) -> None:
        """Initialize AuthSessionService.

        Args:
            user_repository: Repository for user data access.
            session_repository: Repository for session data access.
            token_service: Service for token generation and hashing.
            csrf_service: Service for CSRF token generation.
            session_timeout: Default session timeout in seconds.
            remember_me_duration: Duration for "remember me" sessions
                in seconds.
            max_concurrent_sessions: Maximum concurrent sessions per
                user.
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.token_service = token_service
        self.csrf_service = csrf_service
        self.session_timeout = session_timeout
        self.remember_me_duration = remember_me_duration
        self.max_concurrent_sessions = max_concurrent_sessions

    def create_session(
        self,
        user_id: int,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, datetime, str]:
        """Create a session for a user, enforcing the concurrent limit.

        Revokes the user's oldest sessions when creating the new one
        would exceed the configured maximum number of concurrent
        sessions.

        Args:
            user_id: User identifier.
            remember_me: If True, use extended session duration.
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            Tuple of (session_token, session_expiry, csrf_token).
        """
        self._enforce_concurrent_limit(user_id)

        session_token, session_token_hash = (
            self.token_service.generate_token_and_hash()
        )

        duration = (
            self.remember_me_duration if remember_me else self.session_timeout
        )
        session_expiry = datetime.now(UTC) + timedelta(seconds=duration)

        csrf_token, csrf_token_hash = self.csrf_service.generate_token_and_hash()

        self.session_repository.create(
            user_id=user_id,
            token_hash=session_token_hash,
            csrf_token_hash=csrf_token_hash,
            expires_at=session_expiry,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return session_token, session_expiry, csrf_token

    def _enforce_concurrent_limit(self, user_id: int) -> None:
        """Revoke the oldest sessions beyond the concurrent session limit.

        Args:
            user_id: User identifier.
        """
        active_sessions = self.session_repository.find_active_by_user_id(
            user_id
        )
        excess = len(active_sessions) - self.max_concurrent_sessions + 1
        if excess <= 0:
            return
        self.session_repository.revoke_by_ids(
            [cast(int, s.id) for s in active_sessions[:excess]]
        )

    def validate_session(
        self, session_token: str
    ) -> Optional[Tuple[UserDB, SessionDB]]:
        """Validate a session token and return the associated user and session.

        Args:
            session_token: The session token to validate.

        Returns:
            Tuple of (user, session) if valid, None otherwise.
        """
        session_token_hash = self.token_service.hash_token(session_token)

        session = self.session_repository.find_by_token_hash(session_token_hash)
        if not session:
            return None

        if session.is_revoked:
            return None

        expires_at = DateConverter.ensure_utc(cast(datetime, session.expires_at))
        if expires_at < datetime.now(UTC):
            return None

        user = self.user_repository.find_by_id(cast(int, session.user_id))
        if not user or not user.is_active:
            return None

        return user, session

    def logout_user(self, session_token: str) -> bool:
        """Log out a user by revoking their session.

        Args:
            session_token: The session token to revoke.

        Returns:
            True if session was found and revoked, False otherwise.
        """
        session_token_hash = self.token_service.hash_token(session_token)
        return self.session_repository.revoke_by_token_hash(session_token_hash)

    def logout_all_user_sessions(self, user_id: int) -> int:
        """Log out a user by revoking all their sessions.

        Args:
            user_id: The user ID.

        Returns:
            Number of sessions revoked.
        """
        return self.session_repository.revoke_by_user_id(user_id)

    def revoke_all_sessions_except(self, user_id: int, session_id: int) -> int:
        """Revoke all of a user's sessions except the given one.

        Args:
            user_id: The user ID.
            session_id: Session identifier to keep active.

        Returns:
            Number of sessions revoked.
        """
        return self.session_repository.revoke_by_user_id_except(
            user_id, session_id
        )

    def get_user_sessions(self, user_id: int) -> list[SessionDB]:
        """Get all sessions for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of sessions for the user.
        """
        return self.session_repository.find_by_user_id(user_id)

    def refresh_csrf_token(self, session: SessionDB) -> str:
        """Mint a new CSRF token for a session and persist its hash.

        Args:
            session: The authenticated session entity.

        Returns:
            The new CSRF token. Its hash replaces the stored one, so any
            previously issued token for this session becomes invalid.
        """
        csrf_token, csrf_token_hash = (
            self.csrf_service.generate_token_and_hash()
        )
        self.session_repository.update_csrf_token_hash(
            int(session.id), csrf_token_hash  # type: ignore[arg-type]
        )
        session.csrf_token_hash = csrf_token_hash  # type: ignore[assignment]
        return csrf_token

    def validate_csrf_token(self, token: str, stored_hash: str) -> bool:
        """Validate a CSRF token.

        Args:
            token: The CSRF token to validate.
            stored_hash: The stored hash to compare against.

        Returns:
            True if valid, False otherwise.
        """
        return self.csrf_service.validate_token(token, stored_hash)

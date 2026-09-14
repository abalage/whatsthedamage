"""Authentication service for user registration, login, and session management.

Provides the main business logic for authentication operations including:
- User registration with password and recovery code
- User login with rate limiting
- Session creation and management
- Token generation and validation
"""

import os
from datetime import datetime, timedelta, UTC
from typing import Any, Optional, Tuple, cast
from flask import Flask, request

from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.repositories.user_repository import SqlAlchemyUserRepository
from whatsthedamage.models.repositories.session_repository import SqlAlchemySessionRepository
from whatsthedamage.services.password_service import PasswordService
from whatsthedamage.services.token_service import TokenService
from whatsthedamage.services.recovery_code_service import RecoveryCodeService
from whatsthedamage.services.csrf_service import CsrfService


class AuthenticationService:
    """Service for authentication operations.

    Orchestrates user registration, login, logout, and session management.
    Uses dependency injection for all required services and repositories.

    Attributes:
        user_repository: Repository for user data access.
        session_repository: Repository for session data access.
        password_service: Service for password hashing.
        token_service: Service for token generation and hashing.
        recovery_code_service: Service for recovery code generation.
        csrf_service: Service for CSRF token generation.
        password_min_length: Minimum password length (default 12).
        session_timeout: Default session timeout in seconds (default 3600).
        remember_me_duration: Duration for "remember me" sessions in seconds
            (default 604800 = 7 days).
        max_concurrent_sessions: Maximum concurrent sessions per user
            (default 5).
    """

    def __init__(
        self,
        user_repository: SqlAlchemyUserRepository,
        session_repository: SqlAlchemySessionRepository,
        password_service: PasswordService,
        token_service: TokenService,
        recovery_code_service: RecoveryCodeService,
        csrf_service: CsrfService,
        password_min_length: int = 12,
        session_timeout: int = 3600,
        remember_me_duration: int = 604800,
        max_concurrent_sessions: int = 5
    ):
        """Initialize AuthenticationService.

        Args:
            user_repository: Repository for user data access.
            session_repository: Repository for session data access.
            password_service: Service for password hashing.
            token_service: Service for token generation and hashing.
            recovery_code_service: Service for recovery code generation.
            csrf_service: Service for CSRF token generation.
            password_min_length: Minimum password length.
            session_timeout: Default session timeout in seconds.
            remember_me_duration: Duration for "remember me" sessions.
            max_concurrent_sessions: Maximum concurrent sessions per user.
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.password_service = password_service
        self.token_service = token_service
        self.recovery_code_service = recovery_code_service
        self.csrf_service = csrf_service
        self.password_min_length = password_min_length
        self.session_timeout = session_timeout
        self.remember_me_duration = remember_me_duration
        self.max_concurrent_sessions = max_concurrent_sessions

    def register_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[UserDB, str, str, datetime]:
        """Register a new user account.

        Creates a new user with hashed password and recovery code.
        Also creates an initial session for the user.

        Args:
            username: Unique username for the new user.
            password: Plain text password (minimum length enforced).
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            Tuple of (user, recovery_code, session_token, session_expiry).

        Raises:
            ValueError: If username already exists, password is too short,
                or username is invalid.
        """
        # Validate inputs
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if len(username) > 255:
            raise ValueError("Username cannot exceed 255 characters")
        if len(password) < self.password_min_length:
            raise ValueError(
                f"Password must be at least {self.password_min_length} characters"
            )

        # Check if username exists
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Generate recovery code
        recovery_code = self.recovery_code_service.generate_code()
        formatted_recovery_code = self.recovery_code_service.format_code(recovery_code)

        # Hash password and recovery code
        password_hash = self.password_service.hash_password(password)
        recovery_code_hash = self.password_service.hash_password(recovery_code)

        # Create user
        user = self.user_repository.create(
            username=username.strip(),
            password_hash=password_hash,
            recovery_code_hash=recovery_code_hash
        )

        # Create initial session
        session_token, session_token_hash, session_token_prefix = (
            self.token_service.generate_token_and_hash()
        )
        session_expiry = datetime.now(UTC) + timedelta(
            seconds=self.session_timeout
        )

        session = self.session_repository.create(
            user_id=cast(int, user.id),
            token_hash=session_token_hash,
            token_hash_prefix=session_token_prefix,
            expires_at=session_expiry,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user, formatted_recovery_code, session_token, session_expiry

    def login_user(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[UserDB, str, datetime]:
        """Authenticate a user and create a new session.

        Verifies the username and password, updates the last login timestamp,
        and creates a new session token.

        Args:
            username: User's username.
            password: User's password.
            remember_me: If True, use extended session duration.
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            Tuple of (user, session_token, session_expiry).

        Raises:
            ValueError: If username or password is incorrect, or user is inactive.
        """
        # Find user
        user = self.user_repository.find_by_username(username)
        if not user:
            raise ValueError("Invalid username or password")

        # Check password
        if not self.password_service.verify_password(password, cast(str, user.password_hash)):
            raise ValueError("Invalid username or password")

        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive")

        # Update last login timestamp
        self.user_repository.update_last_login(cast(int, user.id))

        # Create session
        session_token, session_token_hash, session_token_prefix = (
            self.token_service.generate_token_and_hash()
        )

        if remember_me:
            session_expiry = datetime.now(UTC) + timedelta(
                seconds=self.remember_me_duration
            )
        else:
            session_expiry = datetime.now(UTC) + timedelta(
                seconds=self.session_timeout
            )

        session = self.session_repository.create(
            user_id=cast(int, user.id),
            token_hash=session_token_hash,
            token_hash_prefix=session_token_prefix,
            expires_at=session_expiry,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user, session_token, session_expiry

    def logout_user(self, session_token: str) -> bool:
        """Log out a user by revoking their session.

        Args:
            session_token: The session token to revoke.

        Returns:
            True if session was found and revoked, False otherwise.
        """
        # Hash the session token for lookup
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

    def validate_session(self, session_token: str) -> Optional[Tuple[UserDB, SessionDB]]:
        """Validate a session token and return the associated user and session.

        Args:
            session_token: The session token to validate.

        Returns:
            Tuple of (user, session) if valid, None otherwise.
        """
        # Hash the session token for lookup
        session_token_hash = self.token_service.hash_token(session_token)

        # Find session by hash
        session = self.session_repository.find_by_token_hash(session_token_hash)
        if not session:
            return None

        # Check if session is valid
        if session.is_revoked:
            return None

        if session.expires_at < datetime.now(UTC):
            return None

        # Find user
        user = self.user_repository.find_by_id(cast(int, session.user_id))
        if not user or not user.is_active:
            return None

        return user, session

    def validate_session_by_prefix(
        self, session_token: str, prefix: str
    ) -> Optional[Tuple[UserDB, SessionDB]]:
        """Validate a session token using prefix for faster lookup.

        Args:
            session_token: The session token to validate.
            prefix: The expected token hash prefix.

        Returns:
            Tuple of (user, session) if valid, None otherwise.
        """
        # Hash the session token for lookup
        session_token_hash = self.token_service.hash_token(session_token)
        computed_prefix = session_token_hash[:8]

        # Quick rejection if prefix doesn't match
        if computed_prefix != prefix:
            return None

        # Find session by hash
        session = self.session_repository.find_by_token_hash(session_token_hash)
        if not session:
            return None

        # Check if session is valid
        if session.is_revoked:
            return None

        if session.expires_at < datetime.now(UTC):
            return None

        # Find user
        user = self.user_repository.find_by_id(cast(int, session.user_id))
        if not user or not user.is_active:
            return None

        return user, session

    def get_user_sessions(self, user_id: int) -> list[SessionDB]:
        """Get all sessions for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of sessions for the user.
        """
        return self.session_repository.find_by_user_id(user_id)

    def generate_csrf_token(self) -> Tuple[str, str]:
        """Generate a CSRF token and its hash.

        Returns:
            Tuple of (csrf_token, csrf_token_hash).
        """
        return self.csrf_service.generate_token_and_hash()

    def validate_csrf_token(self, token: str, stored_hash: str) -> bool:
        """Validate a CSRF token.

        Args:
            token: The CSRF token to validate.
            stored_hash: The stored hash to compare against.

        Returns:
            True if valid, False otherwise.
        """
        return self.csrf_service.validate_token(token, stored_hash)

    def get_me(
        self, session_token: Optional[str] = None
    ) -> Optional[Tuple[UserDB, SessionDB, str]]:
        """Get current user and session information.

        Also generates a new CSRF token for the session.

        Args:
            session_token: Optional session token. If None, attempts to
                extract from Flask request.

        Returns:
            Tuple of (user, session, csrf_token) if authenticated,
            None otherwise.
        """
        # Try to get session token from request if not provided
        if session_token is None:
            from flask import request as flask_request
            session_token = flask_request.cookies.get('session_token')
            if not session_token:
                return None

        # Validate session
        result = self.validate_session(session_token)
        if not result:
            return None

        user, session = result

        # Generate CSRF token
        csrf_token, _ = self.generate_csrf_token()

        return user, session, csrf_token

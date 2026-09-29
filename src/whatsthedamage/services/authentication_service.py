"""Authentication service for user registration, login, and session management.

Provides the main business logic for authentication operations including:
- User registration with password and recovery code
- User login with rate limiting
- Session creation and management
- Token generation and validation
"""

import os
import logging
from datetime import datetime, timedelta, UTC
from typing import Any, Optional, Tuple, cast
from flask import Flask, request
from whatsthedamage.utils.logging import get_logger

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
        logger: Logger instance for audit logging.
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
        self.logger = get_logger(__name__)

    def register_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[UserDB, str, str, datetime, str]:
        """Register a new user account.

        Creates a new user with hashed password and recovery code.
        Also creates an initial session for the user.

        Args:
            username: Unique username for the new user.
            password: Plain text password (minimum length enforced).
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            Tuple of (user, recovery_code, session_token, session_expiry,
            csrf_token).

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

        # Generate CSRF token and hash for the session
        csrf_token, csrf_token_hash = self.generate_csrf_token()

        session = self.session_repository.create(
            user_id=cast(int, user.id),
            token_hash=session_token_hash,
            token_hash_prefix=session_token_prefix,
            csrf_token_hash=csrf_token_hash,
            expires_at=session_expiry,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user, formatted_recovery_code, session_token, session_expiry, csrf_token

    def login_user(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[UserDB, str, datetime, str]:
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
            Tuple of (user, session_token, session_expiry, csrf_token).

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

        # Generate CSRF token and hash for the session
        csrf_token, csrf_token_hash = self.generate_csrf_token()

        session = self.session_repository.create(
            user_id=cast(int, user.id),
            token_hash=session_token_hash,
            token_hash_prefix=session_token_prefix,
            csrf_token_hash=csrf_token_hash,
            expires_at=session_expiry,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user, session_token, session_expiry, csrf_token

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

    def reset_password_with_recovery_code(
        self,
        username: str,
        recovery_code: str,
        new_password: str
    ) -> Tuple[UserDB, str]:
        """Reset a user's password using their recovery code.

        Validates the username and recovery code, then updates both the
        password and recovery code atomically. Invalidates all existing
        sessions for security.

        Args:
            username: User's username.
            recovery_code: Recovery code provided by user (formatted or raw).
            new_password: New plain text password (minimum length enforced).

        Returns:
            Tuple of (user, new_formatted_recovery_code).
            The new recovery code is displayed once and must be saved.

        Raises:
            ValueError: If username not found, recovery code is invalid,
                or new password is too short.
                Uses generic message "Invalid username or recovery code" to
                prevent username enumeration attacks.
        """
        # Find user by username
        user = self.user_repository.find_by_username(username)
        if not user:
            self.logger.warning("Password reset attempt failed: username not found", extra={"context": {"action": "password_reset", "status": "failed", "reason": "username_not_found"}})
            raise ValueError("Invalid username or recovery code")

        # Parse and normalize the recovery code input (handles both formatted and unformatted)
        parsed_recovery_code = self.recovery_code_service.parse_code(recovery_code)

        # Verify the recovery code
        if not self.password_service.verify_password(
            parsed_recovery_code, cast(str, user.recovery_code_hash)
        ):
            self.logger.warning("Password reset attempt failed: invalid recovery code", extra={"context": {"action": "password_reset", "status": "failed", "reason": "invalid_recovery_code", "user_id": user.id}})
            raise ValueError("Invalid username or recovery code")

        # Validate new password meets minimum length
        if len(new_password) < self.password_min_length:
            self.logger.warning("Password reset attempt failed: password too short", extra={"context": {"action": "password_reset", "status": "failed", "reason": "password_too_short", "user_id": user.id, "password_length": len(new_password), "min_length": self.password_min_length}})
            raise ValueError(
                f"Password must be at least {self.password_min_length} characters"
            )

        # Hash new password
        new_password_hash = self.password_service.hash_password(new_password)

        # Generate new recovery code
        new_raw_code = self.recovery_code_service.generate_code()
        new_formatted_recovery_code = self.recovery_code_service.format_code(new_raw_code)
        new_recovery_code_hash = self.password_service.hash_password(new_raw_code)

        # Atomic update of both password and recovery code
        success = self.user_repository.update_password_and_recovery_code(
            user_id=cast(int, user.id),
            new_password_hash=new_password_hash,
            new_recovery_code_hash=new_recovery_code_hash
        )

        if not success:
            self.logger.error("Password reset failed: database update failed", extra={"context": {"action": "password_reset", "status": "failed", "reason": "database_update_failed", "user_id": user.id}})
            raise ValueError("Invalid username or recovery code")

        # Invalidate all existing sessions for security
        self.logout_all_user_sessions(cast(int, user.id))

        # Update user's last login timestamp for auditing
        self.user_repository.update_last_login(cast(int, user.id))

        # Audit log successful password reset (without sensitive data)
        self.logger.info("Password reset successful", extra={"context": {"action": "password_reset", "status": "success", "user_id": user.id, "username": user.username}})

        # Return the updated user and new formatted recovery code
        # Reload user to get fresh data
        updated_user = self.user_repository.find_by_id(cast(int, user.id))
        assert updated_user is not None, "User should exist after successful update"
        return updated_user, new_formatted_recovery_code

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

        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(UTC)
        expires_at = session.expires_at
        # If expires_at is naive (no timezone), assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < now:
            return None

        # Find user
        user = self.user_repository.find_by_id(cast(int, session.user_id))  # type: ignore[arg-type]
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

        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(UTC)
        expires_at = session.expires_at
        # If expires_at is naive (no timezone), assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < now:
            return None

        # Find user
        user = self.user_repository.find_by_id(cast(int, session.user_id))  # type: ignore[arg-type]
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

    def refresh_csrf_token(self, session: SessionDB) -> str:
        """Mint a new CSRF token for a session and persist its hash.

        Args:
            session: The authenticated session entity.

        Returns:
            The new CSRF token. Its hash replaces the stored one, so any
            previously issued token for this session becomes invalid.
        """
        csrf_token, csrf_token_hash = self.generate_csrf_token()
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

    def get_me(
        self, session_token: Optional[str] = None
    ) -> Optional[Tuple[UserDB, SessionDB, Optional[str]]]:
        """Get current user and session information.

        Returns a CSRF token only when the session does not have one yet;
        this call never rotates an existing token, so tokens already held
        by clients stay valid.

        Args:
            session_token: Optional session token. If None, attempts to
                extract from Flask request.

        Returns:
            Tuple of (user, session, csrf_token) if authenticated,
            None otherwise. csrf_token is None when the session already
            has a CSRF token hash.
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

        # Only mint a token when the session has none; existing tokens
        # must not be invalidated by this idempotent probe
        if session.csrf_token_hash:
            return user, session, None

        csrf_token = self.refresh_csrf_token(session)

        return user, session, csrf_token

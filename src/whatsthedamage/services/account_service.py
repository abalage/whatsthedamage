"""Account service.

Implements account-level authentication operations: registration,
login, password reset and change, username rectification, and the
sharing opt-in. Session lifecycle (creation, validation, revocation)
lives in the AuthSessionService.
"""

from datetime import datetime, UTC
from typing import Optional, Tuple, cast

from whatsthedamage.models.database.session import Session as SessionDB
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.repositories.user_repository import (
    SqlAlchemyUserRepository
)
from whatsthedamage.services.auth_errors import (
    AccountDeletionPendingError,
    AccountInactiveError,
    InvalidCredentialsError,
    InvalidPasswordError,
    PasswordTooWeakError,
    UsernameExistsError,
)
from whatsthedamage.services.auth_session_service import AuthSessionService
from whatsthedamage.services.password_service import PasswordService
from whatsthedamage.services.recovery_code_service import RecoveryCodeService
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.utils.logging import get_logger


class AccountService:
    """Service for account-level authentication operations.

    Attributes:
        user_repository: Repository for user data access.
        password_service: Service for password hashing.
        recovery_code_service: Service for recovery code generation.
        session_service: Service for the session lifecycle.
        password_min_length: Minimum password length.
        logger: Logger instance for audit logging.
    """

    def __init__(
        self,
        user_repository: SqlAlchemyUserRepository,
        password_service: PasswordService,
        recovery_code_service: RecoveryCodeService,
        session_service: AuthSessionService,
        password_min_length: int = 12
    ) -> None:
        """Initialize AccountService.

        Args:
            user_repository: Repository for user data access.
            password_service: Service for password hashing.
            recovery_code_service: Service for recovery code
                generation.
            session_service: Service for the session lifecycle.
            password_min_length: Minimum password length.
        """
        self.user_repository = user_repository
        self.password_service = password_service
        self.recovery_code_service = recovery_code_service
        self.session_service = session_service
        self.password_min_length = password_min_length
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
            UsernameExistsError: If the username is already taken.
            PasswordTooWeakError: If the password is too short.
            ValueError: If the username is invalid.
        """
        # Validate inputs
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if len(username) > 255:
            raise ValueError("Username cannot exceed 255 characters")
        if len(password) < self.password_min_length:
            raise PasswordTooWeakError(
                f"Password must be at least {self.password_min_length} characters"
            )

        # Check if username exists
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            raise UsernameExistsError(f"Username '{username}' already exists")

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
        session_token, session_expiry, csrf_token = (
            self.session_service.create_session(
                cast(int, user.id),
                ip_address=ip_address,
                user_agent=user_agent
            )
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

        Verifies the username and password, updates the last login
        timestamp, and creates a new session token.

        Args:
            username: User's username.
            password: User's password.
            remember_me: If True, use extended session duration.
            ip_address: Client IP address.
            user_agent: Client user agent.

        Returns:
            Tuple of (user, session_token, session_expiry, csrf_token).

        Raises:
            InvalidCredentialsError: If username or password is
                incorrect.
            AccountInactiveError: If the user is inactive.
            AccountDeletionPendingError: If the account's deletion
                grace period has elapsed.
        """
        # Find user
        user = self.user_repository.find_by_username(username)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")

        # Check password
        if not self.password_service.verify_password(password, cast(str, user.password_hash)):
            raise InvalidCredentialsError("Invalid username or password")

        # Check if user is active
        if not user.is_active:
            raise AccountInactiveError("Account is inactive")

        # A scheduled account deletion is canceled by logging in
        # during the grace period; past the scheduled timestamp login
        # is refused until the retention job deletes the account.
        deletion_at = cast(Optional[datetime], user.scheduled_deletion_at)
        if deletion_at is not None:
            deletion_at = DateConverter.ensure_utc(deletion_at)
            if deletion_at <= datetime.now(UTC):
                raise AccountDeletionPendingError(
                    "Account is scheduled for deletion"
                )
            self.user_repository.cancel_deletion(cast(int, user.id))
            self.logger.info(
                "Scheduled account deletion canceled by login",
                extra={"context": {
                    "action": "account_deletion",
                    "status": "canceled",
                    "user_id": user.id
                }}
            )

        # Update last login timestamp
        self.user_repository.update_last_login(cast(int, user.id))

        # Create session
        session_token, session_expiry, csrf_token = (
            self.session_service.create_session(
                cast(int, user.id),
                remember_me=remember_me,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )

        return user, session_token, session_expiry, csrf_token

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
            InvalidCredentialsError: If the username or recovery code
                is wrong. Uses a generic message to prevent username
                enumeration attacks.
            PasswordTooWeakError: If the new password is too short.
        """
        # Find user by username
        user = self.user_repository.find_by_username(username)
        if not user:
            self.logger.warning("Password reset attempt failed: username not found", extra={"context": {"action": "password_reset", "status": "failed", "reason": "username_not_found"}})
            raise InvalidCredentialsError("Invalid username or recovery code")

        # Parse and normalize the recovery code input (handles both formatted and unformatted)
        parsed_recovery_code = self.recovery_code_service.parse_code(recovery_code)

        # Verify the recovery code
        if not self.password_service.verify_password(
            parsed_recovery_code, cast(str, user.recovery_code_hash)
        ):
            self.logger.warning("Password reset attempt failed: invalid recovery code", extra={"context": {"action": "password_reset", "status": "failed", "reason": "invalid_recovery_code", "user_id": user.id}})
            raise InvalidCredentialsError("Invalid username or recovery code")

        # Validate new password meets minimum length
        if len(new_password) < self.password_min_length:
            self.logger.warning("Password reset attempt failed: password too short", extra={"context": {"action": "password_reset", "status": "failed", "reason": "password_too_short", "user_id": user.id, "password_length": len(new_password), "min_length": self.password_min_length}})
            raise PasswordTooWeakError(
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
            raise InvalidCredentialsError("Invalid username or recovery code")

        # Invalidate all existing sessions for security
        self.session_service.logout_all_user_sessions(cast(int, user.id))

        # Update user's last login timestamp for auditing
        self.user_repository.update_last_login(cast(int, user.id))

        # Audit log successful password reset (without personal data
        # beyond the user identifier)
        self.logger.info("Password reset successful", extra={"context": {"action": "password_reset", "status": "success", "user_id": user.id}})

        # Return the updated user and new formatted recovery code
        # Reload user to get fresh data
        updated_user = self.user_repository.find_by_id(cast(int, user.id))
        assert updated_user is not None, "User should exist after successful update"
        return updated_user, new_formatted_recovery_code

    def update_opt_in_sharing(
        self, user_id: int, opt_in_sharing: bool
    ) -> Optional[UserDB]:
        """Update the user's correction sharing opt-in preference.

        The repository records the consent timestamps (opted_in_at /
        opted_out_at) for demonstrability (GDPR Art. 7(1)).

        Args:
            user_id: User identifier.
            opt_in_sharing: Whether the user opts in to sharing
                corrections.

        Returns:
            The updated User entity, or None if the user was not found.
        """
        updated = self.user_repository.set_opt_in_sharing(
            user_id, opt_in_sharing
        )
        if not updated:
            return None
        return self.user_repository.find_by_id(user_id)

    def update_username(
        self, user: UserDB, username: str
    ) -> Optional[UserDB]:
        """Update the user's username (right to rectification).

        Args:
            user: The authenticated user requesting the change.
            username: New username (stripped, max 255 characters).

        Returns:
            The updated User entity, or None if the user was not found.

        Raises:
            UsernameExistsError: If the username is already taken.
            ValueError: If the username is empty or too long.
        """
        stripped = username.strip()
        if not stripped:
            raise ValueError("Username cannot be empty")
        if len(stripped) > 255:
            raise ValueError("Username cannot exceed 255 characters")

        existing = self.user_repository.find_by_username(stripped)
        if existing and existing.id != user.id:
            raise UsernameExistsError(
                f"Username '{stripped}' already exists"
            )

        updated = self.user_repository.update_username(
            cast(int, user.id), stripped
        )
        if not updated:
            return None

        self.logger.info(
            "Username updated",
            extra={"context": {
                "action": "username_update",
                "status": "success",
                "user_id": user.id
            }}
        )
        return self.user_repository.find_by_id(cast(int, user.id))

    def change_password(
        self,
        user: UserDB,
        current_password: str,
        new_password: str,
        current_session: SessionDB
    ) -> None:
        """Change the user's password while logged in.

        Verifies the current password, validates the new password,
        updates the password hash, and revokes all other sessions of
        the user. The current session stays valid.

        Args:
            user: The authenticated user requesting the change.
            current_password: Current password for confirmation.
            new_password: New plain text password (minimum length
                enforced).
            current_session: The session the request was made from;
                it is kept active.

        Raises:
            InvalidPasswordError: If the current password is
                incorrect.
            PasswordTooWeakError: If the new password is too short.
        """
        if not self.password_service.verify_password(
            current_password, cast(str, user.password_hash)
        ):
            self.logger.warning(
                "Password change failed: invalid current password",
                extra={"context": {
                    "action": "password_change",
                    "status": "failed",
                    "reason": "invalid_password",
                    "user_id": user.id
                }}
            )
            raise InvalidPasswordError("Invalid current password")

        if len(new_password) < self.password_min_length:
            raise PasswordTooWeakError(
                f"Password must be at least "
                f"{self.password_min_length} characters"
            )

        new_password_hash = self.password_service.hash_password(
            new_password
        )
        updated = self.user_repository.update_password(
            cast(int, user.id), new_password_hash
        )
        if not updated:
            raise ValueError("User not found")

        revoked = self.session_service.revoke_all_sessions_except(
            cast(int, user.id), cast(int, current_session.id)
        )

        self.logger.info(
            "Password changed",
            extra={"context": {
                "action": "password_change",
                "status": "success",
                "user_id": user.id,
                "sessions_revoked": revoked
            }}
        )

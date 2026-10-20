"""Typed authentication errors.

The authentication and retention services raise these typed
exceptions instead of plain ValueErrors, so endpoints map HTTP
statuses from the exception type rather than sniffing message
substrings. All errors subclass ValueError for backward
compatibility with generic handlers.
"""


class AuthError(ValueError):
    """Base class of the typed authentication errors."""


class UsernameExistsError(AuthError):
    """Raised when registering or renaming to an existing username."""


class PasswordTooWeakError(AuthError):
    """Raised when a new password is shorter than the minimum length."""


class InvalidCredentialsError(AuthError):
    """Raised on a wrong username/password or recovery code."""


class AccountInactiveError(AuthError):
    """Raised when the account has been deactivated."""


class AccountDeletionPendingError(AuthError):
    """Raised when the account's deletion grace period has elapsed."""


class InvalidPasswordError(AuthError):
    """Raised when confirming with the wrong current password."""

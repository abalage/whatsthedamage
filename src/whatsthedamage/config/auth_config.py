"""Authentication configuration.

Centralized configuration for authentication-related settings.
"""

import os
from typing import Any, Optional, cast


class AuthConfig:
    """Authentication configuration container.

    Provides configuration values for authentication services with
    sensible defaults and environment variable overrides.

    Attributes:
        SECRET_KEY: Flask secret key for session security.
        SESSION_COOKIE_SECURE: Whether to use Secure flag for cookies.
        SESSION_COOKIE_HTTPONLY: Whether to use HttpOnly flag for cookies.
        SESSION_COOKIE_SAMESITE: SameSite policy for cookies.
        PERMANENT_SESSION_LIFETIME: Session lifetime in seconds.
        PASSWORD_MIN_LENGTH: Minimum password length.
        PASSWORD_HASH_PARAMETERS: Parameters for Argon2id hashing.
        SESSION_TOKEN_LENGTH: Length of session tokens in bytes.
        SESSION_MAX_CONCURRENT: Maximum concurrent sessions per user.
        SESSION_REMEMBER_ME_DURATION: Duration for "remember me" sessions.
        SESSION_CLEANUP_ON_LOGIN: Whether to clean up expired sessions on login.
        RATE_LIMIT_LOGIN: Rate limit for login attempts.
        RATE_LIMIT_STORAGE: Storage backend for rate limiting.
        CSRF_TOKEN_LENGTH: Length of CSRF tokens in bytes.
        RECOVERY_CODE_LENGTH: Length of recovery codes.
        RECOVERY_CODE_CHARACTERS: Character set for recovery codes.
    """

    # Flask session configuration
    SECRET_KEY: bytes = cast(
        bytes,
        os.getenv('WHATSTHEDAMAGE_SECRET_KEY') or os.urandom(24)
    )
    SESSION_COOKIE_SECURE: bool = os.getenv(
        'WHATSTHEDAMAGE_SESSION_COOKIE_SECURE',
        'true'
    ).lower() == 'true'
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = os.getenv(
        'WHATSTHEDAMAGE_SESSION_COOKIE_SAMESITE',
        'Lax'
    )
    PERMANENT_SESSION_LIFETIME: int = int(os.getenv(
        'WHATSTHEDAMAGE_PERMANENT_SESSION_LIFETIME',
        '3600'
    ))

    # Password configuration
    PASSWORD_MIN_LENGTH: int = int(os.getenv(
        'WHATSTHEDAMAGE_PASSWORD_MIN_LENGTH',
        '12'
    ))
    PASSWORD_HASH_PARAMETERS: dict[str, Any] = {
        'time_cost': int(os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_TIME_COST',
            '3'
        )),
        'memory_cost': int(os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_MEMORY_COST',
            '65536'
        )),
        'parallelism': int(os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_PARALLELISM',
            '4'
        )),
        'hash_len': int(os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_HASH_LEN',
            '32'
        )),
        'salt_len': int(os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_SALT_LEN',
            '16'
        )),
        'type': os.getenv(
            'WHATSTHEDAMAGE_PASSWORD_TYPE',
            'argon2id'
        )
    }

    # Session configuration
    SESSION_TOKEN_LENGTH: int = int(os.getenv(
        'WHATSTHEDAMAGE_SESSION_TOKEN_LENGTH',
        '32'
    ))
    SESSION_MAX_CONCURRENT: int = int(os.getenv(
        'WHATSTHEDAMAGE_SESSION_MAX_CONCURRENT',
        '5'
    ))
    SESSION_REMEMBER_ME_DURATION: int = int(os.getenv(
        'WHATSTHEDAMAGE_SESSION_REMEMBER_ME_DURATION',
        '604800'  # 7 days
    ))
    SESSION_CLEANUP_ON_LOGIN: bool = os.getenv(
        'WHATSTHEDAMAGE_SESSION_CLEANUP_ON_LOGIN',
        'true'
    ).lower() == 'true'

    # Rate limiting configuration
    RATE_LIMIT_LOGIN: str = os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_LOGIN',
        '5 per 15 minutes'
    )
    RATE_LIMIT_STORAGE: str = os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_STORAGE',
        'memory://'
    )

    # CSRF configuration
    CSRF_TOKEN_LENGTH: int = int(os.getenv(
        'WHATSTHEDAMAGE_CSRF_TOKEN_LENGTH',
        '32'
    ))

    # Recovery code configuration
    RECOVERY_CODE_LENGTH: int = int(os.getenv(
        'WHATSTHEDAMAGE_RECOVERY_CODE_LENGTH',
        '16'
    ))
    RECOVERY_CODE_CHARACTERS: str = os.getenv(
        'WHATSTHEDAMAGE_RECOVERY_CODE_CHARACTERS',
        'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    )


# Create a singleton instance
_auth_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """Get the authentication configuration instance.

    Returns:
        AuthConfig instance.
    """
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig()
    return _auth_config

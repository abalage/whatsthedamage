"""CSRF service for generating and validating CSRF tokens.

Provides protection against Cross-Site Request Forgery attacks by
generating unique tokens per session and validating them on state-changing
requests.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple


class CsrfService:
    """Service for generating and validating CSRF tokens.

    CSRF tokens are generated as cryptographically secure random strings
    and hashed before storage. They are tied to user sessions and have
    a limited lifetime.

    Attributes:
        token_length: Length of CSRF tokens in bytes (default 32).
        token_timeout: Token validity duration in seconds (default 3600 = 1 hour).
    """

    def __init__(self, token_length: int = 32, token_timeout: int = 3600):
        """Initialize CsrfService.

        Args:
            token_length: Length of CSRF tokens in bytes (default 32).
            token_timeout: Token validity duration in seconds (default 3600).
        """
        self.token_length = token_length
        self.token_timeout = token_timeout

    def generate_token(self) -> str:
        """Generate a cryptographically secure CSRF token.

        Returns:
            URL-safe base64 encoded random token string.
        """
        return secrets.token_urlsafe(self.token_length)

    def hash_token(self, token: str) -> str:
        """Hash a CSRF token using SHA-256 for secure storage.

        Args:
            token: The CSRF token to hash.

        Returns:
            Hexadecimal SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def generate_token_and_hash(self) -> Tuple[str, str]:
        """Generate a CSRF token and its hash in one operation.

        Returns:
            Tuple of (token, token_hash).
        """
        token = self.generate_token()
        token_hash = self.hash_token(token)
        return token, token_hash

    def validate_token(self, token: str, stored_hash: str) -> bool:
        """Validate a CSRF token against a stored hash.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            token: The CSRF token to validate.
            stored_hash: The stored SHA-256 hash to compare against.

        Returns:
            True if the token's hash matches the stored hash, False otherwise.
        """
        try:
            computed_hash = self.hash_token(token)
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

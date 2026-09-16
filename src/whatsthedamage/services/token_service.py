"""Token service for generating and managing cryptographically secure tokens.

Provides secure token generation using Python's secrets module and
SHA-256 hashing for storage. Only hashed tokens are stored in the database.
"""

import secrets
import hashlib
from typing import Optional, Tuple


class TokenService:
    """Service for generating and managing cryptographically secure tokens.

    Uses Python's secrets module for cryptographically secure random number
    generation and SHA-256 for one-way hashing of tokens before storage.

    Raw tokens are NEVER stored in the database - only their SHA-256 hashes.

    Attributes:
        default_length: Default token length in bytes (default 32).
    """

    def __init__(self, default_length: int = 32):
        """Initialize TokenService.

        Args:
            default_length: Default token length in bytes (default 32).
        """
        self.default_length = default_length

    def generate_token(self, length: Optional[int] = None) -> str:
        """Generate a cryptographically secure random token.

        Uses secrets.token_urlsafe() for URL-safe base64 encoding.
        The token contains sufficient entropy for secure session management.

        Args:
            length: Token length in bytes. If None, uses default_length.

        Returns:
            URL-safe base64 encoded random token string.

        Raises:
            ValueError: If length is less than 16.
        """
        if length is None:
            length = self.default_length
        if length < 16:
            raise ValueError("Token length must be at least 16 bytes")
        return secrets.token_urlsafe(length)

    def hash_token(self, token: str) -> str:
        """Hash a token using SHA-256 for secure storage.

        The hash is a one-way transformation - the original token cannot
        be recovered from the hash.

        Args:
            token: The token to hash.

        Returns:
            Hexadecimal SHA-256 hash of the token (64 characters).

        Raises:
            ValueError: If token is empty or None.
        """
        if not token:
            raise ValueError("Token cannot be empty")
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def get_token_hash_prefix(self, token_hash: str) -> str:
        """Get the first 8 characters of a token hash for fast lookup.

        This prefix is used for performance optimization when looking up
        tokens in the database without requiring Redis or other external
        services.

        Args:
            token_hash: The SHA-256 hash of a token (64 characters).

        Returns:
            First 8 characters of the hash.

        Raises:
            ValueError: If token_hash is not 64 characters.
        """
        if len(token_hash) != 64:
            raise ValueError("Token hash must be 64 characters (SHA-256)")
        return token_hash[:8]

    def generate_token_and_hash(self, length: Optional[int] = None) -> Tuple[str, str, str]:
        """Generate a token, its hash, and hash prefix in one operation.

        Convenience method that generates a token and immediately computes
        its hash and prefix for database storage.

        Args:
            length: Token length in bytes. If None, uses default_length.

        Returns:
            Tuple of (token, token_hash, token_hash_prefix).

        Note:
            The token should be stored securely (e.g., in an HttpOnly cookie)
            and NOT in the database. Only token_hash and token_hash_prefix
            should be stored in the database.
        """
        token = self.generate_token(length)
        token_hash = self.hash_token(token)
        token_hash_prefix = self.get_token_hash_prefix(token_hash)
        return token, token_hash, token_hash_prefix

    def validate_token(self, token: str, stored_hash: str) -> bool:
        """Validate a token against a stored hash.

        Hashes the provided token and compares it to the stored hash.

        Args:
            token: The token to validate.
            stored_hash: The stored SHA-256 hash to compare against.

        Returns:
            True if the token's hash matches the stored hash, False otherwise.
        """
        try:
            computed_hash = self.hash_token(token)
            # Use secrets.compare_digest for constant-time comparison
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    def validate_token_by_prefix(self, token: str, prefix: str, stored_hash: str) -> bool:
        """Validate a token by first checking its hash prefix.

        This is a performance optimization that allows for fast rejection
        of tokens with non-matching prefixes before computing the full hash.

        Args:
            token: The token to validate.
            prefix: The expected token hash prefix (first 8 chars).
            stored_hash: The stored SHA-256 hash to compare against.

        Returns:
            True if the token's hash matches the stored hash and prefix,
            False otherwise.
        """
        try:
            computed_hash = self.hash_token(token)
            computed_prefix = computed_hash[:8]

            # Quick rejection if prefix doesn't match
            if not secrets.compare_digest(computed_prefix, prefix):
                return False

            # Full hash comparison
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

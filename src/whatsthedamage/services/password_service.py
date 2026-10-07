"""Password service for secure password hashing and verification.

Uses Argon2id algorithm with OWASP-recommended parameters for secure
password storage. Provides one-way hashing and verification operations.
"""

from argon2 import PasswordHasher, exceptions
from argon2.low_level import Type
from typing import Any, Optional, cast


class PasswordService:
    """Service for secure password hashing and verification.

    Uses Argon2id algorithm (OWASP recommended) with configurable parameters
    for memory-hard, GPU/ASIC-resistant password hashing.

    Argon2id parameters (defaults):
        time_cost: 3 - Number of iterations
        memory_cost: 65536 - 64MB of memory usage
        parallelism: 4 - Number of parallel threads
        hash_len: 32 - Length of the hash in bytes
        salt_len: 16 - Length of the salt in bytes
        type: Type.ID - Argon2id variant

    Attributes:
        hasher: Argon2 PasswordHasher instance.
    """

    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16,
        type: Type = Type.ID
    ):
        """Initialize PasswordService with Argon2id configuration.

        Args:
            time_cost: Number of iterations for Argon2 (default 3).
            memory_cost: Memory usage in KiB (default 65536 = 64MB).
            parallelism: Number of parallel threads (default 4).
            hash_len: Length of the hash in bytes (default 32).
            salt_len: Length of the salt in bytes (default 16).
            type: Argon2 type (default Type.ID for Argon2id).
        """
        self.hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len,
            type=type
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2id.

        Generates a secure, salted hash of the password using Argon2id.
        The resulting hash includes the salt and parameters, allowing for
        verification without storing them separately.

        Args:
            password: Plain text password to hash.

        Returns:
            Argon2id hashed password string.

        Raises:
            ValueError: If password is empty or None.
        """
        if not password:
            raise ValueError("Password cannot be empty")
        return self.hasher.hash(password)  # type: ignore[no-any-return]

    def verify_password(self, password: str, hash: str) -> bool:
        """Verify a password against a stored Argon2id hash.

        Constant-time comparison is used internally by argon2-cffi to
        prevent timing attacks.

        Args:
            password: Plain text password to verify.
            hash: Stored Argon2id hash to verify against.

        Returns:
            True if password matches the hash, False otherwise.

        Raises:
            ValueError: If password or hash is empty or None.
        """
        if not password or not hash:
            return False
        try:
            self.hasher.verify(hash, password)
            return True
        except exceptions.VerifyMismatchError:
            return False
        except exceptions.VerificationError:
            # Invalid hash format or verification error
            return False
        except exceptions.InvalidHashError:
            # Invalid hash format
            return False

    def needs_rehash(self, hash: str) -> bool:
        """Check if a hash needs to be rehashed with updated parameters.

        Useful for rotating password hashes when parameters are updated.

        Args:
            hash: Stored Argon2id hash to check.

        Returns:
            True if the hash should be rehashed, False otherwise.
        """
        try:
            return self.hasher.check_needs_rehash(hash)  # type: ignore[no-any-return]
        except (exceptions.VerificationError, exceptions.InvalidHashError, ValueError):
            # Invalid hash format - needs rehash
            return True

    def get_hash_info(self, hash: str) -> Optional[dict[str, Any]]:
        """Extract information from a stored hash.

        Args:
            hash: Stored Argon2id hash.

        Returns:
            Dictionary with hash information (type, time_cost, memory_cost,
            parallelism, hash_len, salt_len) or None if invalid.
        """
        try:
            # Argon2 hash format: $argon2id$v=19$m=65536,t=3,p=4$...$...
            parts = hash.split('$')
            if len(parts) < 6:
                return None

            info: dict[str, Any] = {'type': parts[1]}

            # Parse version
            if '=' in parts[2]:
                info['version'] = parts[2].split('=')[1]

            # Parse parameters (m, t, p)
            params_part = parts[3]
            param_pairs = params_part.split(',')
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=')
                    if key == 'm':
                        info['memory_cost'] = int(value)
                    elif key == 't':
                        info['time_cost'] = int(value)
                    elif key == 'p':
                        info['parallelism'] = int(value)

            return info
        except Exception:
            return None

"""Rate limiting service for login attempt limiting.

Provides application-level rate limiting using in-memory storage via
Flask-Limiter. Protects against credential stuffing and brute force attacks.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple, cast
from collections import defaultdict
from threading import Lock


class RateLimitService:
    """Service for rate limiting API requests.

    Implements application-level rate limiting with in-memory storage.
    Tracks attempts per bucket key (username+IP, IP address).

    Rate Limiting Configuration:
        - Login: 5 attempts per 15 minutes per username+IP
        - Password recovery: 5 attempts per 15 minutes per IP
        - Registration: 5 attempts per 15 minutes per IP
        - General API: configurable (default 300 per 60 seconds per IP)
        - Storage: In-memory dictionary (no Redis dependency for US-1)

    Attributes:
        max_attempts: Maximum number of attempts allowed.
        window_seconds: Rate limit window in seconds.
        storage: Dictionary to store attempt counts.
        lock: Thread lock for thread-safe access.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900  # 15 minutes
    ):
        """Initialize RateLimitService.

        Args:
            max_attempts: Maximum number of attempts allowed (default 5).
            window_seconds: Rate limit window in seconds (default 900 = 15 minutes).
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.storage: dict[str, dict[str, Any]] = defaultdict(lambda: {'attempts': 0, 'start_time': 0.0, 'expires_at': 0.0})
        self.lock = Lock()

    def _make_key(self, username: str, ip_address: str) -> str:
        """Create a composite key for username+IP combination.

        Args:
            username: Username.
            ip_address: Client IP address.

        Returns:
            Composite key string.
        """
        return f"{username.lower()}:{ip_address}"

    def _cleanup_expired(self) -> None:
        """Remove expired entries from storage.

        Called automatically during check operations.
        """
        current_time = time.time()
        keys_to_remove = []

        for key, data in self.storage.items():
            if data.get('expires_at', 0) < current_time:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.storage[key]

    def _check_bucket(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """Check and increment a named rate limit bucket.

        Records one attempt in the bucket identified by key and reports
        whether the allowed attempt count has been exhausted.

        Args:
            key: Storage key identifying the bucket.
            max_attempts: Maximum attempts allowed in the window.
            window_seconds: Window length in seconds.

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds).
            - is_rate_limited: True if rate limit is exceeded.
            - retry_after_seconds: Seconds until the rate limit resets.
        """
        current_time = time.time()

        with self.lock:
            # Cleanup expired entries periodically
            if len(self.storage) > 100 and len(self.storage) % 50 == 0:
                self._cleanup_expired()

            # Get or create entry
            entry = self.storage.get(key)
            if entry is None:
                self.storage[key] = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + window_seconds
                }
                return False, 0

            # Check if window has expired
            if current_time > entry['expires_at']:
                # Reset the window
                self.storage[key] = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + window_seconds
                }
                return False, 0

            # Check if limit exceeded
            if entry['attempts'] >= max_attempts:
                retry_after = int(entry['expires_at'] - current_time)
                if retry_after < 0:
                    retry_after = 0
                return True, retry_after

            # Increment attempt count
            entry['attempts'] += 1
            self.storage[key] = entry
            return False, 0

    def check_login_rate_limit(
        self,
        username: str,
        ip_address: str
    ) -> Tuple[bool, int]:
        """Check if rate limit is exceeded for login attempts.

        Tracks attempts per username+IP combination and returns whether
        the limit has been exceeded.

        Args:
            username: Username being authenticated.
            ip_address: Client IP address.

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds).
            - is_rate_limited: True if rate limit is exceeded.
            - retry_after_seconds: Seconds until the rate limit resets.
        """
        key = self._make_key(username, ip_address)
        return self._check_bucket(
            key, self.max_attempts, self.window_seconds
        )

    def reset_rate_limit(self, username: str, ip_address: str) -> None:
        """Reset the rate limit counter for a username+IP combination.

        Useful for resetting after successful authentication or
        administrative override.

        Args:
            username: Username to reset.
            ip_address: Client IP address to reset.
        """
        key = self._make_key(username, ip_address)
        with self.lock:
            if key in self.storage:
                del self.storage[key]

    def get_remaining_attempts(self, username: str, ip_address: str) -> int:
        """Get the number of remaining attempts for a username+IP combination.

        Args:
            username: Username to check.
            ip_address: Client IP address to check.

        Returns:
            Number of remaining attempts, or max_attempts if no limit is active.
        """
        key = self._make_key(username, ip_address)
        current_time = time.time()

        with self.lock:
            entry = self.storage.get(key)
            if entry is None:
                return self.max_attempts

            # Check if window has expired
            if current_time > entry['expires_at']:
                return self.max_attempts

            attempts = cast(int, entry['attempts'])
            remaining = max(0, self.max_attempts - attempts)
            return remaining

    def get_attempts(self, username: str, ip_address: str) -> int:
        """Get the current number of attempts for a username+IP combination.

        Args:
            username: Username to check.
            ip_address: Client IP address to check.

        Returns:
            Number of attempts in the current window.
        """
        key = self._make_key(username, ip_address)

        with self.lock:
            entry = self.storage.get(key)
            if entry is None:
                return 0

            current_time = time.time()
            # Check if window has expired
            if current_time > entry['expires_at']:
                return 0

            attempts = cast(int, entry['attempts'])
            return attempts

    def check_recovery_rate_limit(
        self,
        ip_address: str
    ) -> Tuple[bool, int]:
        """Check if rate limit is exceeded for password recovery attempts.

        Tracks attempts per IP address (username may not be valid).
        Uses same configuration as login rate limiting.

        Args:
            ip_address: Client IP address.

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds).
            - is_rate_limited: True if rate limit is exceeded.
            - retry_after_seconds: Seconds until the rate limit resets.
        """
        key = f"recovery:{ip_address}"
        return self._check_bucket(
            key, self.max_attempts, self.window_seconds
        )

    def check_register_rate_limit(
        self,
        ip_address: str
    ) -> Tuple[bool, int]:
        """Check if rate limit is exceeded for registration attempts.

        Tracks attempts per IP address to prevent bulk account
        creation. Uses same configuration as login rate limiting.

        Args:
            ip_address: Client IP address.

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds).
            - is_rate_limited: True if rate limit is exceeded.
            - retry_after_seconds: Seconds until the rate limit resets.
        """
        key = f"register:{ip_address}"
        return self._check_bucket(
            key, self.max_attempts, self.window_seconds
        )

    def check_api_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """Check if the general API rate limit is exceeded.

        Tracks requests per identifier (typically the client IP,
        optionally prefixed to separate buckets such as heavy
        endpoints). Limits are passed by the caller because they are
        configured per bucket in the Flask configuration.

        Args:
            identifier: Bucket identifier (e.g. client IP address).
            max_requests: Maximum requests allowed in the window.
            window_seconds: Window length in seconds.

        Returns:
            Tuple of (is_rate_limited, retry_after_seconds).
            - is_rate_limited: True if rate limit is exceeded.
            - retry_after_seconds: Seconds until the rate limit resets.
        """
        key = f"api:{identifier}"
        return self._check_bucket(key, max_requests, window_seconds)

    def reset_api_rate_limit(self, identifier: str) -> None:
        """Reset the general API rate limit counter for an identifier.

        Args:
            identifier: Bucket identifier to reset.
        """
        key = f"api:{identifier}"
        with self.lock:
            if key in self.storage:
                del self.storage[key]

    def reset_recovery_rate_limit(self, ip_address: str) -> None:
        """Reset the rate limit counter for password recovery attempts.

        Args:
            ip_address: Client IP address to reset.
        """
        key = f"recovery:{ip_address}"
        with self.lock:
            if key in self.storage:
                del self.storage[key]

    def get_remaining_recovery_attempts(self, ip_address: str) -> int:
        """Get the number of remaining recovery attempts for an IP address.

        Args:
            ip_address: Client IP address to check.

        Returns:
            Number of remaining attempts, or max_attempts if no limit is active.
        """
        key = f"recovery:{ip_address}"
        current_time = time.time()

        with self.lock:
            entry = self.storage.get(key)
            if entry is None:
                return self.max_attempts

            # Check if window has expired
            if current_time > entry['expires_at']:
                return self.max_attempts

            attempts = cast(int, entry['attempts'])
            remaining = max(0, self.max_attempts - attempts)
            return remaining

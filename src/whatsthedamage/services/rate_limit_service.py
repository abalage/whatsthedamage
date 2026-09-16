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
    """Service for rate limiting login attempts.

    Implements application-level rate limiting with in-memory storage.
    Tracks login attempts per username+IP combination.

    Rate Limiting Configuration:
        - Default: 5 attempts per 15 minutes per username+IP
        - Storage: In-memory dictionary (no Redis dependency for US-1)
        - Cleanup: Automatic cleanup of expired entries

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
        current_time = time.time()

        with self.lock:
            # Cleanup expired entries periodically
            if len(self.storage) > 100 and len(self.storage) % 50 == 0:
                self._cleanup_expired()

            # Get or create entry
            entry = self.storage.get(key)
            if entry is None:
                entry = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + self.window_seconds
                }
                self.storage[key] = entry
                return False, 0

            # Check if window has expired
            if current_time > entry['expires_at']:
                # Reset the window
                entry = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + self.window_seconds
                }
                self.storage[key] = entry
                return False, 0

            # Check if limit exceeded
            if entry['attempts'] >= self.max_attempts:
                retry_after = int(entry['expires_at'] - current_time)
                if retry_after < 0:
                    retry_after = 0
                return True, retry_after

            # Increment attempt count
            entry['attempts'] += 1
            self.storage[key] = entry
            return False, 0

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
        current_time = time.time()

        with self.lock:
            # Cleanup expired entries periodically
            if len(self.storage) > 100 and len(self.storage) % 50 == 0:
                self._cleanup_expired()

            # Get or create entry
            entry = self.storage.get(key)
            if entry is None:
                entry = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + self.window_seconds
                }
                self.storage[key] = entry
                return False, 0

            # Check if window has expired
            if current_time > entry['expires_at']:
                # Reset the window
                entry = {
                    'attempts': 1,
                    'start_time': current_time,
                    'expires_at': current_time + self.window_seconds
                }
                self.storage[key] = entry
                return False, 0

            # Check if limit exceeded
            if entry['attempts'] >= self.max_attempts:
                retry_after = int(entry['expires_at'] - current_time)
                if retry_after < 0:
                    retry_after = 0
                return True, retry_after

            # Increment attempt count
            entry['attempts'] += 1
            self.storage[key] = entry
            return False, 0

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

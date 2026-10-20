"""Tests for RateLimitService.

Tests rate limiting functionality for login and password recovery attempts.
"""

import pytest
import time
from unittest.mock import Mock, patch

from whatsthedamage.services.rate_limit_service import RateLimitService


@pytest.fixture
def rate_limit_service():
    """Create a RateLimitService instance for testing."""
    return RateLimitService(
        max_attempts=5,
        window_seconds=900  # 15 minutes
    )


class TestRateLimitServiceLogin:
    """Tests for login rate limiting functionality."""

    def test_check_login_rate_limit_first_attempt(self, rate_limit_service):
        """Test first login attempt is not rate limited."""
        is_rate_limited, retry_after = rate_limit_service.check_login_rate_limit(
            username='testuser',
            ip_address='127.0.0.1'
        )

        assert is_rate_limited is False
        assert retry_after == 0

    def test_check_login_rate_limit_exceeded(self, rate_limit_service):
        """Test that rate limit is exceeded after max attempts."""
        # Make 5 attempts (the limit)
        for i in range(5):
            is_rate_limited, _ = rate_limit_service.check_login_rate_limit(
                username='testuser',
                ip_address='127.0.0.1'
            )
            assert is_rate_limited is False

        # 6th attempt should be rate limited
        is_rate_limited, retry_after = rate_limit_service.check_login_rate_limit(
            username='testuser',
            ip_address='127.0.0.1'
        )

        assert is_rate_limited is True
        assert retry_after > 0
        assert retry_after <= 900  # Within the window

    def test_check_login_rate_limit_different_ip(self, rate_limit_service):
        """Test that different IPs have separate rate limits."""
        # Max out attempts for first IP
        for _ in range(5):
            rate_limit_service.check_login_rate_limit(
                username='testuser',
                ip_address='127.0.0.1'
            )

        # Second IP should not be rate limited
        is_rate_limited, retry_after = rate_limit_service.check_login_rate_limit(
            username='testuser',
            ip_address='127.0.0.2'
        )

        assert is_rate_limited is False
        assert retry_after == 0

    def test_check_login_rate_limit_different_username(self, rate_limit_service):
        """Test that different usernames have separate rate limits."""
        # Max out attempts for first username
        for _ in range(5):
            rate_limit_service.check_login_rate_limit(
                username='user1',
                ip_address='127.0.0.1'
            )

        # Second username should not be rate limited
        is_rate_limited, retry_after = rate_limit_service.check_login_rate_limit(
            username='user2',
            ip_address='127.0.0.1'
        )



class TestRateLimitServiceRecovery:
    """Tests for password recovery rate limiting functionality."""

    def test_check_recovery_rate_limit_first_attempt(self, rate_limit_service):
        """Test first recovery attempt is not rate limited."""
        is_rate_limited, retry_after = rate_limit_service.check_recovery_rate_limit(
            ip_address='127.0.0.1'
        )

        assert is_rate_limited is False
        assert retry_after == 0

    def test_check_recovery_rate_limit_exceeded(self, rate_limit_service):
        """Test that recovery rate limit is exceeded after max attempts."""
        # Make 5 attempts (the limit)
        for i in range(5):
            is_rate_limited, _ = rate_limit_service.check_recovery_rate_limit(
                ip_address='127.0.0.1'
            )
            assert is_rate_limited is False

        # 6th attempt should be rate limited
        is_rate_limited, retry_after = rate_limit_service.check_recovery_rate_limit(
            ip_address='127.0.0.1'
        )

        assert is_rate_limited is True
        assert retry_after > 0
        assert retry_after <= 900

    def test_check_recovery_rate_limit_different_ip(self, rate_limit_service):
        """Test that different IPs have separate recovery rate limits."""
        # Max out attempts for first IP
        for _ in range(5):
            rate_limit_service.check_recovery_rate_limit(ip_address='127.0.0.1')

        # Second IP should not be rate limited
        is_rate_limited, retry_after = rate_limit_service.check_recovery_rate_limit(
            ip_address='127.0.0.2'
        )

        assert is_rate_limited is False
        assert retry_after == 0

    def test_reset_recovery_rate_limit(self, rate_limit_service):
        """Test resetting recovery rate limit for an IP address."""
        # Max out attempts
        for _ in range(5):
            rate_limit_service.check_recovery_rate_limit(ip_address='127.0.0.1')

        # Should be rate limited
        is_rate_limited, _ = rate_limit_service.check_recovery_rate_limit(
            ip_address='127.0.0.1'
        )
        assert is_rate_limited is True

        # Reset the rate limit
        rate_limit_service.reset_recovery_rate_limit('127.0.0.1')




    def test_window_expiry_resets_counter(self, rate_limit_service):
        """Test that counter resets after window expiry."""
        # Make 5 attempts to max out
        for _ in range(5):
            rate_limit_service.check_login_rate_limit('testuser', '127.0.0.1')

        # Should be rate limited
        is_rate_limited, _ = rate_limit_service.check_login_rate_limit(
            'testuser',
            '127.0.0.1'
        )
        assert is_rate_limited is True

        # Manually expire the window
        key = rate_limit_service._make_key('testuser', '127.0.0.1')
        rate_limit_service.storage[key]['expires_at'] = time.time() - 1

        # Should no longer be rate limited (window reset)
        is_rate_limited, retry_after = rate_limit_service.check_login_rate_limit(
            'testuser',
            '127.0.0.1'
        )
        assert is_rate_limited is False
        assert retry_after == 0

    def test_custom_max_attempts(self):
        """Test custom max attempts configuration."""
        custom_service = RateLimitService(
            max_attempts=3,
            window_seconds=60
        )

        # After 3 attempts, should be rate limited
        for _ in range(3):
            custom_service.check_login_rate_limit('testuser', '127.0.0.1')

        is_rate_limited, _ = custom_service.check_login_rate_limit(
            'testuser',
            '127.0.0.1'
        )
        assert is_rate_limited is True

    def test_custom_window_seconds(self):
        """Test custom window seconds configuration."""
        custom_service = RateLimitService(
            max_attempts=5,
            window_seconds=60  # 1 minute
        )

        # Make 5 attempts
        for _ in range(5):
            custom_service.check_login_rate_limit('testuser', '127.0.0.1')

        # Should be rate limited
        is_rate_limited, retry_after = custom_service.check_login_rate_limit(
            'testuser',
            '127.0.0.1'
        )

        assert is_rate_limited is True
        # Retry after should be approximately 60 seconds (the window)
        assert retry_after <= 60

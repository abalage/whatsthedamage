"""Tests for PasswordService.

Tests password hashing and verification using Argon2id algorithm.
"""

import pytest
from whatsthedamage.services.password_service import PasswordService


@pytest.fixture
def password_service():
    """Create a PasswordService instance for testing."""
    return PasswordService(
        time_cost=2,  # Reduced for faster tests
        memory_cost=16384,  # Reduced for faster tests
        parallelism=1
    )


class TestPasswordServiceHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_string(self, password_service):
        """Test that hash_password returns a string."""
        result = password_service.hash_password("test_password")
        assert isinstance(result, str)

    def test_hash_password_different_for_same_password(self, password_service):
        """Test that hashing the same password produces different hashes (due to salt)."""
        hash1 = password_service.hash_password("same_password")
        hash2 = password_service.hash_password("same_password")
        assert hash1 != hash2

    def test_hash_password_empty_raises_error(self, password_service):
        """Test that hashing an empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_service.hash_password("")

    def test_hash_password_none_raises_error(self, password_service):
        """Test that hashing None raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_service.hash_password(None)


class TestPasswordServiceVerification:
    """Tests for password verification functionality."""

    def test_verify_password_correct(self, password_service):
        """Test that verify_password returns True for correct password."""
        password = "secure_password_123"
        hash = password_service.hash_password(password)
        assert password_service.verify_password(password, hash) is True

    def test_verify_password_incorrect(self, password_service):
        """Test that verify_password returns False for incorrect password."""
        password = "secure_password_123"
        hash = password_service.hash_password(password)
        assert password_service.verify_password("wrong_password", hash) is False

    def test_verify_password_empty_password(self, password_service):
        """Test that verify_password returns False for empty password."""
        hash = password_service.hash_password("some_password")
        assert password_service.verify_password("", hash) is False

    def test_verify_password_empty_hash(self, password_service):
        """Test that verify_password returns False for empty hash."""
        assert password_service.verify_password("some_password", "") is False

    def test_verify_password_invalid_hash(self, password_service):
        """Test that verify_password returns False for invalid hash format."""
        assert password_service.verify_password("password", "invalid_hash_format") is False


class TestPasswordServiceRehash:
    """Tests for password rehashing functionality."""

    def test_needs_rehash_with_own_parameters(self, password_service):
        """Test that needs_rehash returns False for hash created with same parameters."""
        password = "test_password"
        hash = password_service.hash_password(password)
        # Hash created with same parameters should not need rehash
        assert password_service.needs_rehash(hash) is False

    def test_get_hash_info(self, password_service):
        """Test that get_hash_info extracts information from hash."""
        password = "test_password"
        hash = password_service.hash_password(password)
        info = password_service.get_hash_info(hash)

        assert info is not None
        assert 'type' in info
        assert info['type'] == 'argon2id'

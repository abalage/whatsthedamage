"""Tests for TokenService.

Tests token generation, hashing, and validation.
"""

import pytest
from whatsthedamage.services.token_service import TokenService


@pytest.fixture
def token_service():
    """Create a TokenService instance for testing."""
    return TokenService(default_length=32)


class TestTokenGeneration:
    """Tests for token generation functionality."""

    def test_generate_token_returns_string(self, token_service):
        """Test that generate_token returns a string."""
        token = token_service.generate_token()
        assert isinstance(token, str)

    def test_generate_token_length(self, token_service):
        """Test that generated token has correct length."""
        # URL-safe base64 encoding: 32 bytes = ~43 characters
        token = token_service.generate_token()
        # Decode to check byte length
        import base64
        # URL-safe base64 may have padding removed
        decoded = base64.urlsafe_b64decode(token + '===')
        # Should be at least 32 bytes (may be more due to padding)
        assert len(decoded) >= 32

    def test_generate_token_custom_length(self, token_service):
        """Test that custom length tokens are generated."""
        token = token_service.generate_token(16)
        import base64
        decoded = base64.urlsafe_b64decode(token + '===')
        assert len(decoded) >= 16

    def test_generate_token_minimum_length(self, token_service):
        """Test that minimum token length is enforced."""
        with pytest.raises(ValueError, match="Token length must be at least 16 bytes"):
            token_service.generate_token(8)

    def test_generate_token_unique(self, token_service):
        """Test that generated tokens are unique."""
        token1 = token_service.generate_token()
        token2 = token_service.generate_token()
        assert token1 != token2


class TestTokenHashing:
    """Tests for token hashing functionality."""

    def test_hash_token_returns_64_char_hex(self, token_service):
        """Test that hash_token returns 64 character hex string."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        assert isinstance(hash, str)
        assert len(hash) == 64
        # Check it's hexadecimal
        assert all(c in '0123456789abcdef' for c in hash)

    def test_hash_token_empty_raises_error(self, token_service):
        """Test that hashing empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            token_service.hash_token("")

    def test_hash_token_same_for_same_token(self, token_service):
        """Test that same token produces same hash."""
        token = "test_token_string"
        hash1 = token_service.hash_token(token)
        hash2 = token_service.hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_for_different_tokens(self, token_service):
        """Test that different tokens produce different hashes."""
        hash1 = token_service.hash_token("token_1")
        hash2 = token_service.hash_token("token_2")
        assert hash1 != hash2


class TestTokenHashPrefix:
    """Tests for token hash prefix functionality."""

    def test_get_prefix_returns_8_chars(self, token_service):
        """Test that get_token_hash_prefix returns 8 characters."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        prefix = token_service.get_token_hash_prefix(hash)
        assert len(prefix) == 8

    def test_get_prefix_is_first_8_chars(self, token_service):
        """Test that prefix is first 8 characters of hash."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        prefix = token_service.get_token_hash_prefix(hash)
        assert prefix == hash[:8]

    def test_get_prefix_invalid_length_raises_error(self, token_service):
        """Test that invalid hash length raises ValueError."""
        with pytest.raises(ValueError, match="Token hash must be 64 characters"):
            token_service.get_token_hash_prefix("short")


class TestTokenAndHashGeneration:
    """Tests for combined token and hash generation."""

    def test_generate_token_and_hash_returns_tuple(self, token_service):
        """Test that generate_token_and_hash returns 3 values."""
        result = token_service.generate_token_and_hash()
        assert len(result) == 3
        token, hash, prefix = result
        assert isinstance(token, str)
        assert isinstance(hash, str)
        assert isinstance(prefix, str)

    def test_generate_token_and_hash_consistency(self, token_service):
        """Test that generated token, hash, and prefix are consistent."""
        token, hash, prefix = token_service.generate_token_and_hash()
        assert hash == token_service.hash_token(token)
        assert prefix == token_service.get_token_hash_prefix(hash)
        assert prefix == hash[:8]


class TestTokenValidation:
    """Tests for token validation functionality."""

    def test_validate_token_correct(self, token_service):
        """Test that validate_token returns True for correct token."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        assert token_service.validate_token(token, hash) is True

    def test_validate_token_incorrect(self, token_service):
        """Test that validate_token returns False for incorrect token."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        assert token_service.validate_token("wrong_token", hash) is False

    def test_validate_token_by_prefix_correct(self, token_service):
        """Test that validate_token_by_prefix returns True for correct token."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        prefix = token_service.get_token_hash_prefix(hash)
        assert token_service.validate_token_by_prefix(token, prefix, hash) is True

    def test_validate_token_by_prefix_wrong_prefix(self, token_service):
        """Test that validate_token_by_prefix returns False for wrong prefix."""
        token = token_service.generate_token()
        hash = token_service.hash_token(token)
        assert token_service.validate_token_by_prefix(token, "wrongxxx", hash) is False

"""Unit tests for TextCorrectionService."""

import pytest
from whatsthedamage.services.text_correction_service import TextCorrectionService
from whatsthedamage.config.text_config import TextCleaningConfig

class TestTextCorrectionService:
    """Focused unit tests for TextCorrectionService."""

    @pytest.fixture
    def service(self) -> TextCorrectionService:
        """Default service with both features enabled."""
        return TextCorrectionService(TextCleaningConfig())

    @pytest.fixture
    def service_unicode_only(self) -> TextCorrectionService:
        """Service with only unicode normalization."""
        return TextCorrectionService(TextCleaningConfig(
            unicode_normalization=True,
            whitespace_cleaning=False
        ))

    @pytest.fixture
    def service_whitespace_only(self) -> TextCorrectionService:
        """Service with only whitespace cleaning."""
        return TextCorrectionService(TextCleaningConfig(
            unicode_normalization=False,
            whitespace_cleaning=True
        ))

    def test_initialization(self, service: TextCorrectionService) -> None:
        """Test basic service initialization."""
        assert service is not None
        assert service.config.unicode_normalization
        assert service.config.whitespace_cleaning

    @pytest.mark.parametrize("input_text,expected", [
        ("TATABÁNYA", "TATABÁNYA"),  # Combined character normalization
        ("café", "café"),             # Already normalized
        ("naïve", "naïve"),           # Another normalization case
    ])
    def test_unicode_normalization(self, service: TextCorrectionService, input_text: str, expected: str) -> None:
        """Test Unicode NFKC normalization with parametrized cases."""
        result = service.clean_partner_field(input_text)
        assert result == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("  test  ", "test"),                    # Multiple spaces
        ("test\t\tstring", "test string"),      # Tabs
        ("  \t mixed  \t  ", "mixed"),          # Mixed whitespace
    ])
    def test_whitespace_cleaning(self, service: TextCorrectionService, input_text: str, expected: str) -> None:
        """Test whitespace cleaning with parametrized cases."""
        result = service.clean_partner_field(input_text)
        assert result == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("  TATABÁNYA  ", "TATABÁNYA"),      # Both normalization and cleaning
        ("  café  \t", "café"),              # Another combined case
        ("naïve  \t  test", "naïve test"),   # Mixed case
    ])
    def test_combined_operations(self, service: TextCorrectionService, input_text: str, expected: str) -> None:
        """Test combined normalization and cleaning with parametrized cases."""
        result = service.clean_partner_field(input_text)
        assert result == expected

    def test_configuration_options(self, service_unicode_only: TextCorrectionService, service_whitespace_only: TextCorrectionService) -> None:
        """Test different configuration combinations."""
        test_input = "  TATABÁNYA  "

        # Unicode only should preserve spaces
        result_unicode = service_unicode_only.clean_partner_field(test_input)
        assert result_unicode == "  TATABÁNYA  "  # Normalized, spaces preserved

        # Whitespace only should not normalize
        result_whitespace = service_whitespace_only.clean_partner_field(test_input)
        assert result_whitespace == "TATABÁNYA"  # Spaces cleaned, not normalized

    @pytest.mark.parametrize("input_text,expected", [
        ("", ""),                              # Empty string
        ("   ", ""),                           # Only spaces
        ("test", "test"),                     # Already clean
        ("a", "a"),                           # Single character
    ])
    def test_edge_cases(self, service: TextCorrectionService, input_text: str, expected: str) -> None:
        """Test edge cases with parametrized inputs."""
        result = service.clean_partner_field(input_text)
        assert result == expected

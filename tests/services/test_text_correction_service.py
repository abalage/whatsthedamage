"""Unit tests for TextCorrectionService."""

import pytest
from whatsthedamage.services.text_correction_service import TextCorrectionService
from whatsthedamage.config.text_config import TextCleaningConfig, TextCleaningPatternsConfig

class TestTextCorrectionService:
    """Focused unit tests for TextCorrectionService."""

    @pytest.fixture
    def service(self) -> TextCorrectionService:
        """Default service with both features enabled."""
        patterns_config = TextCleaningPatternsConfig(
            payment_providers=['^OTPMOBL\\s*', '^PAYPAL\\s*', '^CRV\\s*'],
            company_suffixes=['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b'],
            buggy_partner_replacements={'e lelmisz': 'Élelmisz'}
        )
        return TextCorrectionService(TextCleaningConfig(), patterns_config)

    @pytest.fixture
    def service_unicode_only(self) -> TextCorrectionService:
        """Service with only unicode normalization."""
        patterns_config = TextCleaningPatternsConfig()
        return TextCorrectionService(TextCleaningConfig(
            unicode_normalization=True,
            whitespace_cleaning=False
        ), patterns_config)

    @pytest.fixture
    def service_whitespace_only(self) -> TextCorrectionService:
        """Service with only whitespace cleaning."""
        patterns_config = TextCleaningPatternsConfig()
        return TextCorrectionService(TextCleaningConfig(
            unicode_normalization=False,
            whitespace_cleaning=True
        ), patterns_config)

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

        # Unicode only should preserve spaces (but now also applies ML cleaning by default)
        result_unicode = service_unicode_only.clean_partner_field(test_input)
        assert result_unicode == "TATABÁNYA"  # Normalized, spaces cleaned, ML cleaning applied

        # Whitespace only should not normalize (but now also applies ML cleaning by default)
        result_whitespace = service_whitespace_only.clean_partner_field(test_input)
        assert result_whitespace == "TATABÁNYA"  # Spaces cleaned, not normalized (unicode_normalization=False), ML cleaning applied

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

    def test_ml_cleaning_configuration(self):
        """Test ML-specific cleaning configuration flags."""
        # Test basic cleaning (explicitly disable ML flags)
        basic_config = TextCleaningConfig(
            remove_payment_providers=False,
            remove_hungarian_suffixes=False
        )
        patterns_config = TextCleaningPatternsConfig(
            payment_providers=['^OTPMOBL\\s*', '^PAYPAL\\s*'],
            company_suffixes=['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        )
        basic_service = TextCorrectionService(basic_config, patterns_config)
        result_basic = basic_service.clean_partner_field('OTPMOBL test kft')
        assert result_basic == 'OTPMOBL test kft'  # No ML cleaning applied

        # Test ML cleaning via configuration flags (default behavior)
        ml_config = TextCleaningConfig()  # Default has ML cleaning enabled
        ml_service = TextCorrectionService(ml_config, patterns_config)
        result_ml = ml_service.clean_partner_field('OTPMOBL test kft')
        assert result_ml == 'test'  # Both payment provider and suffix removed

        # Test partial ML cleaning - only payment providers
        partial_config = TextCleaningConfig(
            remove_payment_providers=True,
            remove_hungarian_suffixes=False
        )
        partial_service = TextCorrectionService(partial_config, patterns_config)
        result_partial = partial_service.clean_partner_field('OTPMOBL test kft')
        assert result_partial == 'test kft'  # Only payment provider removed

        # Test partial ML cleaning - only Hungarian suffixes
        suffix_config = TextCleaningConfig(
            remove_payment_providers=False,
            remove_hungarian_suffixes=True
        )
        suffix_service = TextCorrectionService(suffix_config, patterns_config)
        result_suffix = suffix_service.clean_partner_field('OTPMOBL test kft')
        assert result_suffix == 'OTPMOBL test'  # Only suffix removed

    def test_regex_replacement_configuration(self):
        """Test regex-based partner replacement configuration."""
        # Test with regex replacements disabled
        no_regex_config = TextCleaningConfig(replace_buggy_partners=False)
        patterns_config = TextCleaningPatternsConfig(
            buggy_partner_replacements={
                r'old\s*company': 'New Company',
                r'buggy\s*partner': 'Fixed Partner',
                r'TEST\s*LTD': 'Test Corporation'
            }
        )
        no_regex_service = TextCorrectionService(no_regex_config, patterns_config)

        result_no_regex = no_regex_service.clean_partner_field('old company buggy partner')
        assert result_no_regex == 'old company buggy partner'  # No replacements applied

        # Test with regex replacements enabled
        regex_config = TextCleaningConfig(replace_buggy_partners=True)
        regex_service = TextCorrectionService(regex_config, patterns_config)

        result_with_regex = regex_service.clean_partner_field('old company buggy partner')
        assert result_with_regex == 'New Company Fixed Partner'  # Both replacements applied

        # Test case insensitivity
        result_case = regex_service.clean_partner_field('OLD COMPANY BUGGY PARTNER')
        assert result_case == 'New Company Fixed Partner'  # Case insensitive matching

        # Test mixed with other cleaning operations
        full_config = TextCleaningConfig(
            replace_buggy_partners=True,
            remove_payment_providers=True,
            remove_hungarian_suffixes=True
        )
        full_patterns_config = TextCleaningPatternsConfig(
            payment_providers=['^OTPMOBL\\s*'],
            company_suffixes=['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b'],
            buggy_partner_replacements={
                r'old\s*company': 'New Company',
                r'buggy\s*partner': 'Fixed Partner',
                r'TEST\s*LTD': 'Test Corporation'
            }
        )
        full_service = TextCorrectionService(full_config, full_patterns_config)

        result_full = full_service.clean_partner_field('OTPMOBL old company kft')
        assert result_full == 'New Company'  # Regex replacement, then payment provider and suffix removal

    def test_regex_replacement_order(self):
        """Test that regex replacements are applied before payment provider removal."""
        # Set up test replacements
        patterns_config = TextCleaningPatternsConfig(
            buggy_partner_replacements={
                r'PAYPAL\s*OLD': 'New Payment Service',
                r'TEST\s*PARTNER': 'Verified Partner'
            },
            payment_providers=['^PAYPAL\\s*']
        )

        config = TextCleaningConfig(
            replace_buggy_partners=True,
            remove_payment_providers=True
        )
        service = TextCorrectionService(config, patterns_config)

        # Test that regex replacement happens before payment provider removal
        result = service.clean_partner_field('PAYPAL OLD Service')
        assert result == 'New Payment Service Service'  # Regex replacement first, then PAYPAL prefix would be removed if it existed

        # Test complex scenario
        result_complex = service.clean_partner_field('TEST PARTNER with extra text')
        assert result_complex == 'Verified Partner with extra text'  # Only the regex replacement

    def test_empty_regex_replacements(self):
        """Test behavior when buggy_partner_replacements is empty."""
        # Create patterns config with empty replacements
        patterns_config = TextCleaningPatternsConfig(buggy_partner_replacements={})

        config = TextCleaningConfig(replace_buggy_partners=True)
        service = TextCorrectionService(config, patterns_config)

        result = service.clean_partner_field('some random text')
        assert result == 'some random text'  # No changes when dictionary is empty

    def test_regex_payment_providers(self):
        """Test that PAYMENT_PROVIDERS use raw regex patterns without escaping."""
        # Create service with payment provider removal enabled
        patterns_config = TextCleaningPatternsConfig(
            payment_providers=[
                '^OTPMOBL\\s*', '^PAYPAL\\s*', '^CRV\\s*',
                '^SUMUP\\s*', '^BARION(P)*\\s*', '^VIMPAY\\s*'
            ],
            company_suffixes=['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        )
        config = TextCleaningConfig(
            remove_payment_providers=True,
            remove_hungarian_suffixes=True
        )
        service = TextCorrectionService(config, patterns_config)

        # Test various payment provider patterns
        test_cases = [
            ('OTPMOBL Test Company', 'Test Company'),
            ('PAYPAL Payment Service Kft', 'Payment Service'),
            ('CRV Commerce Ltd', 'Commerce Ltd'),
            ('SUMUP Solutions BT', 'Solutions BT'),
            ('BARION Business', 'Business'),
            ('VIMPAY Services', 'Services'),
            ('Normal Company', 'Normal Company'),  # Should not be affected
        ]

        for input_text, expected in test_cases:
            result = service.clean_partner_field(input_text)
            assert result == expected, f"Expected '{expected}', got '{result}' for input '{input_text}'"

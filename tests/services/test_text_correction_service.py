"""Unit tests for TextCorrectionService."""

import pytest
from whatsthedamage.services.text_correction_service import TextCorrectionService

class TestTextCorrectionService:
    """Focused unit tests for TextCorrectionService."""

    @pytest.fixture
    def service(self) -> TextCorrectionService:
        """Default service with both features enabled."""
        config_dict = {
            'payment_providers': ['^OTPMOBL\\s*', '^PAYPAL\\s*', '^CRV\\s*'],
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b'],
            'buggy_partner_replacements': {'e lelmisz': 'Élelmisz'}
        }
        return TextCorrectionService(config_dict)

    @pytest.fixture
    def service_unicode_only(self) -> TextCorrectionService:
        """Service with only unicode normalization."""
        return TextCorrectionService({})  # Empty dict uses defaults

    @pytest.fixture
    def service_whitespace_only(self) -> TextCorrectionService:
        """Service with only whitespace cleaning."""
        return TextCorrectionService({})  # Empty dict uses defaults

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

        # Both services now use default configuration which includes unicode normalization
        result_unicode = service_unicode_only.clean_partner_field(test_input)
        assert result_unicode == "TATABÁNYA"  # Normalized, spaces cleaned, ML cleaning applied

        result_whitespace = service_whitespace_only.clean_partner_field(test_input)
        assert result_whitespace == "TATABÁNYA"  # Normalized, spaces cleaned, ML cleaning applied

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
        basic_config_dict = {
            'payment_providers': ['^OTPMOBL\\s*', '^PAYPAL\\s*'],
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        }
        basic_service = TextCorrectionService(basic_config_dict)
        result_basic = basic_service.clean_partner_field('OTPMOBL test kft')
        assert result_basic == 'test'  # ML cleaning applied by default

        # Test ML cleaning via configuration flags (default behavior)
        ml_config_dict = {
            'payment_providers': ['^OTPMOBL\\s*', '^PAYPAL\\s*'],
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        }
        ml_service = TextCorrectionService(ml_config_dict)
        result_ml = ml_service.clean_partner_field('OTPMOBL test kft')
        assert result_ml == 'test'  # Both payment provider and suffix removed

        # Test partial ML cleaning - only payment providers
        partial_config_dict = {
            'payment_providers': ['^OTPMOBL\\s*', '^PAYPAL\\s*'],
            'company_suffixes': []  # Empty suffixes
        }
        partial_service = TextCorrectionService(partial_config_dict)
        result_partial = partial_service.clean_partner_field('OTPMOBL test kft')
        assert result_partial == 'test kft'  # Only payment provider removed

        # Test partial ML cleaning - only Hungarian suffixes
        suffix_config_dict = {
            'payment_providers': [],  # Empty providers
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        }
        suffix_service = TextCorrectionService(suffix_config_dict)
        result_suffix = suffix_service.clean_partner_field('OTPMOBL test kft')
        assert result_suffix == 'OTPMOBL test'  # Only suffix removed

    def test_regex_replacement_configuration(self):
        """Test regex-based partner replacement configuration."""
        # Test with regex replacements disabled - but now always enabled by default
        no_regex_config_dict = {
            'buggy_partner_replacements': {
                r'old\s*company': 'New Company',
                r'buggy\s*partner': 'Fixed Partner',
                r'TEST\s*LTD': 'Test Corporation'
            }
        }
        no_regex_service = TextCorrectionService(no_regex_config_dict)

        result_no_regex = no_regex_service.clean_partner_field('old company buggy partner')
        assert result_no_regex == 'New Company Fixed Partner'  # Replacements applied by default

        # Test with regex replacements enabled
        regex_config_dict = {
            'buggy_partner_replacements': {
                r'old\s*company': 'New Company',
                r'buggy\s*partner': 'Fixed Partner',
                r'TEST\s*LTD': 'Test Corporation'
            }
        }
        regex_service = TextCorrectionService(regex_config_dict)

        result_with_regex = regex_service.clean_partner_field('old company buggy partner')
        assert result_with_regex == 'New Company Fixed Partner'  # Both replacements applied

        # Test case insensitivity
        result_case = regex_service.clean_partner_field('OLD COMPANY BUGGY PARTNER')
        assert result_case == 'New Company Fixed Partner'  # Case insensitive matching

        # Test mixed with other cleaning operations
        full_config_dict = {
            'payment_providers': ['^OTPMOBL\\s*'],
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b'],
            'buggy_partner_replacements': {
                r'old\s*company': 'New Company',
                r'buggy\s*partner': 'Fixed Partner',
                r'TEST\s*LTD': 'Test Corporation'
            }
        }
        full_service = TextCorrectionService(full_config_dict)

        result_full = full_service.clean_partner_field('OTPMOBL old company kft')
        assert result_full == 'New Company'  # Regex replacement, then payment provider and suffix removal

    def test_regex_replacement_order(self):
        """Test that regex replacements are applied before payment provider removal."""
        # Set up test replacements
        config_dict = {
            'buggy_partner_replacements': {
                r'PAYPAL\s*OLD': 'New Payment Service',
                r'TEST\s*PARTNER': 'Verified Partner'
            },
            'payment_providers': ['^PAYPAL\\s*']
        }

        service = TextCorrectionService(config_dict)

        # Test that regex replacement happens before payment provider removal
        result = service.clean_partner_field('PAYPAL OLD Service')
        assert result == 'New Payment Service Service'  # Regex replacement first, then PAYPAL prefix would be removed if it existed

        # Test complex scenario
        result_complex = service.clean_partner_field('TEST PARTNER with extra text')
        assert result_complex == 'Verified Partner with extra text'  # Only the regex replacement

    def test_empty_regex_replacements(self):
        """Test behavior when buggy_partner_replacements is empty."""
        # Create config dict with empty replacements
        config_dict = {
            'buggy_partner_replacements': {}
        }

        service = TextCorrectionService(config_dict)

        result = service.clean_partner_field('some random text')
        assert result == 'some random text'  # No changes when dictionary is empty

    def test_regex_payment_providers(self):
        """Test that PAYMENT_PROVIDERS use raw regex patterns without escaping."""
        # Create service with payment provider removal enabled
        config_dict = {
            'payment_providers': [
                '^OTPMOBL\\s*', '^PAYPAL\\s*', '^CRV\\s*',
                '^SUMUP\\s*', '^BARION(P)*\\s*', '^VIMPAY\\s*'
            ],
            'company_suffixes': ['\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.?\\b']
        }
        service = TextCorrectionService(config_dict)

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

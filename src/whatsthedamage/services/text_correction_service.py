"""Text cleaning service for partner field values."""

import unicodedata
import re
import yaml
from typing import Optional, Dict, Any, Tuple
from whatsthedamage.config.text_config import TextCleaningConfig, TextCleaningPatternsConfig
from whatsthedamage.config import DEFAULT_CONFIG_PATH
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

class TextCorrectionService:
    """Service for text cleaning of partner field values."""

    def __init__(self, text_cleaning_config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize the text cleaning service.

        Args:
            text_cleaning_config_dict: Optional dictionary containing text cleaning configuration
                                     from the main config file. If None, uses default configuration.
        """
        # Create both config objects from the provided dictionary or use defaults
        self.config, self.patterns_config = self._create_config_from_dict(text_cleaning_config_dict)

    def _create_config_from_dict(self, text_cleaning_config_dict: Optional[Dict[str, Any]]) -> Tuple[TextCleaningConfig, TextCleaningPatternsConfig]:
        """
        Create TextCleaningConfig and TextCleaningPatternsConfig from raw configuration dictionary.

        Args:
            text_cleaning_config_dict: Dictionary containing text cleaning configuration

        Returns:
            Tuple of (TextCleaningConfig, TextCleaningPatternsConfig)
        """
        # Create cleaning config (currently uses defaults, could be extended to use custom values)
        cleaning_config = TextCleaningConfig()

        # # Create cleaning config from provided dictionary or use defaults
        # if text_cleaning_config_dict:
        #     cleaning_config = TextCleaningConfig(
        #         unicode_normalization=text_cleaning_config_dict.get('unicode_normalization', True),
        #         whitespace_cleaning=text_cleaning_config_dict.get('whitespace_cleaning', True),
        #         replace_buggy_partners=text_cleaning_config_dict.get('replace_buggy_partners', True),
        #         remove_payment_providers=text_cleaning_config_dict.get('remove_payment_providers', True),
        #         remove_hungarian_suffixes=text_cleaning_config_dict.get('remove_hungarian_suffixes', True),
        #         remove_numbers=text_cleaning_config_dict.get('remove_numbers', True),
        #         remove_punctuation=text_cleaning_config_dict.get('remove_punctuation', True),
        #         remove_comment_prefix=text_cleaning_config_dict.get('remove_comment_prefix', True)
        #     )
        # else:
        #     cleaning_config = TextCleaningConfig()

        # Create patterns config from provided dictionary or load defaults
        if text_cleaning_config_dict:
            patterns_config = TextCleaningPatternsConfig(
                payment_providers=text_cleaning_config_dict.get('payment_providers', []),
                company_suffixes=text_cleaning_config_dict.get('company_suffixes', []),
                buggy_partner_replacements=text_cleaning_config_dict.get('buggy_partner_replacements', {})
            )
        else:
            patterns_config = self._load_default_patterns()

        return cleaning_config, patterns_config

    def clean_partner_field(self, partner_text: str) -> str:
        """
        Clean the partner field text by applying normalization, whitespace cleaning,
        and optional ML-specific cleaning based on configuration.

        Args:
            partner_text: Input partner text to clean

        Returns:
            Cleaned partner text
        """
        original = partner_text
        if self.config.unicode_normalization:
            partner_text = self._normalize_unicode(partner_text)

        # Apply regex-based partner replacements if configured
        if self.config.replace_buggy_partners:
            partner_text = self._replace_buggy_partners(partner_text)

        # Apply ML-specific cleaning if configured
        if self.config.remove_payment_providers:
            partner_text = self._remove_payment_providers(partner_text)

        if self.config.remove_hungarian_suffixes:
            partner_text = self._remove_hungarian_suffixes(partner_text)

        if self.config.remove_numbers:
            partner_text = self._remove_numbers(partner_text)

        if self.config.remove_punctuation:
            partner_text = self._remove_punctuation(partner_text)

        if self.config.remove_comment_prefix:
            partner_text = self._remove_comment_prefix(partner_text)

        if self.config.whitespace_cleaning:
            partner_text = self._clean_whitespace(partner_text)

        if original != partner_text:
            logger.debug(f"Text correction: original '{original}' -> {partner_text}",
                        extra={'context': {'original': original, 'corrected': partner_text}})
        return partner_text

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters using NFKC form."""
        return unicodedata.normalize('NFKC', text)

    def _clean_whitespace(self, text: str) -> str:
        """Clean whitespace by collapsing multiple spaces and stripping edges."""
        return re.sub(r'\s+', ' ', text).strip()

    def _remove_payment_providers(self, text: str) -> str:
        """Remove payment provider prefixes from partner text using raw regex patterns."""
        for provider_pattern in self.patterns_config.payment_providers:
            text = re.sub(provider_pattern, '', text, flags=re.IGNORECASE)
        return text.strip()

    def _remove_hungarian_suffixes(self, text: str) -> str:
        """Remove common Hungarian company suffixes from partner text."""
        for suffix in self.patterns_config.company_suffixes:
            text = re.sub(suffix, '', text, flags=re.IGNORECASE)
        return text.strip()

    def _remove_numbers(self, text: str) -> str:
        text = re.sub(r'\d+','',text)
        return text.strip()

    def _remove_punctuation(self, text: str) -> str:
        text = re.sub(r'(?:^|[^a-zA-Z])\.(?:[^a-zA-Z]|$)','', text)
        return text.strip()

    def _remove_comment_prefix(self, text: str) -> str:
        """Remove '// :' comment prefix from partner text."""
        text = re.sub(r'\/\/\s*:', '', text)
        return text.strip()

    def _replace_buggy_partners(self, text: str) -> str:
        """
        Replace partner text using regex patterns from buggy_partner_replacements dictionary.

        For each regex pattern in the dictionary, replaces matches with the corresponding value.
        Uses case-insensitive matching for consistency with other cleaning methods.
        """
        for pattern, replacement in self.patterns_config.buggy_partner_replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()

    def _is_patterns_empty(self, patterns_config: TextCleaningPatternsConfig) -> bool:
        """Check if patterns configuration is empty."""
        return (not patterns_config.payment_providers and
                not patterns_config.company_suffixes and
                not patterns_config.buggy_partner_replacements)

    def _load_default_patterns(self) -> TextCleaningPatternsConfig:
        """Load default text cleaning patterns from configuration file."""
        try:
            # Try to load from default config file
            with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
                text_cleaning_config = config_data.get('text_cleaning', {})
                return TextCleaningPatternsConfig(
                    payment_providers=text_cleaning_config.get('payment_providers', []),
                    company_suffixes=text_cleaning_config.get('company_suffixes', []),
                    buggy_partner_replacements=text_cleaning_config.get('buggy_partner_replacements', {})
                )
        except Exception as e:
            logger.warning(f"Failed to load default text cleaning patterns: {e}")
            # Return empty patterns as fallback
            return TextCleaningPatternsConfig()

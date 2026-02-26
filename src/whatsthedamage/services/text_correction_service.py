"""Text cleaning service for partner field values."""

import unicodedata
import re
from whatsthedamage.config.text_config import TextCleaningConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

class TextCorrectionService:
    """Service for text cleaning of partner field values."""

    def __init__(self, config: TextCleaningConfig):
        """
        Initialize the text cleaning service.

        Args:
            config: Text cleaning configuration
        """
        self.config = config

    def clean_partner_field(self, partner_text: str) -> str:
        """
        Clean the partner field text by applying normalization and whitespace cleaning.

        Args:
            partner_text: Input partner text to clean

        Returns:
            Cleaned partner text
        """
        original = partner_text
        if self.config.unicode_normalization:
            partner_text = self._normalize_unicode(partner_text)

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
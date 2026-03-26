"""Configuration for text cleaning functionality."""

from typing import Dict, List
from pydantic import BaseModel, Field

class TextCleaningConfig(BaseModel):
    """Configuration for text cleaning functionality."""
    unicode_normalization: bool = Field(default=True)
    whitespace_cleaning: bool = Field(default=True)
    replace_buggy_partners: bool = Field(default=True)
    remove_payment_providers: bool = Field(default=True)
    remove_hungarian_suffixes: bool = Field(default=True)
    remove_numbers: bool = Field(default=True)
    remove_punctuation: bool = Field(default=True)
    remove_comment_prefix: bool = Field(default=True)

class TextCleaningPatternsConfig(BaseModel):
    """Configuration for text cleaning patterns."""
    payment_providers: List[str] = Field(default_factory=list)
    company_suffixes: List[str] = Field(default_factory=list)
    buggy_partner_replacements: Dict[str, str] = Field(default_factory=dict)

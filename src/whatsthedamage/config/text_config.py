"""Configuration for text cleaning functionality."""

from pydantic import BaseModel, Field

class TextCleaningConfig(BaseModel):
    """Configuration for text cleaning functionality."""
    unicode_normalization: bool = Field(default=True)
    whitespace_cleaning: bool = Field(default=True)
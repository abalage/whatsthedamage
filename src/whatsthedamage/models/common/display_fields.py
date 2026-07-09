"""Display field models for formatted data representation.

These models represent data that has both a display format (for UI) and a raw value
(for processing/calculations). They are used throughout the application for amounts,
dates, and other formatted data.
"""
from pydantic import BaseModel, Field
from typing import Union


class DisplayRawField(BaseModel):
    """A value with both display format and raw numeric value.

    Used for amounts, totals, and other numeric values that need to be displayed
    in a formatted way (e.g., currency) while maintaining the raw value for
    calculations.

    Attributes:
        display: The formatted string representation (e.g., "-1,234.56 HUF")
        raw: The raw numeric value (float or int)
    """
    display: str = Field(
        description="Formatted string representation of the value"
    )
    raw: Union[float, int] = Field(
        description="Raw numeric value for calculations"
    )


class DateField(BaseModel):
    """A date with both display format and Unix timestamp.

    Used for dates that need to be displayed in a human-readable format
    while maintaining a timestamp for sorting, filtering, and API contracts.

    Attributes:
        display: The formatted date string (e.g., "January 2024", "2024-01-15")
        timestamp: Unix timestamp (seconds since epoch) for programmatic use
    """
    display: str = Field(
        description="Formatted date string for display"
    )
    timestamp: int = Field(
        description="Unix timestamp in seconds"
    )

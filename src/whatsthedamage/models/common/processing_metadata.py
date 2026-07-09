"""Processing metadata model for CSV processing results.

This module provides the ProcessingMetadata model used throughout the application
for tracking processing statistics and metadata.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict


class ProcessingMetadata(BaseModel):
    """Metadata for processing response.

    Contains statistics and contextual information about a processing operation,
    including row count, processing time, ML status, and date range filters.
    """
    row_count: int = Field(description="Number of rows processed")
    processing_time: float = Field(description="Processing time in seconds")
    ml_enabled: bool = Field(description="Whether ML categorization was used")
    result_id: str = Field(description="Unique identifier for this processing result")
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range filter applied (start and end dates)"
    )

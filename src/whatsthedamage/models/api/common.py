"""API common models for request/response metadata.

These Pydantic models define common structures used across API endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Union


class ProcessingMetadata(BaseModel):
    """Metadata for processing response."""
    row_count: int = Field(description="Number of rows processed")
    processing_time: float = Field(description="Processing time in seconds")
    ml_enabled: bool = Field(description="Whether ML categorization was used")
    result_id: str = Field(description="Unique identifier for this processing result")
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range filter applied (start and end dates)"
    )


class ErrorResponse(BaseModel):
    """Standardized error response for all API endpoints.

    Provides consistent error format for v2 API with
    HTTP status code, message, and optional debugging details.
    """
    code: int = Field(
        description="HTTP status code",
        examples=[400, 404, 422, 500]
    )
    message: str = Field(
        description="Human-readable error message",
        examples=["Invalid CSV format", "Results expired, please re-process"]
    )
    details: Optional[Dict[str, Union[str, int, List[str]]]] = Field(
        default=None,
        description="Additional error context and debugging information"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 422,
                "message": "CSV processing failed",
                "details": {
                    "errors": ["Missing required column: 'amount'"],
                    "line": 5
                }
            }
        }
    )

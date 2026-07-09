"""Error response models for API endpoints.

Provides standardized error response format for all API endpoints, ensuring
consistent error handling across the application.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Standardized error response for all API endpoints.

    All error responses (non-200 status codes) should use this format for
    consistency across the API.

    Attributes:
        code: HTTP status code (400, 404, 422, 500, etc.)
        message: Human-readable error description
        details: Optional additional error context/diagnostics for debugging
    """
    code: int = Field(
        description="HTTP status code",
        examples=[400, 404, 422, 500]
    )
    message: str = Field(
        description="Human-readable error message",
        examples=["Invalid CSV format", "Results expired, please re-process"]
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details for debugging"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": 422,
                "message": "CSV processing failed",
                "details": {
                    "errors": ["Missing required column: 'amount'"],
                    "line": 5
                }
            }
        }
    }

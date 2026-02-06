"""
API request and response models using Pydantic.

These models are used exclusively for JSON API request/response validation
and serialization. Web UI forms use FlaskForm, and file uploads use Flask's
request.files. These models provide type safety and automatic validation for
the REST API endpoints.
"""
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Dict, List, Union
from whatsthedamage.config.config import CsvConfig


class ProcessingRequest(BaseModel):
    """Request model for CSV processing endpoints.

    Used by v2 API. File uploads are handled
    separately via Flask's request.files multipart form data.

    Date format is validated against the date_attribute_format from CsvConfig
    (default: "%Y.%m.%d"). If config_file is provided during processing, dates
    should match that config's format.
    """
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for filtering transactions (format matches config date_attribute_format)",
        examples=["2024.01.01"]
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for filtering transactions (format matches config date_attribute_format)",
        examples=["2024.12.31"]
    )
    ml_enabled: bool = Field(
        default=False,
        description="Enable machine learning-based categorization"
    )
    category_filter: Optional[str] = Field(
        default=None,
        description="Filter results by category (e.g., 'grocery', 'utilities')",
        examples=["grocery"]
    )
    language: str = Field(
        default="en",
        description="Language for output localization",
        examples=["en", "hu"]
    )
    date_format: Optional[str] = Field(
        default=None,
        description="Date format string (Python strptime format). If not provided, uses CsvConfig default.",
        examples=["%Y.%m.%d", "%Y-%m-%d"]
    )

    @model_validator(mode='after')
    def validate_date_formats(self) -> 'ProcessingRequest':
        """Validate date formats and range using ValidationService."""
        # Get date_format or use CsvConfig default
        date_format = self.date_format or CsvConfig().date_attribute_format

        # Use ValidationService for validation
        from whatsthedamage.services.validation_service import ValidationService
        validation_service = ValidationService()

        # Validate start_date format
        start_result = validation_service.validate_date_format(self.start_date, date_format)
        if not start_result.is_valid:
            raise ValueError(start_result.error_message or "Invalid start_date")

        # Validate end_date format
        end_result = validation_service.validate_date_format(self.end_date, date_format)
        if not end_result.is_valid:
            raise ValueError(end_result.error_message or "Invalid end_date")

        # Validate date range (start <= end)
        range_result = validation_service.validate_date_range(
            self.start_date, self.end_date, date_format
        )
        if not range_result.is_valid:
            raise ValueError(range_result.error_message or "Invalid date range")

        return self


class ProcessingMetadata(BaseModel):
    """Metadata for processing response."""
    row_count: int = Field(description="Number of rows processed")
    processing_time: float = Field(description="Processing time in seconds")
    ml_enabled: bool = Field(description="Whether ML categorization was used")
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

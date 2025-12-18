"""
API request and response models using Pydantic.

These models are used exclusively for JSON API request/response validation
and serialization. Web UI forms use FlaskForm, and file uploads use Flask's
request.files. These models provide type safety and automatic validation for
the REST API endpoints.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, List, Union
from whatsthedamage.config.config import CsvConfig
from whatsthedamage.config.dt_models import (
    AggregatedRow
)
from whatsthedamage.services.validation_service import ValidationService


class ProcessingRequest(BaseModel):
    """Request model for CSV processing endpoints.

    Used by both v1 (summary) and v2 (detailed) APIs. File uploads are handled
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


class SummaryMetadata(BaseModel):
    """Metadata for summary response."""
    row_count: int = Field(description="Number of rows processed")
    processing_time: float = Field(description="Processing time in seconds")
    ml_enabled: bool = Field(description="Whether ML categorization was used")
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range filter applied (start and end dates)"
    )


class SummaryResponse(BaseModel):
    """Response model for v1 API (summary only).

    Returns aggregated totals by category with minimal metadata.
    Naturally small payloads suitable for direct JSON responses.
    """
    data: Dict[str, float] = Field(
        description="Summary data with category totals (category name -> total amount)"
    )
    metadata: SummaryMetadata = Field(
        description="Processing metadata (row_count, processing_time, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "grocery": -45000.00,
                    "utilities": -12000.00,
                    "salary": 350000.00
                },
                "metadata": {
                    "row_count": 3,
                    "processing_time": 0.15,
                    "ml_enabled": False,
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        }


class DetailedMetadata(BaseModel):
    """Metadata for detailed response."""
    row_count: int = Field(description="Number of rows processed")
    processing_time: float = Field(description="Processing time in seconds")
    ml_enabled: bool = Field(description="Whether ML categorization was used")
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range filter applied (start and end dates)"
    )


class DetailedResponse(BaseModel):
    """Response model for v2 API (includes transaction details).

    Returns transaction-level details grouped by category and month.
    """
    data: List[AggregatedRow] = Field(
        description="List of aggregated rows with transaction details"
    )
    metadata: DetailedMetadata = Field(
        description="Processing metadata"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "category": "grocery",
                        "total": {"display": "-45,000.00 HUF", "raw": -45000.00},
                        "month": {"display": "January 2024", "timestamp": 1704067200},
                        "details": [
                            {
                                "date": {"display": "2024-01-15", "timestamp": 1705276800},
                                "amount": {"display": "-12,500.00", "raw": -12500.00},
                                "merchant": "TESCO",
                                "currency": "HUF"
                            }
                        ]
                    }
                ],
                "metadata": {
                    "result_id": "550e8400-e29b-41d4-a716-446655440000",
                    "row_count": 1,
                    "processing_time": 0.23,
                    "ml_enabled": False
                }
            }
        }


class ExportRequest(BaseModel):
    """Request model for CSV export endpoint.

    Result ID comes from prior /api/v2/process call. No additional
    parameters needed as export uses cached processing results.
    """
    result_id: str = Field(
        description="UUID from prior processing request",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )


class ErrorResponse(BaseModel):
    """Standardized error response for all API endpoints.

    Provides consistent error format across v1 and v2 APIs with
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

    class Config:
        json_schema_extra = {
            "example": {
                "code": 422,
                "message": "CSV processing failed",
                "details": {
                    "errors": ["Missing required column: 'amount'"],
                    "line": 5
                }
            }
        }

"""API request models for REST API v2 endpoints.

These Pydantic models define the contract for API request validation.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional
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
    date_format: Optional[str] = Field(
        default=None,
        description="Date format string (Python strptime format). If not provided, uses CsvConfig default.",
        examples=["%Y.%m.%d", "%Y-%m-%d"]
    )
    cache_ttl: Optional[int] = Field(
        default=None,
        description="Cache TTL in seconds. If None, uses backend default. 0 means never expire.",
        examples=[1800, 0]
    )

    @model_validator(mode='after')
    def validate_date_formats(self) -> 'ProcessingRequest':
        """Validate date formats and range using ValidationService."""
        # Get date_format or use CsvConfig default
        date_format = self.date_format or CsvConfig().date_attribute_format

        # Use FileUploadService for validation
        from whatsthedamage.services.file_upload_service import FileUploadService
        file_upload_service = FileUploadService()

        # Validate start_date format
        start_result = file_upload_service.validate_date_format(self.start_date, date_format)
        if not start_result.is_valid:
            raise ValueError(start_result.error_message or "Invalid start_date")

        # Validate end_date format
        end_result = file_upload_service.validate_date_format(self.end_date, date_format)
        if not end_result.is_valid:
            raise ValueError(end_result.error_message or "Invalid end_date")

        # Validate date range (start <= end)
        range_result = file_upload_service.validate_date_range(
            self.start_date, self.end_date, date_format
        )
        if not range_result.is_valid:
            raise ValueError(range_result.error_message or "Invalid date range")

        return self

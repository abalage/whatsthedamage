"""Validation service for file uploads and MIME types.

This service centralizes validation logic used in file upload handling to
eliminate duplication between web routes and API endpoints.
"""
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
from werkzeug.datastructures import FileStorage
from datetime import datetime
import magic
import os


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        error_message: Human-readable error message if validation failed
        error_code: Machine-readable error code for API responses
        details: Additional context about the validation failure
    """
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(
        cls,
        error_message: str,
        error_code: str = 'VALIDATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            error_message=error_message,
            error_code=error_code,
            details=details or {}
        )


class ValidationError(Exception):
    """Exception raised when validation fails.

    This exception wraps a ValidationResult for easier error handling
    in contexts where exceptions are preferred over result objects.
    """
    def __init__(self, result: ValidationResult):
        self.result = result
        super().__init__(result.error_message)


class ValidationService:
    """Service for validating file uploads and MIME types.

    Centralizes validation logic to eliminate duplication in file handling.

    Attributes:
        _allowed_mime_types: Set of acceptable MIME types for uploaded files
    """

    # CSV files can be text/csv or text/plain (due to encoding edge cases)
    # Config files can be YAML or plain text
    ALLOWED_MIME_TYPES: Set[str] = {
        'text/csv',
        'text/plain',
        'application/x-yaml',
        'text/yaml'
    }

    def __init__(self, allowed_mime_types: Optional[Set[str]] = None):
        """Initialize validation service.

        Args:
            allowed_mime_types: Set of allowed MIME types (optional)
        """
        self._allowed_mime_types = allowed_mime_types or self.ALLOWED_MIME_TYPES

    def validate_file_upload(self, file: FileStorage) -> ValidationResult:
        """Validate uploaded file has a proper filename.

        Args:
            file: Uploaded file object

        Returns:
            ValidationResult indicating success or failure
        """
        if not file.filename:
            return ValidationResult.failure(
                error_message="No file selected",
                error_code="NO_FILE_SELECTED"
            )

        filename = file.filename.strip()
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            return ValidationResult.failure(
                error_message="Invalid filename",
                error_code="INVALID_FILENAME"
            )

        return ValidationResult.success()

    def validate_mime_type(self, file_path: str) -> ValidationResult:
        """Validate file MIME type using libmagic.

        Replaces the old allowed_file() function which was duplicated in
        routes_helpers.py. Accepts text/plain for CSV files as libmagic may
        return text/plain instead of text/csv for certain encodings.

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult indicating success or failure
        """
        if not os.path.exists(file_path):
            return ValidationResult.failure(
                error_message="File not found",
                error_code="FILE_NOT_FOUND"
            )

        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(file_path)

            if detected_mime not in self._allowed_mime_types:
                return ValidationResult.failure(
                    error_message="Invalid file type. Only CSV and YAML files are allowed.",
                    error_code="INVALID_FILE_TYPE"
                )

            return ValidationResult.success()
        except Exception as e:
            return ValidationResult.failure(
                error_message=f"Failed to validate file: {str(e)}",
                error_code="VALIDATION_FAILED"
            )

    def validate_date_format(self, date_str: Optional[str], date_format: str) -> ValidationResult:
        """Validate a date string against a format.

        Args:
            date_str: Date string to validate (None is considered valid)
            date_format: Expected date format (Python strptime format)

        Returns:
            ValidationResult indicating success or failure
        """
        if not date_str:
            return ValidationResult.success()

        try:
            datetime.strptime(date_str, date_format)
            return ValidationResult.success()
        except ValueError:
            return ValidationResult.failure(
                error_message=f"Date '{date_str}' must be in {date_format} format",
                error_code="INVALID_DATE_FORMAT",
                details={"date": date_str, "expected_format": date_format}
            )

    def validate_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        date_format: str
    ) -> ValidationResult:
        """Validate that start_date is before or equal to end_date.

        Also validates that both dates are in the correct format.

        Args:
            start_date: Start date string (None is valid)
            end_date: End date string (None is valid)
            date_format: Expected date format (Python strptime format)

        Returns:
            ValidationResult indicating success or failure
        """
        # If either date is missing, range validation is not applicable
        if not start_date or not end_date:
            return ValidationResult.success()

        # Validate both date formats first
        start_validation = self.validate_date_format(start_date, date_format)
        if not start_validation.is_valid:
            return start_validation

        end_validation = self.validate_date_format(end_date, date_format)
        if not end_validation.is_valid:
            return end_validation

        # Parse dates and compare
        try:
            start = datetime.strptime(start_date, date_format)
            end = datetime.strptime(end_date, date_format)

            if start > end:
                return ValidationResult.failure(
                    error_message="Start date must be before or equal to end date",
                    error_code="INVALID_DATE_RANGE",
                    details={"start_date": start_date, "end_date": end_date}
                )

            return ValidationResult.success()
        except ValueError as e:
            return ValidationResult.failure(
                error_message=f"Invalid date format: {str(e)}",
                error_code="INVALID_DATE_FORMAT"
            )

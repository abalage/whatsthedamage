"""File upload service for handling secure file uploads.

This service centralizes file upload handling logic to eliminate duplication
between web routes and API endpoints. It provides secure file saving with
proper validation, error handling, and cleanup.

Now includes validation functionality that was previously in ValidationService.
"""
import os
from typing import Optional, Set, TYPE_CHECKING
from datetime import datetime
import magic

from werkzeug.utils import secure_filename
from werkzeug.security import safe_join

if TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage
    from whatsthedamage.utils.validation import ValidationResult

__all__ = ['FileUploadService', 'FileUploadError']


class FileUploadError(Exception):
    """Exception raised when file upload operations fail."""
    pass


class FileUploadService:
    """Service for handling secure file uploads.

    Provides centralized file upload handling with validation, secure path
    resolution, and automatic cleanup. Now includes validation functionality
    that was previously in ValidationService.

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
        """Initialize file upload service.

        Args:
            allowed_mime_types: Set of allowed MIME types (optional)
        """
        self._allowed_mime_types = allowed_mime_types or self.ALLOWED_MIME_TYPES

    def validate_file_upload(self, file: "FileStorage") -> "ValidationResult":
        """Validate uploaded file has a proper filename.

        Args:
            file: Uploaded file object

        Returns:
            ValidationResult indicating success or failure
        """
        from whatsthedamage.utils.validation import ValidationResult

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

    def validate_mime_type(self, file_path: str) -> "ValidationResult":
        """Validate file MIME type using libmagic.

        Replaces the old allowed_file() function which was duplicated in
        routes_helpers.py. Accepts text/plain for CSV files as libmagic may
        return text/plain instead of text/csv for certain encodings.

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult indicating success or failure
        """
        from whatsthedamage.utils.validation import ValidationResult

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

    def validate_date_format(self, date_str: Optional[str], date_format: str) -> "ValidationResult":
        """Validate a date string against a format.

        Args:
            date_str: Date string to validate (None is considered valid)
            date_format: Expected date format (Python strptime format)

        Returns:
            ValidationResult indicating success or failure
        """
        from whatsthedamage.utils.validation import ValidationResult

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
    ) -> "ValidationResult":
        """Validate that start_date is before or equal to end_date.

        Also validates that both dates are in the correct format.

        Args:
            start_date: Start date string (None is valid)
            end_date: End date string (None is valid)
            date_format: Expected date format (Python strptime format)

        Returns:
            ValidationResult indicating success or failure
        """
        from whatsthedamage.utils.validation import ValidationResult

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

    def save_file(
        self,
        file: "FileStorage",
        upload_folder: str,
        custom_filename: Optional[str] = None
    ) -> str:
        """Save uploaded file securely with validation.

        :param file: FileStorage object from Flask/Werkzeug
        :param upload_folder: Absolute path to upload directory
        :param custom_filename: Optional custom filename (will be secured)
        :return: Absolute path to saved file
        :raises FileUploadError: If validation fails or save operation fails
        """
        # Validate file upload (filename checks)
        result = self.validate_file_upload(file)
        if not result.is_valid:
            raise FileUploadError(
                result.error_message or "File upload validation failed"
            )

        # Ensure upload folder exists
        try:
            os.makedirs(upload_folder, exist_ok=True)
        except OSError as e:
            raise FileUploadError(f"Failed to create upload directory: {e}")

        # Secure the filename
        if custom_filename:
            filename = secure_filename(custom_filename)
        else:
            filename = secure_filename(file.filename or 'upload')

        # Use safe_join for secure path resolution (prevents directory traversal)
        file_path = safe_join(upload_folder, filename)
        if file_path is None:
            raise FileUploadError(f"Invalid file path: {filename}")

        # Type narrowing: file_path is definitely str here
        assert isinstance(file_path, str)

        # Save the file
        try:
            file.save(file_path)
        except Exception as e:
            raise FileUploadError(f"Failed to save file: {e}")

        # Validate MIME type after saving
        mime_result = self.validate_mime_type(file_path)
        if not mime_result.is_valid:
            # Clean up invalid file
            self._safe_remove(file_path)
            raise FileUploadError(
                mime_result.error_message or "Invalid file type"
            )

        return file_path

    def save_files(
        self,
        csv_file: "FileStorage",
        upload_folder: str,
        config_file: Optional["FileStorage"] = None
    ) -> tuple[str, Optional[str]]:
        """Save CSV and optional config file.

        Convenience method for the common pattern of uploading CSV + config.
        If config file upload fails, CSV is automatically cleaned up.

        :param csv_file: CSV FileStorage object
        :param upload_folder: Absolute path to upload directory
        :param config_file: Optional config FileStorage object
        :return: Tuple of (csv_path, config_path). config_path is None if no config
        :raises FileUploadError: If validation or save fails
        """
        csv_path = None
        config_path = None

        try:
            # Save CSV file
            csv_path = self.save_file(csv_file, upload_folder)

            # Save config file if provided
            if config_file and config_file.filename:
                config_path = self.save_file(config_file, upload_folder)

            return csv_path, config_path

        except FileUploadError:
            # Clean up on error
            if csv_path:
                self._safe_remove(csv_path)
            if config_path:
                self._safe_remove(config_path)
            raise

    def cleanup_files(self, *file_paths: Optional[str]) -> None:
        """Remove uploaded files safely.

        :param file_paths: Variable number of file paths to remove (None values ignored)
        """
        for file_path in file_paths:
            if file_path:
                self._safe_remove(file_path)

    def _safe_remove(self, file_path: str) -> None:
        """Safely remove a file without raising exceptions.

        :param file_path: Path to file to remove
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            # Log warning but don't raise - cleanup is best-effort
            pass

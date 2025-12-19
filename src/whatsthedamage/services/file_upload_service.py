"""File upload service for handling secure file uploads.

This service centralizes file upload handling logic to eliminate duplication
between web routes and API endpoints. It provides secure file saving with
proper validation, error handling, and cleanup.
"""
import os
from typing import Optional, TYPE_CHECKING
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join

from whatsthedamage.services.validation_service import ValidationService

if TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage

__all__ = ['FileUploadService', 'FileUploadError']


class FileUploadError(Exception):
    """Exception raised when file upload operations fail."""
    pass


class FileUploadService:
    """Service for handling secure file uploads.

    Provides centralized file upload handling with validation, secure path
    resolution, and automatic cleanup. Uses ValidationService for MIME type
    and filename validation.

    Attributes:
        validation_service: Service for validating files
    """

    def __init__(self, validation_service: ValidationService):
        """Initialize file upload service.

        Args:
            validation_service: ValidationService instance for file validation
        """
        self.validation_service = validation_service

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
        result = self.validation_service.validate_file_upload(file)
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
        mime_result = self.validation_service.validate_mime_type(file_path)
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

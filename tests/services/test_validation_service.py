"""Tests for ValidationService."""

import tempfile
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage

from whatsthedamage.services.validation_service import (
    ValidationService,
    ValidationResult,
    ValidationError,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_success(self):
        """Test successful validation result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.error_code is None
        assert result.details is None

    def test_validation_result_failure(self):
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            error_message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        assert result.is_valid is False
        assert result.error_message == "Test error"
        assert result.error_code == "TEST_ERROR"
        assert result.details == {"key": "value"}


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_message(self):
        """Test ValidationError with message."""
        result = ValidationResult.failure("Test error message", "TEST_ERROR")
        error = ValidationError(result)
        assert str(error) == "Test error message"
        assert error.result == result

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        result = ValidationResult.failure("Error", "TEST_ERROR", {"code": "TEST"})
        error = ValidationError(result)
        assert str(error) == "Error"
        assert error.result.details == {"code": "TEST"}


class TestFileUploadValidation:
    """Tests for file upload validation."""

    def test_validate_file_upload_success(self):
        """Test successful file upload validation."""
        service = ValidationService()
        file = FileStorage(
            stream=BytesIO(b"test content"),
            filename="test.csv"
        )
        result = service.validate_file_upload(file)
        assert result.is_valid is True

    def test_validate_file_upload_no_filename(self):
        """Test validation fails for missing filename."""
        service = ValidationService()
        file = FileStorage(
            stream=BytesIO(b"test"),
            filename=""
        )
        result = service.validate_file_upload(file)
        assert result.is_valid is False
        assert result.error_code == "NO_FILE_SELECTED"

    def test_validate_file_upload_path_traversal(self):
        """Test validation blocks path traversal attempts."""
        service = ValidationService()

        # Test various path traversal patterns
        bad_filenames = [
            "../etc/passwd",
            "..\\windows\\system32",
            "folder/file.csv",
            "folder\\file.csv"
        ]

        for filename in bad_filenames:
            file = FileStorage(
                stream=BytesIO(b"test"),
                filename=filename
            )
            result = service.validate_file_upload(file)
            assert result.is_valid is False
            assert result.error_code == "INVALID_FILENAME"

    def test_validate_file_upload_valid_filenames(self):
        """Test validation accepts safe filenames."""
        service = ValidationService()

        # Test various safe filename patterns
        safe_filenames = [
            "file.csv",
            "my-file_2024.csv",
            "transactions.csv",
            "config.yml",
        ]

        for filename in safe_filenames:
            file = FileStorage(
                stream=BytesIO(b"test"),
                filename=filename
            )
            result = service.validate_file_upload(file)
            assert result.is_valid is True


class TestMimeTypeValidation:
    """Tests for MIME type validation."""

    def test_validate_mime_type_csv_success(self):
        """Test successful CSV MIME type validation."""
        service = ValidationService()

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("header1,header2\n")
            f.write("value1,value2\n")
            temp_path = f.name

        try:
            result = service.validate_mime_type(temp_path)
            assert result.is_valid is True
        finally:
            os.unlink(temp_path)

    def test_validate_mime_type_yaml_success(self):
        """Test successful YAML MIME type validation."""
        service = ValidationService()

        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("csv:\n  delimiter: ','\n")
            temp_path = f.name

        try:
            result = service.validate_mime_type(temp_path)
            assert result.is_valid is True
        finally:
            os.unlink(temp_path)

    def test_validate_mime_type_file_not_found(self):
        """Test validation fails for non-existent file."""
        service = ValidationService()

        result = service.validate_mime_type('/nonexistent/file.csv')
        assert result.is_valid is False
        assert result.error_code == "FILE_NOT_FOUND"

    def test_validate_mime_type_wrong_type(self):
        """Test validation fails for wrong MIME type."""
        service = ValidationService()

        # Create a PDF file (or binary file)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b"%PDF-1.4\n")
            temp_path = f.name

        try:
            result = service.validate_mime_type(temp_path)
            assert result.is_valid is False
            assert result.error_code == "INVALID_FILE_TYPE"
        finally:
            os.unlink(temp_path)


class TestDateFormatValidation:
    """Tests for date format validation."""

    def test_validate_date_format_success(self):
        """Test successful date format validation."""
        service = ValidationService()

        result = service.validate_date_format('2024-01-15', '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_format_custom_format(self):
        """Test validation with custom date format."""
        service = ValidationService()

        result = service.validate_date_format('2024.01.15', '%Y.%m.%d')
        assert result.is_valid is True

    def test_validate_date_format_invalid(self):
        """Test validation fails for invalid date format."""
        service = ValidationService()

        result = service.validate_date_format('2024/01/15', '%Y-%m-%d')
        assert result.is_valid is False
        assert result.error_code == "INVALID_DATE_FORMAT"
        assert result.error_message is not None
        assert '2024/01/15' in result.error_message
        assert '%Y-%m-%d' in result.error_message

    def test_validate_date_format_none(self):
        """Test validation succeeds for None date."""
        service = ValidationService()

        result = service.validate_date_format(None, '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_format_empty_string(self):
        """Test validation succeeds for empty date string."""
        service = ValidationService()

        result = service.validate_date_format('', '%Y-%m-%d')
        assert result.is_valid is True


class TestDateRangeValidation:
    """Tests for date range validation."""

    def test_validate_date_range_valid(self):
        """Test successful date range validation."""
        service = ValidationService()

        result = service.validate_date_range('2024-01-01', '2024-12-31', '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_range_same_date(self):
        """Test date range validation allows same start and end date."""
        service = ValidationService()

        result = service.validate_date_range('2024-06-15', '2024-06-15', '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_range_invalid_order(self):
        """Test validation fails when start date is after end date."""
        service = ValidationService()

        result = service.validate_date_range('2024-12-31', '2024-01-01', '%Y-%m-%d')
        assert result.is_valid is False
        assert result.error_code == "INVALID_DATE_RANGE"
        assert result.error_message is not None
        assert "Start date must be before or equal to end date" in result.error_message

    def test_validate_date_range_invalid_start_format(self):
        """Test validation fails for invalid start date format."""
        service = ValidationService()

        result = service.validate_date_range('2024/01/01', '2024-12-31', '%Y-%m-%d')
        assert result.is_valid is False
        assert result.error_code == "INVALID_DATE_FORMAT"

    def test_validate_date_range_invalid_end_format(self):
        """Test validation fails for invalid end date format."""
        service = ValidationService()

        result = service.validate_date_range('2024-01-01', '2024/12/31', '%Y-%m-%d')
        assert result.is_valid is False
        assert result.error_code == "INVALID_DATE_FORMAT"

    def test_validate_date_range_both_none(self):
        """Test date range validation succeeds when both dates are None."""
        service = ValidationService()

        result = service.validate_date_range(None, None, '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_range_only_start(self):
        """Test date range validation succeeds with only start date."""
        service = ValidationService()

        result = service.validate_date_range('2024-01-01', None, '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_range_only_end(self):
        """Test date range validation succeeds with only end date."""
        service = ValidationService()

        result = service.validate_date_range(None, '2024-12-31', '%Y-%m-%d')
        assert result.is_valid is True

    def test_validate_date_range_custom_format(self):
        """Test date range validation with custom format."""
        service = ValidationService()

        result = service.validate_date_range('2024.01.01', '2024.12.31', '%Y.%m.%d')
        assert result.is_valid is True

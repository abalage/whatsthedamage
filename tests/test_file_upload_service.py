"""Tests for FileUploadService.

Tests file upload handling, validation, error handling, and cleanup.
"""
import os
import pytest
from unittest.mock import Mock, patch
from werkzeug.datastructures import FileStorage

from whatsthedamage.services.file_upload_service import FileUploadService, FileUploadError
from whatsthedamage.services.validation_service import ValidationService


# ==================== Fixtures ====================

@pytest.fixture
def validation_service():
    """Create a ValidationService instance for testing."""
    return ValidationService()


@pytest.fixture
def file_upload_service(validation_service):
    """Create a FileUploadService instance for testing."""
    return FileUploadService(validation_service)


@pytest.fixture
def temp_upload_folder(tmp_path):
    """Create a temporary upload folder."""
    upload_folder = tmp_path / "uploads"
    upload_folder.mkdir()
    return str(upload_folder)


def create_mock_file(filename, content_writer=None):
    """Helper to create a mock FileStorage object.

    Args:
        filename: Name of the file
        content_writer: Callable that writes content to path (e.g., csv_content_writer)
    """
    file = Mock(spec=FileStorage)
    file.filename = filename
    if content_writer:
        file.save = content_writer
    else:
        file.save = Mock()
    return file


def csv_content_writer(path):
    """Write valid CSV content to path."""
    with open(path, 'w') as f:
        f.write("date,amount\n2024-01-01,100\n")


def yaml_content_writer(path):
    """Write valid YAML content to path."""
    with open(path, 'w') as f:
        f.write("csv:\n  delimiter: ','\n")


def invalid_mime_content_writer(path):
    """Write content that will fail MIME validation (JSON file)."""
    with open(path, 'w') as f:
        f.write('{"key": "value", "type": "json"}\n')

# ==================== Tests ====================

class TestSaveFile:
    """Tests for save_file method."""

    @pytest.mark.parametrize("custom_filename,expected_filename", [
        (None, "test.csv"),
        ("custom.csv", "custom.csv"),
    ])
    def test_save_file_success(self, file_upload_service, temp_upload_folder,
                               custom_filename, expected_filename):
        """Test successful file save with and without custom filename."""
        mock_file = create_mock_file("test.csv", csv_content_writer)
        file_path = os.path.join(temp_upload_folder, expected_filename)

        result_path = file_upload_service.save_file(
            mock_file,
            temp_upload_folder,
            custom_filename=custom_filename
        )

        assert result_path == file_path
        assert os.path.exists(result_path)

    @pytest.mark.parametrize("filename,expected_error", [
        ("", "No file selected"),
        ("../../../etc/passwd", "Invalid filename"),
        ("file/../other", "Invalid filename"),
    ])
    def test_save_file_invalid_filename(self, file_upload_service, temp_upload_folder,
                                       filename, expected_error):
        """Test save fails for invalid filenames."""
        mock_file = create_mock_file(filename)

        with pytest.raises(FileUploadError, match=expected_error):
            file_upload_service.save_file(mock_file, temp_upload_folder)

    def test_save_file_creates_upload_folder(self, file_upload_service, tmp_path):
        """Test that upload folder is created if it doesn't exist."""
        upload_folder = str(tmp_path / "new_uploads")
        mock_file = create_mock_file("test.csv", csv_content_writer)

        assert not os.path.exists(upload_folder)

        result_path = file_upload_service.save_file(mock_file, upload_folder)

        assert os.path.exists(upload_folder)
        assert os.path.exists(result_path)

    def test_save_file_invalid_mime_type(self, file_upload_service, temp_upload_folder):
        """Test save fails for invalid MIME type (JSON) and cleans up."""
        mock_file = create_mock_file("data.json", invalid_mime_content_writer)

        with pytest.raises(FileUploadError, match="Invalid file type"):
            file_upload_service.save_file(mock_file, temp_upload_folder)

        # File should be cleaned up
        assert not os.path.exists(os.path.join(temp_upload_folder, "data.json"))

    @pytest.mark.parametrize("exception,error_message", [
        (IOError("Disk full"), "Failed to save file"),
        (PermissionError("Access denied"), "Failed to save file"),
    ])
    def test_save_file_exceptions(self, file_upload_service, temp_upload_folder,
                                  exception, error_message):
        """Test handling of various save exceptions."""
        mock_file = create_mock_file("test.csv")
        mock_file.save = Mock(side_effect=exception)

        with pytest.raises(FileUploadError, match=error_message):
            file_upload_service.save_file(mock_file, temp_upload_folder)

    @patch('os.makedirs')
    def test_save_file_mkdir_exception(self, mock_makedirs, file_upload_service):
        """Test handling of mkdir exceptions."""
        mock_makedirs.side_effect = OSError("Permission denied")
        mock_file = create_mock_file("test.csv")

        with pytest.raises(FileUploadError, match="Failed to create upload directory"):
            file_upload_service.save_file(mock_file, "/invalid/path")


class TestSaveFiles:
    """Tests for save_files method (CSV + config)."""

    @pytest.mark.parametrize("config_filename,config_writer,expect_config", [
        (None, None, False),  # No config file
        ("", None, False),    # Empty filename
        ("config.yml", yaml_content_writer, True),  # Valid config
    ])
    def test_save_files_various_configs(self, file_upload_service, temp_upload_folder,
                                       config_filename, config_writer, expect_config):
        """Test saving CSV with various config file scenarios."""
        mock_csv = create_mock_file("test.csv", csv_content_writer)

        config_file = None
        if config_filename is not None:
            config_file = create_mock_file(config_filename, config_writer)

        csv_path, config_path = file_upload_service.save_files(
            mock_csv,
            temp_upload_folder,
            config_file=config_file
        )

        assert csv_path is not None
        assert os.path.exists(csv_path)

        if expect_config:
            assert config_path is not None
            assert os.path.exists(config_path)
        else:
            assert config_path is None

    @pytest.mark.parametrize("fail_on,expected_files_remaining", [
        ("csv", 0),     # CSV fails, nothing saved
        ("config", 0),  # Config fails, both cleaned up
    ])
    def test_save_files_cleanup_on_error(self, file_upload_service, temp_upload_folder,
                                        fail_on, expected_files_remaining):
        """Test cleanup when save operations fail."""
        if fail_on == "csv":
            mock_csv = create_mock_file("test.csv")
            mock_csv.save = Mock(side_effect=IOError("Disk full"))
            config_file = None
        else:  # fail_on == "config"
            mock_csv = create_mock_file("test.csv", csv_content_writer)
            config_file = create_mock_file("config.json", invalid_mime_content_writer)

        with pytest.raises(FileUploadError):
            file_upload_service.save_files(
                mock_csv,
                temp_upload_folder,
                config_file=config_file
            )

        assert len(os.listdir(temp_upload_folder)) == expected_files_remaining


class TestCleanupFiles:
    """Tests for cleanup_files method."""

    @pytest.mark.parametrize("num_files,include_none", [
        (1, False),   # Single file
        (2, False),   # Multiple files
        (1, True),    # File with None values
    ])
    def test_cleanup_files(self, file_upload_service, temp_upload_folder,
                          num_files, include_none):
        """Test cleanup of various file configurations."""
        # Create test files
        file_paths = []
        for i in range(num_files):
            file_path = os.path.join(temp_upload_folder, f"test{i}.csv")
            with open(file_path, 'w') as f:
                f.write(f"test{i}")
            file_paths.append(file_path)
            assert os.path.exists(file_path)

        # Add None values if requested
        if include_none:
            file_paths.extend([None, None])

        # Cleanup
        file_upload_service.cleanup_files(*file_paths)

        # Verify all real files are removed
        for file_path in file_paths:
            if file_path is not None:
                assert not os.path.exists(file_path)

    def test_cleanup_nonexistent_file(self, file_upload_service, temp_upload_folder):
        """Test cleanup of nonexistent file doesn't raise exception."""
        nonexistent = os.path.join(temp_upload_folder, "nonexistent.csv")
        file_upload_service.cleanup_files(nonexistent)  # Should not raise

    @patch('os.unlink')
    def test_cleanup_handles_oserror(self, mock_unlink, file_upload_service):
        """Test cleanup handles OSError gracefully."""
        mock_unlink.side_effect = OSError("Permission denied")
        file_upload_service.cleanup_files("/some/file.csv")  # Should not raise


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_with_cleanup(self, file_upload_service, temp_upload_folder):
        """Test full workflow: save CSV + config, then cleanup."""
        mock_csv = create_mock_file("test.csv", csv_content_writer)
        mock_config = create_mock_file("config.yml", yaml_content_writer)

        # Save files
        csv_path, config_path = file_upload_service.save_files(
            mock_csv,
            temp_upload_folder,
            config_file=mock_config
        )

        assert os.path.exists(csv_path)
        assert os.path.exists(config_path)

        # Cleanup
        file_upload_service.cleanup_files(csv_path, config_path)

        assert not os.path.exists(csv_path)
        assert not os.path.exists(config_path)

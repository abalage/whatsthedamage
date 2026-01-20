"""Tests for SessionService file cleanup functionality."""

import pytest
import tempfile
import os
import time
from flask import Flask, session
from whatsthedamage.services.session_service import SessionService

class TestSessionServiceFileCleanup:
    """Tests for SessionService file cleanup functionality."""

    @pytest.fixture
    def app(self):
        """Create Flask app with test configuration."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def session_service(self):
        """Create SessionService instance."""
        return SessionService()

    @pytest.fixture
    def temp_upload_folder(self):
        """Create temporary upload folder for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_store_uploaded_file_with_ttl(self, app, session_service, temp_upload_folder):
        """Test storing uploaded file with TTL."""
        with app.test_request_context():
            # Store a file with custom TTL
            file_path = os.path.join(temp_upload_folder, "test_file.csv")
            with open(file_path, 'w') as f:
                f.write("test content")

            session_service.store_uploaded_file_reference(file_path, ttl=300)

            # Verify file is stored in session
            uploaded_files = session_service.get_uploaded_file_references()
            assert file_path in uploaded_files
            assert uploaded_files[file_path] > time.time()  # Expiry in future

    def test_store_uploaded_file_with_default_ttl(self, app, session_service, temp_upload_folder):
        """Test storing uploaded file with default TTL (600 seconds)."""
        with app.test_request_context():
            # Store a file with default TTL
            file_path = os.path.join(temp_upload_folder, "test_file.csv")
            with open(file_path, 'w') as f:
                f.write("test content")

            session_service.store_uploaded_file_reference(file_path)

            # Verify file is stored with default TTL
            uploaded_files = session_service.get_uploaded_file_references()
            assert file_path in uploaded_files
            expiry_time = uploaded_files[file_path]
            assert expiry_time > time.time()
            assert expiry_time <= time.time() + 601  # Should be ~600 seconds from now

    def test_get_uploaded_files_empty(self, app, session_service):
        """Test getting uploaded files when none exist."""
        with app.test_request_context():
            uploaded_files = session_service.get_uploaded_file_references()
            assert uploaded_files == {}

    def test_get_uploaded_files_with_data(self, app, session_service, temp_upload_folder):
        """Test getting uploaded files with existing data."""
        with app.test_request_context():
            # Store multiple files
            file1 = os.path.join(temp_upload_folder, "file1.csv")
            file2 = os.path.join(temp_upload_folder, "file2.csv")
            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")

            session_service.store_uploaded_file_reference(file1, ttl=100)
            session_service.store_uploaded_file_reference(file2, ttl=200)

            # Get uploaded files
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 2
            assert file1 in uploaded_files
            assert file2 in uploaded_files

    def test_cleanup_expired_files_no_expired_files(self, app, session_service, temp_upload_folder):
        """Test cleanup when no files are expired."""
        with app.test_request_context():
            # Store files with long TTL
            file1 = os.path.join(temp_upload_folder, "file1.csv")
            file2 = os.path.join(temp_upload_folder, "file2.csv")
            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")

            session_service.store_uploaded_file_reference(file1, ttl=300)
            session_service.store_uploaded_file_reference(file2, ttl=300)

            # Cleanup should not remove any files
            session_service.cleanup_expired_file_references(temp_upload_folder)

            # Files should still be in session
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 2
            assert file1 in uploaded_files
            assert file2 in uploaded_files

            # Files should still exist on disk
            assert os.path.exists(file1)
            assert os.path.exists(file2)

    def test_cleanup_expired_files_with_expired_files(self, app, session_service, temp_upload_folder):
        """Test cleanup when some files are expired."""
        with app.test_request_context():
            # Store files with short TTL (already expired)
            file1 = os.path.join(temp_upload_folder, "file1.csv")
            file2 = os.path.join(temp_upload_folder, "file2.csv")
            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")

            # Set expiry times in the past
            past_time = time.time() - 100  # 100 seconds ago
            session[session_service.SESSION_KEY_UPLOADED_FILES] = {
                file1: past_time,
                file2: past_time
            }

            # Cleanup should remove expired files
            session_service.cleanup_expired_file_references(temp_upload_folder)

            # Files should be removed from session
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 0

            # Files should be removed from disk
            assert not os.path.exists(file1)
            assert not os.path.exists(file2)

    def test_cleanup_expired_files_mixed_expiry(self, app, session_service, temp_upload_folder):
        """Test cleanup with mix of expired and non-expired files."""
        with app.test_request_context():
            # Store files with different expiry times
            expired_file = os.path.join(temp_upload_folder, "expired.csv")
            valid_file = os.path.join(temp_upload_folder, "valid.csv")
            with open(expired_file, 'w') as f:
                f.write("expired content")
            with open(valid_file, 'w') as f:
                f.write("valid content")

            # Set mixed expiry times
            past_time = time.time() - 100  # Expired
            future_time = time.time() + 300  # Still valid
            session[session_service.SESSION_KEY_UPLOADED_FILES] = {
                expired_file: past_time,
                valid_file: future_time
            }

            # Cleanup should only remove expired file
            session_service.cleanup_expired_file_references(temp_upload_folder)

            # Only valid file should remain in session
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 1
            assert valid_file in uploaded_files
            assert expired_file not in uploaded_files

            # Expired file should be removed from disk, valid file should remain
            assert not os.path.exists(expired_file)
            assert os.path.exists(valid_file)

    def test_cleanup_expired_files_nonexistent_files(self, app, session_service, temp_upload_folder):
        """Test cleanup handles non-existent files gracefully."""
        with app.test_request_context():
            # Store reference to non-existent file
            nonexistent_file = os.path.join(temp_upload_folder, "nonexistent.csv")
            past_time = time.time() - 100
            session[session_service.SESSION_KEY_UPLOADED_FILES] = {
                nonexistent_file: past_time
            }

            # Cleanup should not raise exception for non-existent file
            session_service.cleanup_expired_file_references(temp_upload_folder)

            # File should be removed from session
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 0

    def test_cleanup_expired_files_directory_removal(self, app, session_service, temp_upload_folder):
        """Test cleanup handles directory removal gracefully."""
        with app.test_request_context():
            # Create a directory instead of a file
            dir_path = os.path.join(temp_upload_folder, "test_dir")
            os.makedirs(dir_path, exist_ok=True)

            # Store directory with expired TTL
            past_time = time.time() - 100
            session[session_service.SESSION_KEY_UPLOADED_FILES] = {
                dir_path: past_time
            }

            # Cleanup should handle directory removal
            session_service.cleanup_expired_file_references(temp_upload_folder)

            # Directory should be removed
            assert not os.path.exists(dir_path)

            # Entry should be removed from session
            uploaded_files = session_service.get_uploaded_file_references()
            assert len(uploaded_files) == 0

    def test_cleanup_expired_files_permission_error(self, app, session_service, temp_upload_folder):
        """Test cleanup handles permission errors gracefully."""
        with app.test_request_context():
            # Create a file and make it read-only
            readonly_file = os.path.join(temp_upload_folder, "readonly.csv")
            with open(readonly_file, 'w') as f:
                f.write("readonly content")

            # Set file to read-only (if platform supports it)
            try:
                os.chmod(readonly_file, 0o444)  # Read-only

                # Store with expired TTL
                past_time = time.time() - 100
                session[session_service.SESSION_KEY_UPLOADED_FILES] = {
                    readonly_file: past_time
                }

                # Cleanup should handle permission error gracefully
                session_service.cleanup_expired_file_references(temp_upload_folder)

                # File should be removed from session even if disk deletion fails
                uploaded_files = session_service.get_uploaded_file_references()
                assert len(uploaded_files) == 0

            finally:
                # Restore permissions for cleanup
                if os.path.exists(readonly_file):
                    os.chmod(readonly_file, 0o644)
                    os.remove(readonly_file)

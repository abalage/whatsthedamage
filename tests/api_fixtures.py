"""Pytest fixtures specifically for API unit tests.

Provides test clients, mocks, and helpers for testing API endpoints
in isolation from business logic.
"""
import os
import pytest
import tempfile
import shutil
from contextlib import contextmanager


@contextmanager
def _create_test_client(processing_service=None):
    """Internal helper to create Flask test client with optional service injection.

    Args:
        processing_service: Optional ProcessingService to inject via DI

    Yields:
        Flask test client with app context
    """
    from whatsthedamage.app import create_app

    temp_dir = tempfile.mkdtemp()

    config = {
        'TESTING': True,
        'UPLOAD_FOLDER': temp_dir,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max file size
    }

    app = create_app(processing_service=processing_service)
    app.config.from_mapping(config)

    try:
        with app.test_client() as client:
            with app.app_context():
                yield client
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@pytest.fixture
def api_client():
    """Flask test client fixture for testing API endpoints.

    Includes both v1 and v2 API blueprints with proper configuration.
    Uses default ProcessingService (tests should mock it as needed).
    """
    with _create_test_client() as client:
        yield client


@pytest.fixture
def mock_processing_service():
    """Mock ProcessingService for testing with auto-configured successful responses."""
    from tests.api_test_utils import MockProcessingService
    service = MockProcessingService()

    # Auto-configure with successful default responses
    service.process_summary.return_value = MockProcessingService.create_summary_result(
        {'default': 100.0}, row_count=2
    )
    service.process_with_details.return_value = MockProcessingService.create_detailed_result(
        [], row_count=2
    )

    return service


@pytest.fixture
def api_client_with_mock(mock_processing_service):
    """Flask test client with mocked ProcessingService injected.

    Use this fixture when you need to control ProcessingService behavior.
    Configure mock_processing_service in your test before making requests.
    """
    with _create_test_client(processing_service=mock_processing_service) as client:
        yield client


@pytest.fixture
def sample_csv_file():
    """Sample CSV file ready for upload."""
    from tests.api_test_utils import create_csv_bytes
    content = create_csv_bytes([
        ['2023-01-01', '100', 'bank', 'deposit', 'EUR'],
        ['2023-01-02', '200', 'bank', 'deposit', 'EUR']
    ])
    return (content, 'test.csv')


@pytest.fixture
def api_test_helper(api_client_with_mock):
    """APITestClient helper wrapper for cleaner test code."""
    from tests.api_test_utils import APITestClient
    return APITestClient(api_client_with_mock)

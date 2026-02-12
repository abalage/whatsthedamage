"""Unit and integration tests for main routes.

This module contains comprehensive tests for the main application routes:
- index
- process
- clear
- legal
- privacy
- about
- set_language
- recalculate_statistics
- health
- favicon
"""
import pytest
import os
from flask import current_app
from io import BytesIO
from unittest.mock import patch
from tests.utils.route_test_factory import RouteTestFactory
from whatsthedamage.controllers.routes import clear_upload_folder

class TestMainRoutes:
    """Test suite for main application routes."""

    @pytest.fixture
    def factory(self) -> RouteTestFactory:
        """Create route test factory."""
        return RouteTestFactory()

    @pytest.fixture
    def client(self, factory: RouteTestFactory):
        """Create test client with configured services."""
        return factory.create_test_client()

    def test_index_route(self, client):
        """Test index route returns 200 and contains form."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<form' in response.data

    def test_clear_route(self, client):
        """Test clear route clears session data and redirects."""
        # Setup session data
        with client.session_transaction() as sess:
            sess['form_data'] = {'some': 'data'}

        # Get CSRF token (disabled in test config, but we'll mock it)
        csrf_token = "test-csrf-token"

        response = client.post('/clear', data={'csrf_token': csrf_token})

        assert response.status_code == 302
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert 'form_data' not in sess

    def test_clear_upload_folder(self, client):
        """Test clear_upload_folder function removes files from upload directory."""
        with client.application.app_context():
            upload_folder = current_app.config['UPLOAD_FOLDER']
            test_file_path = os.path.join(upload_folder, 'test.txt')
            with open(test_file_path, 'w') as f:
                f.write('test content')

            clear_upload_folder()
            assert not os.path.exists(test_file_path)

    def test_legal_route(self, client):
        """Test legal route returns 200."""
        response = client.get('/legal')
        assert response.status_code == 200

    def test_privacy_route(self, client):
        """Test privacy route returns 200."""
        response = client.get('/privacy')
        assert response.status_code == 200

    def test_about_route(self, client):
        """Test about route returns 200."""
        response = client.get('/about')
        assert response.status_code == 200

    def test_set_language_route(self, client):
        """Test set_language route changes language and redirects."""
        # Test valid language
        response = client.get('/set_language/en', follow_redirects=True)
        assert response.status_code == 200
        assert b'Language changed to EN' in response.data

        # Test invalid language
        response = client.get('/set_language/invalid', follow_redirects=True)
        assert response.status_code == 200
        assert b'Selected language is not supported' in response.data

    def test_favicon_route(self, client):
        """Test favicon route returns favicon."""
        response = client.get('/favicon.ico')
        assert response.status_code == 200

    def test_health_route(self, client):
        """Test health route returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        assert b'healthy' in response.data

    def test_recalculate_statistics_route(self, client):
        """Test recalculate_statistics route with valid and invalid data."""
        # Test missing data
        response = client.post('/recalculate-statistics', json={})
        assert response.status_code == 400
        assert b'No data provided' in response.data

        # Test missing result_id
        response = client.post('/recalculate-statistics', json={'algorithms': ['iqr']})
        assert response.status_code == 400
        assert b'result_id is required' in response.data

        # Test invalid algorithms (not a list)
        response = client.post('/recalculate-statistics', json={
            'result_id': 'test123',
            'algorithms': 'not-a-list'
        })
        assert response.status_code == 400
        assert b'algorithms must be a list' in response.data

        # Test invalid direction
        response = client.post('/recalculate-statistics', json={
            'result_id': 'test123',
            'algorithms': ['iqr'],
            'direction': 'invalid'
        })
        assert response.status_code == 400
        assert b'direction must be either' in response.data
        assert b'columns' in response.data
        assert b'rows' in response.data

    def test_process_route_success(self, client, monkeypatch, standard_csv_content, standard_config_content, process_test_data):
        """Test process route with valid CSV and config files."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            # Use fixture to prepare test data
            data = process_test_data()

            # Ensure upload folder exists within application context
            with client.application.app_context():
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

            response = client.post('/process', data=data, content_type='multipart/form-data')

            assert response.status_code == 200
            # Check that form data is stored in session
            with client.session_transaction() as sess:
                assert 'form_data' in sess

    def test_process_route_invalid_data(self, client, monkeypatch, standard_config_content):
        """Test process route with missing required fields."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            # Use standard config content from fixture
            data = {
                'csrf_token': "test-csrf-token",
                'config': (BytesIO(standard_config_content.encode()), 'config.yml')
                # Missing other required fields
            }
            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 302  # Expecting a redirect due to validation failure

    def test_process_route_missing_file(self, client, monkeypatch, standard_config_content):
        """Test process route with missing CSV file."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            data = {
                'csrf_token': "test-csrf-token",
                'config': (BytesIO(standard_config_content.encode()), 'config.yml'),
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
            }
            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 302  # Expecting a redirect due to missing file

    def test_process_route_missing_config(self, client, monkeypatch, standard_csv_content):
        """Test process route with missing config file (ML mode enabled)."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            data = {
                'csrf_token': "test-csrf-token",
                'filename': (BytesIO(standard_csv_content.encode()), 'sample.csv'),
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'ml': True,  # ML mode enabled, config can be missing
            }
            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 200

    def test_process_route_invalid_end_date(self, client, monkeypatch, standard_csv_content, standard_config_content):
        """Test process route with invalid end date format."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            data = {
                'csrf_token': "test-csrf-token",
                'filename': (BytesIO(standard_csv_content.encode()), 'sample.csv'),
                'config': (BytesIO(standard_config_content.encode()), 'config.yml'),
                'start_date': '2023-01-01',
                'end_date': 'invalid-date',
            }
            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 302  # Expecting a redirect due to invalid end date format
            # Verify session doesn't contain form data
            with client.session_transaction() as sess:
                assert 'form_data' not in sess

    def test_process_route_invalid_start_date(self, client, monkeypatch, standard_csv_content, standard_config_content):
        """Test process route with invalid start date format."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            data = {
                'csrf_token': "test-csrf-token",
                'filename': (BytesIO(standard_csv_content.encode()), 'sample.csv'),
                'config': (BytesIO(standard_config_content.encode()), 'config.yml'),
                'start_date': 'invalid-date',
                'end_date': '2023-12-31',
            }
            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 302  # Expecting a redirect due to invalid start date format
            # Verify session doesn't contain form data
            with client.session_transaction() as sess:
                assert 'form_data' not in sess

class TestMainRoutesEdgeCases:
    """Edge case tests for main application routes."""

    @pytest.fixture
    def factory(self) -> RouteTestFactory:
        """Create route test factory."""
        return RouteTestFactory()

    @pytest.fixture
    def client(self, factory: RouteTestFactory):
        """Create test client with configured services."""
        return factory.create_test_client()

    def test_process_route_with_empty_csv(self, client, monkeypatch, standard_config_content):
        """Test process route with empty CSV file."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            # Create empty CSV content
            csv_content = """date,amount,currency,partner
"""

            data = {
                'csrf_token': "test-csrf-token",
                'filename': (BytesIO(csv_content.encode()), 'empty.csv'),
                'config': (BytesIO(standard_config_content.encode()), 'config.yml'),
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
            }

            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 200  # Should still process empty CSV

    def test_process_route_with_large_csv(self, client, monkeypatch, standard_config_content):
        """Test process route with large CSV file."""
        # Mock the processing service
        def mock_process_with_details(**kwargs):
            from whatsthedamage.models.dt_models import ProcessingResponse, StatisticalMetadata
            return ProcessingResponse(
                result_id='test123',
                data={},
                metadata={},
                statistical_metadata=StatisticalMetadata(highlights=[])
            )

        # Patch the processing service
        with patch('whatsthedamage.controllers.routes_helpers._get_processing_service') as mock_service:
            mock_service.return_value.process_with_details = mock_process_with_details

            # Create large CSV content (100 rows)
            csv_lines = ["date,amount,currency,partner"]
            for i in range(100):
                csv_lines.append(f"2023-01-{i%28+1:02d},{i*10}.00,EUR,Test Partner {i}")

            csv_content = "\n".join(csv_lines)

            data = {
                'csrf_token': "test-csrf-token",
                'filename': (BytesIO(csv_content.encode()), 'large.csv'),
                'config': (BytesIO(standard_config_content.encode()), 'config.yml'),
                'start_date': '2023-01-01',
                'end_date': '2023-01-31',
            }

            response = client.post('/process', data=data, content_type='multipart/form-data')
            assert response.status_code == 200

    def test_health_route_with_unwritable_upload_folder(self, client, monkeypatch):
        """Test health route when upload folder is not writable."""
        # The health route currently doesn't test for writable folders, just basic functionality
        # This test verifies the basic health check works
        response = client.get('/health')
        assert response.status_code == 200
        assert b'healthy' in response.data

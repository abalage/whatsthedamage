"""
Tests for API error handlers.
"""
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from pydantic import ValidationError
from whatsthedamage.api.error_handlers import (
    handle_bad_request,
    handle_file_not_found,
    handle_validation_error,
    handle_value_error,
    handle_request_entity_too_large,
    handle_generic_exception
)


def test_handle_bad_request(client):
    """Test BadRequest handler returns correct ErrorResponse."""
    with client.application.app_context():
        error = BadRequest("Invalid data")
        response, status_code = handle_bad_request(error)
        
        assert status_code == 400
        data = response.get_json()
        assert data['code'] == 400
        assert data['message'] == "Bad Request"
        assert "Invalid data" in data['details']['error']


def test_handle_file_not_found(client):
    """Test FileNotFoundError handler returns correct ErrorResponse."""
    with client.application.app_context():
        error = FileNotFoundError("config.yml not found")
        response, status_code = handle_file_not_found(error)
        
        assert status_code == 400
        data = response.get_json()
        assert data['code'] == 400
        assert data['message'] == "File Not Found"
        assert "config.yml not found" in data['details']['error']


def test_handle_validation_error(client):
    """Test Pydantic ValidationError handler returns correct ErrorResponse."""
    with client.application.app_context():
        # Create a simple Pydantic model that will fail validation
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            age: int = Field(gt=0)
        
        try:
            TestModel(age=-1)
        except ValidationError as e:
            response, status_code = handle_validation_error(e)
            
            assert status_code == 400
            data = response.get_json()
            assert data['code'] == 400
            assert data['message'] == "Validation Error"
            assert 'errors' in data['details']
            assert len(data['details']['errors']) > 0


def test_handle_value_error(client):
    """Test ValueError handler returns correct ErrorResponse."""
    with client.application.app_context():
        error = ValueError("CSV file is empty")
        response, status_code = handle_value_error(error)
        
        assert status_code == 422
        data = response.get_json()
        assert data['code'] == 422
        assert data['message'] == "Unprocessable Entity"
        assert "CSV file is empty" in data['details']['error']


def test_handle_request_entity_too_large(client):
    """Test RequestEntityTooLarge handler returns correct ErrorResponse."""
    with client.application.app_context():
        error = RequestEntityTooLarge("File too large")
        response, status_code = handle_request_entity_too_large(error)
        
        assert status_code == 413
        data = response.get_json()
        assert data['code'] == 413
        assert data['message'] == "Request Entity Too Large"


def test_handle_generic_exception(client):
    """Test generic Exception handler returns correct ErrorResponse."""
    with client.application.app_context():
        error = RuntimeError("Something went wrong")
        response, status_code = handle_generic_exception(error)
        
        assert status_code == 500
        data = response.get_json()
        assert data['code'] == 500
        assert data['message'] == "Internal Server Error"
        assert data['details']['error'] == "An unexpected error occurred"


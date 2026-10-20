"""
Tests for API error handlers.

All handlers produce the canonical API error shape: a JSON body with
an ``error`` message (plus ``details`` for validation errors). The
exception text of unexpected errors is never exposed.
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
    """Test BadRequest handler returns the request description."""
    with client.application.app_context():
        error = BadRequest("Invalid data")
        response, status_code = handle_bad_request(error)

        assert status_code == 400
        data = response.get_json()
        assert "Invalid data" in data['error']


def test_handle_file_not_found(client):
    """Test FileNotFoundError handler returns a generic message."""
    with client.application.app_context():
        error = FileNotFoundError("config.yml not found")
        response, status_code = handle_file_not_found(error)

        assert status_code == 400
        data = response.get_json()
        assert data['error'] == "File not found"


def test_handle_validation_error(client):
    """Test Pydantic ValidationError handler returns error details."""
    with client.application.app_context():
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            age: int = Field(gt=0)

        try:
            TestModel(age=-1)
        except ValidationError as e:
            response, status_code = handle_validation_error(e)

            assert status_code == 400
            data = response.get_json()
            assert data['error'] == "Validation Error"
            assert len(data['details']) > 0


def test_handle_value_error(client):
    """Test ValueError handler returns the controlled message."""
    with client.application.app_context():
        error = ValueError("CSV file is empty")
        response, status_code = handle_value_error(error)

        assert status_code == 422
        data = response.get_json()
        assert "CSV file is empty" in data['error']


def test_handle_request_entity_too_large(client):
    """Test RequestEntityTooLarge handler returns the description."""
    with client.application.app_context():
        error = RequestEntityTooLarge("File too large")
        response, status_code = handle_request_entity_too_large(error)

        assert status_code == 413
        data = response.get_json()
        assert "File too large" in data['error']


def test_handle_generic_exception(client):
    """Test generic Exception handler hides the exception text."""
    with client.application.app_context():
        error = RuntimeError("Something went wrong")
        response, status_code = handle_generic_exception(error)

        assert status_code == 500
        data = response.get_json()
        assert data['error'] == "Internal Server Error"
        assert "Something went wrong" not in data['error']

"""Tests for OpenAPI specification and schema validation.

This module tests that the OpenAPI schema is valid, complete, and correctly
served by the API endpoint.
"""
import pytest
import json
from whatsthedamage.api.v2.schema import get_openapi_schema


class TestOpenApiSchemaStructure:
    """Test suite for OpenAPI schema structure validation."""

    def test_schema_is_valid_openapi_3_0(self):
        """Test that schema has correct OpenAPI version."""
        schema = get_openapi_schema()
        assert schema["openapi"] == "3.0.3"

    def test_schema_has_info(self):
        """Test that schema has info section."""
        schema = get_openapi_schema()
        assert "info" in schema
        assert schema["info"]["title"] == "whatsthedamage API v2"
        assert schema["info"]["version"] == "2.0.0"
        assert "description" in schema["info"]

    def test_schema_has_servers(self):
        """Test that schema has servers section."""
        schema = get_openapi_schema()
        assert "servers" in schema
        assert len(schema["servers"]) > 0
        assert schema["servers"][0]["url"] == "/api/v2"

    def test_schema_has_paths(self):
        """Test that schema has paths section with all endpoints."""
        schema = get_openapi_schema()
        assert "paths" in schema
        paths = schema["paths"]
        
        # Check all 11 endpoints are present
        expected_paths = [
            "/process",
            "/results/{result_id}",
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/months",
            "/results/{result_id}/accounts/{account_id}/months/{month_id}/categories",
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions",
            "/recalculate-statistics",
            "/categories",
            "/categories/cost-of-living",
            "/csv-profiles",
            "/csv-profiles/{profile_id}",
            "/openapi.json"
        ]
        
        for path in expected_paths:
            assert path in paths, f"Path {path} not found in schema"

    def test_schema_has_components(self):
        """Test that schema has components section with schemas."""
        schema = get_openapi_schema()
        assert "components" in schema
        assert "schemas" in schema["components"]
        
        schemas = schema["components"]["schemas"]
        # Check key schemas are present
        expected_schemas = [
            "CategoryDefinition",
            "CsvProfile",
            "ProcessingRequest",
            "RecalculateStatisticsRequest",
            "AmountField",
            "DateField",
            "DetailRow",
            "AggregatedRow",
            "DetailedResponse",
            "ErrorResponse",
            "ResultsApiResponse",
            "CategoryMonthsApiResponse",
            "MonthCategoriesApiResponse",
            "CategoryMonthTransactionsApiResponse",
            "RecalculateApiResponse"
        ]
        
        for schema_name in expected_schemas:
            assert schema_name in schemas, f"Schema {schema_name} not found in components"


class TestOpenApiSchemaContent:
    """Test suite for OpenAPI schema content validation."""

    def test_process_endpoint_has_post_method(self):
        """Test that /process endpoint has POST method."""
        schema = get_openapi_schema()
        assert "post" in schema["paths"]["/process"]

    def test_results_endpoint_has_get_method(self):
        """Test that /results/{result_id} endpoint has GET method."""
        schema = get_openapi_schema()
        assert "get" in schema["paths"]["/results/{result_id}"]

    def test_drilldown_endpoints_have_get_method(self):
        """Test that all drilldown endpoints have GET method."""
        schema = get_openapi_schema()
        
        drilldown_paths = [
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/months",
            "/results/{result_id}/accounts/{account_id}/months/{month_id}/categories",
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/months/{month_id}/transactions"
        ]
        
        for path in drilldown_paths:
            assert "get" in schema["paths"][path], f"GET method not found for {path}"

    def test_recalculate_endpoint_has_post_method(self):
        """Test that /recalculate-statistics endpoint has POST method."""
        schema = get_openapi_schema()
        assert "post" in schema["paths"]["/recalculate-statistics"]

    def test_category_endpoints_have_get_method(self):
        """Test that category endpoints have GET method."""
        schema = get_openapi_schema()
        assert "get" in schema["paths"]["/categories"]
        assert "get" in schema["paths"]["/categories/cost-of-living"]

    def test_csv_profile_endpoints_have_get_method(self):
        """Test that CSV profile endpoints have GET method."""
        schema = get_openapi_schema()
        assert "get" in schema["paths"]["/csv-profiles"]
        assert "get" in schema["paths"]["/csv-profiles/{profile_id}"]

    def test_processing_request_has_all_fields(self):
        """Test that ProcessingRequest schema has all required fields."""
        schema = get_openapi_schema()
        processing_request = schema["components"]["schemas"]["ProcessingRequest"]
        
        required_fields = ["csv_file"]
        assert processing_request["required"] == required_fields
        
        all_fields = [
            "csv_file",
            "config_file",
            "start_date",
            "end_date",
            "date_format",
            "ml_enabled",
            "category_filter",
            "cache_ttl",
            "csv_profile_id"
        ]
        
        for field in all_fields:
            assert field in processing_request["properties"], f"Field {field} not found in ProcessingRequest"

    def test_error_response_has_correct_structure(self):
        """Test that ErrorResponse schema has correct structure."""
        schema = get_openapi_schema()
        error_response = schema["components"]["schemas"]["ErrorResponse"]
        
        assert error_response["required"] == ["status", "error"]
        assert "status" in error_response["properties"]
        assert "error" in error_response["properties"]
        
        error_properties = error_response["properties"]["error"]
        assert error_properties["required"] == ["code", "message"]
        assert "code" in error_properties["properties"]
        assert "message" in error_properties["properties"]
        assert "details" in error_properties["properties"]

    def test_schema_is_valid_json(self):
        """Test that schema can be serialized to JSON."""
        schema = get_openapi_schema()
        # This will raise an exception if the schema is not JSON-serializable
        json_str = json.dumps(schema)
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed == schema


class TestOpenApiEndpoint:
    """Test suite for /api/v2/openapi.json endpoint."""

    def test_openapi_endpoint_returns_200(self, api_client_with_mock):
        """Test that GET /api/v2/openapi.json returns 200."""
        response = api_client_with_mock.get('/api/v2/openapi.json')
        assert response.status_code == 200

    def test_openapi_endpoint_returns_json(self, api_client_with_mock):
        """Test that GET /api/v2/openapi.json returns valid JSON."""
        response = api_client_with_mock.get('/api/v2/openapi.json')
        data = response.get_json()
        assert data is not None
        assert isinstance(data, dict)

    def test_openapi_endpoint_returns_complete_schema(self, api_client_with_mock):
        """Test that GET /api/v2/openapi.json returns complete schema."""
        response = api_client_with_mock.get('/api/v2/openapi.json')
        data = response.get_json()
        
        # Verify basic structure
        assert data["openapi"] == "3.0.3"
        assert "info" in data
        assert "paths" in data
        assert "components" in data
        
        # Verify all endpoints are present
        assert "/process" in data["paths"]
        assert "/results/{result_id}" in data["paths"]
        assert "/categories" in data["paths"]
        assert "/csv-profiles" in data["paths"]
        assert "/openapi.json" in data["paths"]

    def test_openapi_endpoint_returns_valid_openapi(self, api_client_with_mock):
        """Test that GET /api/v2/openapi.json returns valid OpenAPI spec."""
        response = api_client_with_mock.get('/api/v2/openapi.json')
        data = response.get_json()
        
        # Check OpenAPI version
        assert data.get("openapi") == "3.0.3"
        
        # Check info section
        info = data.get("info", {})
        assert "title" in info
        assert "version" in info
        assert "description" in info
        
        # Check servers
        servers = data.get("servers", [])
        assert len(servers) > 0

    def test_openapi_schema_matches_function_output(self, api_client_with_mock):
        """Test that /api/v2/openapi.json response matches get_openapi_schema()."""
        # Get schema from endpoint
        response = api_client_with_mock.get('/api/v2/openapi.json')
        endpoint_schema = response.get_json()
        
        # Get schema from function
        function_schema = get_openapi_schema()
        
        # They should be identical
        assert endpoint_schema == function_schema

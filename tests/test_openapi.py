"""Tests for OpenAPI specification and schema validation.

This module tests that the OpenAPI schema is valid, complete, and
correctly served by the API endpoint. It also verifies that every
registered v2 API route and method is documented in the schema.
"""
import re
import json
from whatsthedamage.api.v2.schema import get_openapi_schema


def _documented_path(rule: str) -> str:
    """Convert a Flask URL rule to its OpenAPI path form.

    Args:
        rule: Flask URL rule (e.g. /api/v2/transactions/<int:id>).

    Returns:
        OpenAPI path (e.g. /transactions/{id}).
    """
    path = rule[len("/api/v2"):]
    return re.sub(r"<(?:[^:>]*:)?(\w+)>", r"{\1}", path)


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

        expected_paths = [
            "/auth/register",
            "/auth/login",
            "/auth/logout",
            "/auth/me",
            "/auth/reset-password",
            "/auth/csrf-token",
            "/processing-results",
            "/processing-results/{result_id}",
            "/transactions",
            "/transactions/{transaction_id}",
            "/transactions/aggregate",
            "/corrections",
            "/corrections/{correction_id}",
            "/recalculate-statistics",
            "/categories",
            "/categories/cost-of-living",
            "/csv-profiles",
            "/csv-profiles/{profile_id}",
            "/openapi.json",
        ]

        for path in expected_paths:
            assert path in paths, f"Path {path} not found in schema"

    def test_schema_has_components(self):
        """Test that schema has components section with schemas."""
        schema = get_openapi_schema()
        assert "components" in schema
        assert "schemas" in schema["components"]

        schemas = schema["components"]["schemas"]
        expected_schemas = [
            "ErrorResponse",
            "MessageResponse",
            "CategoryDefinition",
            "CsvProfile",
            "UserSummary",
            "UserDetail",
            "RegisterRequest",
            "RegisterResponse",
            "LoginRequest",
            "LoginResponse",
            "MeResponse",
            "ResetPasswordRequest",
            "ResetPasswordResponse",
            "CsrfTokenResponse",
            "ProcessingRequest",
            "ProcessingResultListItem",
            "ProcessingResultCreated",
            "ProcessingResultMetadata",
            "TransactionApiResponse",
            "CreateTransactionRequest",
            "UpdateTransactionRequest",
            "ListTransactionsResponse",
            "AggregatedTransactionsResponse",
            "CorrectionApiResponse",
            "CreateCorrectionRequest",
            "UpdateCorrectionRequest",
            "ListCorrectionsResponse",
            "RecalculateStatisticsRequest",
            "RecalculateApiResponse",
        ]

        for schema_name in expected_schemas:
            assert schema_name in schemas, (
                f"Schema {schema_name} not found in components"
            )

    def test_all_schema_refs_resolve(self):
        """Test that every schema reference resolves to a component."""
        schema = get_openapi_schema()
        refs = set(
            re.findall(
                r"#/components/schemas/(\w+)", json.dumps(schema)
            )
        )
        defined = set(schema["components"]["schemas"].keys())
        unresolved = refs - defined
        assert not unresolved, f"Unresolved refs: {unresolved}"


class TestOpenApiSchemaContent:
    """Test suite for OpenAPI schema content validation."""

    def test_auth_endpoints_have_correct_methods(self):
        """Test that auth endpoints document the correct methods."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        assert "post" in paths["/auth/register"]
        assert "post" in paths["/auth/login"]
        assert "post" in paths["/auth/logout"]
        assert "get" in paths["/auth/me"]
        assert "post" in paths["/auth/reset-password"]
        assert "get" in paths["/auth/csrf-token"]

    def test_processing_results_endpoints_have_correct_methods(self):
        """Test that processing result endpoints document methods."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        assert "post" in paths["/processing-results"]
        assert "get" in paths["/processing-results"]
        assert "get" in paths["/processing-results/{result_id}"]

    def test_transaction_endpoints_have_correct_methods(self):
        """Test that transaction endpoints document the correct methods."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        assert "get" in paths["/transactions"]
        assert "post" in paths["/transactions"]
        for method in ("get", "put", "delete"):
            assert method in paths["/transactions/{transaction_id}"], (
                f"{method.upper()} not documented for transaction detail"
            )
        assert "get" in paths["/transactions/aggregate"]

    def test_correction_endpoints_have_correct_methods(self):
        """Test that correction endpoints document the correct methods."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        assert "get" in paths["/corrections"]
        assert "post" in paths["/corrections"]
        for method in ("get", "put", "delete"):
            assert method in paths["/corrections/{correction_id}"], (
                f"{method.upper()} not documented for correction detail"
            )

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
        processing_request = schema["components"]["schemas"][
            "ProcessingRequest"
        ]

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
            "csv_profile_id",
        ]

        for field in all_fields:
            assert field in processing_request["properties"], (
                f"Field {field} not found in ProcessingRequest"
            )

    def test_error_response_has_correct_structure(self):
        """Test that ErrorResponse schema matches the Pydantic model."""
        schema = get_openapi_schema()
        error_response = schema["components"]["schemas"][
            "ErrorResponse"
        ]

        assert error_response["required"] == ["code", "message"]
        properties = error_response["properties"]
        assert properties["code"]["type"] == "integer"
        assert properties["message"]["type"] == "string"
        assert "details" in properties

    def test_authenticated_operations_declare_security(self):
        """Test that protected operations require cookie auth."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        protected = [
            ("/transactions", "get"),
            ("/transactions", "post"),
            ("/transactions/{transaction_id}", "put"),
            ("/transactions/{transaction_id}", "delete"),
            ("/processing-results", "post"),
            ("/corrections", "post"),
            ("/auth/logout", "post"),
        ]
        for path, method in protected:
            operation = paths[path][method]
            assert operation.get("security") == [{"cookieAuth": []}], (
                f"{method.upper()} {path} must declare cookieAuth"
            )

    def test_public_auth_operations_have_no_security(self):
        """Test that public auth operations do not require a session."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        for path, method in [
            ("/auth/register", "post"),
            ("/auth/login", "post"),
            ("/auth/reset-password", "post"),
        ]:
            operation = paths[path][method]
            assert "security" not in operation, (
                f"{method.upper()} {path} should be public"
            )

    def test_schema_is_valid_json(self):
        """Test that schema can be serialized to JSON."""
        schema = get_openapi_schema()
        # This will raise an exception if the schema is not
        # JSON-serializable
        json_str = json.dumps(schema)
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed == schema


class TestOpenApiRouteCoverage:
    """Test suite verifying the schema covers registered routes."""

    def test_schema_documents_all_v2_routes(self, api_client_with_mock):
        """Test that every registered v2 route appears in the schema."""
        schema = get_openapi_schema()
        documented = set(schema["paths"].keys())

        for rule in api_client_with_mock.application.url_map.iter_rules():
            if not rule.rule.startswith("/api/v2"):
                continue
            path = _documented_path(rule.rule)
            assert path in documented, (
                f"Route {rule.rule} is not documented in the "
                f"OpenAPI schema"
            )

    def test_schema_documents_all_v2_methods(self, api_client_with_mock):
        """Test that every v2 route's methods are documented."""
        schema = get_openapi_schema()
        paths = schema["paths"]

        for rule in api_client_with_mock.application.url_map.iter_rules():
            if not rule.rule.startswith("/api/v2"):
                continue
            path = _documented_path(rule.rule)
            for method in rule.methods:
                if method in ("HEAD", "OPTIONS"):
                    continue
                assert method.lower() in paths[path], (
                    f"{method} {rule.rule} is not documented in "
                    f"the OpenAPI schema"
                )


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

    def test_openapi_endpoint_returns_complete_schema(
        self, api_client_with_mock
    ):
        """Test that GET /api/v2/openapi.json returns complete schema."""
        response = api_client_with_mock.get('/api/v2/openapi.json')
        data = response.get_json()

        # Verify basic structure
        assert data["openapi"] == "3.0.3"
        assert "info" in data
        assert "paths" in data
        assert "components" in data

        # Verify key endpoints are present
        assert "/auth/register" in data["paths"]
        assert "/processing-results" in data["paths"]
        assert "/transactions" in data["paths"]
        assert "/categories" in data["paths"]
        assert "/csv-profiles" in data["paths"]
        assert "/openapi.json" in data["paths"]

    def test_openapi_endpoint_returns_valid_openapi(
        self, api_client_with_mock
    ):
        """Test that GET /api/v2/openapi.json returns valid OpenAPI."""
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

    def test_openapi_schema_matches_function_output(
        self, api_client_with_mock
    ):
        """Test that /api/v2/openapi.json response matches schema."""
        # Get schema from endpoint
        response = api_client_with_mock.get('/api/v2/openapi.json')
        endpoint_schema = response.get_json()

        # Get schema from function
        function_schema = get_openapi_schema()

        # They should be identical
        assert endpoint_schema == function_schema

"""OpenAPI 3.0 schema for whatsthedamage v2 API.

This module defines the OpenAPI specification for the v2 API endpoints.
V2 API provides transaction-level data for authenticated users, with
processing results, transaction CRUD, corrections, and statistics.
"""
from typing import Any


def _ref(name: str) -> dict[str, Any]:
    """Build a schema reference for a named component.

    Args:
        name: Component schema name.

    Returns:
        Reference object pointing into components/schemas.
    """
    return {"$ref": f"#/components/schemas/{name}"}


def _json_content(schema: dict[str, Any]) -> dict[str, Any]:
    """Build an application/json content block.

    Args:
        schema: JSON schema of the response or request body.

    Returns:
        Content mapping for an OpenAPI response or requestBody.
    """
    return {
        "content": {
            "application/json": {"schema": schema}
        }
    }


def _ok(desc: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Build a success response with a JSON schema.

    Args:
        desc: Response description.
        schema: JSON schema of the response body.

    Returns:
        OpenAPI response object.
    """
    response: dict[str, Any] = {"description": desc}
    response.update(_json_content(schema))
    return response


def _error(desc: str) -> dict[str, Any]:
    """Build an error response referencing the ErrorResponse schema.

    Args:
        desc: Response description.

    Returns:
        OpenAPI response object.
    """
    return _ok(desc, _ref("ErrorResponse"))


def _errors(**descriptions: str) -> dict[str, Any]:
    """Build error responses keyed by HTTP status code.

    Args:
        descriptions: Status code to description mapping.

    Returns:
        OpenAPI responses mapping.
    """
    return {
        code: _error(desc) for code, desc in descriptions.items()
    }


def _param(
    name: str,
    place: str,
    desc: str,
    param_type: str = "string",
    required: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Build an OpenAPI parameter object.

    Args:
        name: Parameter name.
        place: Parameter location (query or path).
        desc: Parameter description.
        param_type: Parameter JSON type.
        required: Whether the parameter is required.
        extra: Additional schema attributes (default, enum, format).

    Returns:
        OpenAPI parameter object.
    """
    schema: dict[str, Any] = {"type": param_type}
    schema.update(extra)
    return {
        "name": name,
        "in": place,
        "required": required,
        "description": desc,
        "schema": schema,
    }


def _body(schema_name: str, required: bool = True) -> dict[str, Any]:
    """Build a JSON request body referencing a component schema.

    Args:
        schema_name: Component schema name.
        required: Whether the request body is required.

    Returns:
        OpenAPI requestBody object.
    """
    body: dict[str, Any] = {"required": required}
    body.update(_json_content(_ref(schema_name)))
    return body


def _security() -> list[dict[str, Any]]:
    """Build the cookie authentication security requirement.

    Returns:
        Security requirement list for authenticated operations.
    """
    return [{"cookieAuth": []}]


def get_openapi_schema() -> dict[str, Any]:
    """Generate OpenAPI 3.0 schema for v2 API.

    Returns:
        dict: OpenAPI 3.0 specification.
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "whatsthedamage API v2",
            "description": (
                "REST API for processing bank transaction CSV exports. "
                "V2 provides transaction-level data with processing "
                "results, transaction CRUD, corrections, aggregation, "
                "and statistical analysis. Requires user "
                "authentication; all data is scoped to the "
                "authenticated user."
            ),
            "version": "2.0.0",
            "contact": {
                "name": "whatsthedamage",
                "url": "https://github.com/abalage/whatsthedamage"
            },
            "license": {
                "name": "GPLv3",
                "url": "https://www.gnu.org/licenses/gpl-3.0.html"
            }
        },
        "servers": [
            {
                "url": "/api/v2",
                "description": "V2 API base path"
            }
        ],
        "tags": [
            {"name": "Authentication", "description": (
                "User registration, login, logout, and password reset"
            )},
            {"name": "Processing Results", "description": (
                "CSV import and processing result metadata"
            )},
            {"name": "Transactions", "description": (
                "Transaction entity CRUD, listing, and aggregation"
            )},
            {"name": "Corrections", "description": (
                "User transaction corrections"
            )},
            {"name": "Statistics", "description": (
                "Statistical highlight calculation"
            )},
            {"name": "Categories", "description": (
                "Category definitions"
            )},
            {"name": "CSV Profiles", "description": (
                "CSV bank-format profile definitions"
            )},
            {"name": "Documentation", "description": (
                "API documentation"
            )},
        ],
        "paths": {
            "/auth/register": {
                "post": {
                    "summary": "Register a new user account",
                    "description": (
                        "Creates a user with username and password, "
                        "generates a one-time recovery code, and "
                        "creates an initial session."
                    ),
                    "operationId": "register",
                    "tags": ["Authentication"],
                    "requestBody": _body("RegisterRequest"),
                    "responses": {
                        "201": _ok(
                            "User registered",
                            _ref("RegisterResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Validation error",
                                "409": "Username already exists",
                                "422": "Password too weak",
                            }
                        ),
                    },
                }
            },
            "/auth/login": {
                "post": {
                    "summary": "Authenticate a user and create a "
                               "session",
                    "description": (
                        "Verifies credentials and creates a session "
                        "token cookie. Rate limited to 5 attempts "
                        "per 15 minutes per username and IP "
                        "combination."
                    ),
                    "operationId": "login",
                    "tags": ["Authentication"],
                    "requestBody": _body("LoginRequest"),
                    "responses": {
                        "200": _ok(
                            "User logged in",
                            _ref("LoginResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Validation error",
                                "401": "Invalid credentials",
                                "429": "Too many login attempts",
                            }
                        ),
                    },
                }
            },
            "/auth/logout": {
                "post": {
                    "summary": "Log out the current user",
                    "description": (
                        "Revokes the current session and clears the "
                        "session cookie. Requires the X-CSRF-Token "
                        "header."
                    ),
                    "operationId": "logout",
                    "tags": ["Authentication"],
                    "security": _security(),
                    "responses": {
                        "200": _ok(
                            "User logged out",
                            _ref("MessageResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Invalid or missing CSRF token",
                            }
                        ),
                    },
                }
            },
            "/auth/me": {
                "get": {
                    "summary": "Get current user information",
                    "description": (
                        "Returns the authenticated user's details and "
                        "a CSRF token when the session does not have "
                        "one yet."
                    ),
                    "operationId": "getMe",
                    "tags": ["Authentication"],
                    "security": _security(),
                    "responses": {
                        "200": _ok(
                            "Current user information",
                            _ref("MeResponse")
                        ),
                        **_errors(**{"401": "Not authenticated"}),
                    },
                }
            },
            "/auth/reset-password": {
                "post": {
                    "summary": "Reset password using a recovery code",
                    "description": (
                        "Public endpoint. The recovery code is "
                        "single-use and a new one is issued on "
                        "success. All existing sessions are "
                        "invalidated. Rate limited to 5 attempts "
                        "per 15 minutes per IP address."
                    ),
                    "operationId": "resetPassword",
                    "tags": ["Authentication"],
                    "requestBody": _body("ResetPasswordRequest"),
                    "responses": {
                        "200": _ok(
                            "Password reset",
                            _ref("ResetPasswordResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Validation error",
                                "401": "Invalid username or recovery "
                                       "code",
                                "422": "Password too weak",
                                "429": "Too many attempts",
                            }
                        ),
                    },
                }
            },
            "/auth/csrf-token": {
                "get": {
                    "summary": "Get a new CSRF token",
                    "description": (
                        "Mints a CSRF token for the current session. "
                        "Send it in the X-CSRF-Token header on "
                        "state-changing requests (POST, PUT, DELETE)."
                    ),
                    "operationId": "getCsrfToken",
                    "tags": ["Authentication"],
                    "security": _security(),
                    "responses": {
                        "200": _ok(
                            "CSRF token generated",
                            _ref("CsrfTokenResponse")
                        ),
                        **_errors(**{"401": "Not authenticated"}),
                    },
                }
            },
            "/processing-results": {
                "post": {
                    "summary": "Create a transaction processing result",
                    "description": (
                        "Uploads a CSV file, processes and persists "
                        "the transactions for the authenticated user, "
                        "and returns processing result metadata only. "
                        "Requires the X-CSRF-Token header."
                    ),
                    "operationId": "createProcessingResult",
                    "tags": ["Processing Results"],
                    "security": _security(),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": _ref("ProcessingRequest")
                            }
                        },
                    },
                    "responses": {
                        "201": _ok(
                            "Processing result created",
                            _ref("ProcessingResultCreated")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "409": "Duplicate transaction",
                                "422": "CSV parsing or validation "
                                       "error",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "get": {
                    "summary": "List transaction processing results",
                    "description": (
                        "Returns a paginated list of the authenticated "
                        "user's processing results."
                    ),
                    "operationId": "listProcessingResults",
                    "tags": ["Processing Results"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "limit", "query",
                            "Maximum number of results to return",
                            "integer", default=100
                        ),
                        _param(
                            "offset", "query",
                            "Pagination offset",
                            "integer", default=0
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "List of processing results",
                            {
                                "type": "array",
                                "items": _ref(
                                    "ProcessingResultListItem"
                                ),
                            }
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/processing-results/{result_id}": {
                "get": {
                    "summary": "Get a processing result's metadata",
                    "description": (
                        "Returns metadata only. Transaction data is "
                        "fetched via the /transactions endpoint using "
                        "the result_id filter."
                    ),
                    "operationId": "getProcessingResult",
                    "tags": ["Processing Results"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "result_id", "path",
                            "UUID of the processing result",
                            required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Processing result metadata",
                            _ref("ProcessingResultMetadata")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Result belongs to another "
                                       "user",
                                "404": "Processing result not found",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/transactions": {
                "get": {
                    "summary": "List transactions",
                    "description": (
                        "Returns a paginated, filterable list of the "
                        "authenticated user's Transaction entities."
                    ),
                    "operationId": "listTransactions",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "limit", "query",
                            "Maximum number of transactions to "
                            "return",
                            "integer", default=100
                        ),
                        _param(
                            "offset", "query",
                            "Pagination offset",
                            "integer", default=0
                        ),
                        _param(
                            "start_date", "query",
                            "Filter by start date (YYYY-MM-DD)",
                            format="date"
                        ),
                        _param(
                            "end_date", "query",
                            "Filter by end date (YYYY-MM-DD)",
                            format="date"
                        ),
                        _param(
                            "category_id", "query",
                            "Filter by category ID"
                        ),
                        _param(
                            "account", "query",
                            "Filter by account"
                        ),
                        _param(
                            "partner", "query",
                            "Filter by partner name (searches "
                            "original_partner and partner)"
                        ),
                        _param(
                            "transaction_type", "query",
                            "Filter by transaction type "
                            "(debit/credit)"
                        ),
                        _param(
                            "month", "query",
                            "Filter by month (YYYY-MM)"
                        ),
                        _param(
                            "min_amount", "query",
                            "Filter by minimum amount",
                            "number"
                        ),
                        _param(
                            "max_amount", "query",
                            "Filter by maximum amount",
                            "number"
                        ),
                        _param(
                            "result_id", "query",
                            "Filter by processing result"
                        ),
                        _param(
                            "sort_by", "query",
                            "Field to sort by",
                            default="date",
                            enum=[
                                "date", "amount", "partner",
                                "account", "category",
                            ]
                        ),
                        _param(
                            "sort_order", "query",
                            "Sort order",
                            default="desc",
                            enum=["asc", "desc"]
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Paginated list of transactions",
                            _ref("ListTransactionsResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Invalid query parameters",
                                "401": "Not authenticated",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "post": {
                    "summary": "Create a transaction",
                    "description": (
                        "Creates a single Transaction entity for "
                        "the authenticated user. Requires the "
                        "X-CSRF-Token header. Duplicate transactions "
                        "(same account, date, partner, amount) are "
                        "rejected with 409."
                    ),
                    "operationId": "createTransaction",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "requestBody": _body("CreateTransactionRequest"),
                    "responses": {
                        "201": _ok(
                            "Transaction created",
                            _ref("TransactionApiResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "409": "Duplicate transaction",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/transactions/{transaction_id}": {
                "get": {
                    "summary": "Get a transaction",
                    "description": (
                        "Returns a single Transaction entity owned "
                        "by the authenticated user."
                    ),
                    "operationId": "getTransaction",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "transaction_id", "path",
                            "Transaction identifier",
                            "integer", required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Transaction entity",
                            _ref("TransactionApiResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Transaction belongs to "
                                       "another user",
                                "404": "Transaction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "put": {
                    "summary": "Update a transaction",
                    "description": (
                        "Updates the non-deduplication fields of a "
                        "Transaction entity and applies the "
                        "correction to the original partner for "
                        "future uploads. Requires the X-CSRF-Token "
                        "header."
                    ),
                    "operationId": "updateTransaction",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "transaction_id", "path",
                            "Transaction identifier",
                            "integer", required=True
                        ),
                    ],
                    "requestBody": _body("UpdateTransactionRequest"),
                    "responses": {
                        "200": _ok(
                            "Transaction updated",
                            _ref("TransactionApiResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "403": "Transaction belongs to "
                                       "another user",
                                "404": "Transaction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "delete": {
                    "summary": "Delete a transaction",
                    "description": (
                        "Deletes a Transaction entity owned by the "
                        "authenticated user. Requires the "
                        "X-CSRF-Token header."
                    ),
                    "operationId": "deleteTransaction",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "transaction_id", "path",
                            "Transaction identifier",
                            "integer", required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Transaction deleted",
                            _ref("MessageResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Transaction belongs to "
                                       "another user",
                                "404": "Transaction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/transactions/aggregate": {
                "get": {
                    "summary": "Get aggregated transaction data",
                    "description": (
                        "Groups the authenticated user's transactions "
                        "by category, month, account, or category "
                        "and month for drilldown views, with "
                        "statistical highlights computed over the "
                        "parent matrix scope. Replaces the removed "
                        "per-result drilldown endpoints."
                    ),
                    "operationId": "aggregateTransactions",
                    "tags": ["Transactions"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "group_by", "query",
                            "How to group results",
                            required=True,
                            enum=[
                                "category", "month",
                                "account", "category_month",
                            ]
                        ),
                        _param(
                            "result_id", "query",
                            "Filter by processing result"
                        ),
                        _param(
                            "account", "query",
                            "Filter by account"
                        ),
                        _param(
                            "category_id", "query",
                            "Filter by category"
                        ),
                        _param(
                            "month", "query",
                            "Filter by month (YYYY-MM)"
                        ),
                        _param(
                            "algorithms", "query",
                            "Comma-separated algorithm names "
                            "(default: iqr,pareto)"
                        ),
                        _param(
                            "direction", "query",
                            "Analysis direction",
                            default="columns",
                            enum=["columns", "rows"]
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Aggregated transaction data",
                            _ref("AggregatedTransactionsResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Invalid parameters",
                                "401": "Not authenticated",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/corrections": {
                "get": {
                    "summary": "List corrections",
                    "description": (
                        "Returns a paginated list of the "
                        "authenticated user's corrections, "
                        "optionally filtered by original partner."
                    ),
                    "operationId": "listCorrections",
                    "tags": ["Corrections"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "limit", "query",
                            "Maximum number of corrections to "
                            "return",
                            "integer", default=100
                        ),
                        _param(
                            "offset", "query",
                            "Pagination offset",
                            "integer", default=0
                        ),
                        _param(
                            "original_partner", "query",
                            "Filter by original partner name"
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Paginated list of corrections",
                            _ref("ListCorrectionsResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "post": {
                    "summary": "Create a correction",
                    "description": (
                        "Creates a correction entry for the "
                        "authenticated user. Requires the "
                        "X-CSRF-Token header."
                    ),
                    "operationId": "createCorrection",
                    "tags": ["Corrections"],
                    "security": _security(),
                    "requestBody": _body("CreateCorrectionRequest"),
                    "responses": {
                        "201": _ok(
                            "Correction created",
                            _ref("CorrectionApiResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "409": "Correction already exists",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/corrections/{correction_id}": {
                "get": {
                    "summary": "Get a correction",
                    "description": (
                        "Returns a single correction owned by the "
                        "authenticated user."
                    ),
                    "operationId": "getCorrection",
                    "tags": ["Corrections"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "correction_id", "path",
                            "Correction identifier",
                            "integer", required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Correction entity",
                            _ref("CorrectionApiResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Correction belongs to "
                                       "another user",
                                "404": "Correction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "put": {
                    "summary": "Update a correction",
                    "description": (
                        "Updates a correction owned by the "
                        "authenticated user. Requires the "
                        "X-CSRF-Token header."
                    ),
                    "operationId": "updateCorrection",
                    "tags": ["Corrections"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "correction_id", "path",
                            "Correction identifier",
                            "integer", required=True
                        ),
                    ],
                    "requestBody": _body("UpdateCorrectionRequest"),
                    "responses": {
                        "200": _ok(
                            "Correction updated",
                            _ref("CorrectionApiResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "403": "Correction belongs to "
                                       "another user",
                                "404": "Correction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                },
                "delete": {
                    "summary": "Delete a correction",
                    "description": (
                        "Deletes a correction owned by the "
                        "authenticated user. Requires the "
                        "X-CSRF-Token header."
                    ),
                    "operationId": "deleteCorrection",
                    "tags": ["Corrections"],
                    "security": _security(),
                    "parameters": [
                        _param(
                            "correction_id", "path",
                            "Correction identifier",
                            "integer", required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "Correction deleted",
                            _ref("MessageResponse")
                        ),
                        **_errors(
                            **{
                                "401": "Not authenticated",
                                "403": "Correction belongs to "
                                       "another user",
                                "404": "Correction not found",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/recalculate-statistics": {
                "post": {
                    "summary": "Recalculate statistics",
                    "description": (
                        "Recalculates statistical highlights from "
                        "the persisted transactions of the "
                        "authenticated user. When result_id is "
                        "omitted, all of the user's transactions "
                        "are analyzed."
                    ),
                    "operationId": "recalculateStatistics",
                    "tags": ["Statistics"],
                    "security": _security(),
                    "requestBody": _body("RecalculateStatisticsRequest"),
                    "responses": {
                        "200": _ok(
                            "Recalculated highlights",
                            _ref("RecalculateApiResponse")
                        ),
                        **_errors(
                            **{
                                "400": "Bad request",
                                "401": "Not authenticated",
                                "404": "Processing result not found",
                                "500": "Server error",
                            }
                        ),
                    },
                }
            },
            "/categories": {
                "get": {
                    "summary": "Get all category definitions",
                    "description": (
                        "Returns assignable (non-calculated) category "
                        "definitions. Calculated categories are excluded "
                        "because they cannot be assigned to transactions."
                    ),
                    "operationId": "getCategories",
                    "tags": ["Categories"],
                    "responses": {
                        "200": _ok(
                            "List of category definitions",
                            {
                                "type": "array",
                                "items": _ref("CategoryDefinition"),
                            }
                        )
                    }
                }
            },
            "/categories/cost-of-living": {
                "get": {
                    "summary": "Get cost of living categories",
                    "description": (
                        "Returns cost of living category definitions."
                    ),
                    "operationId": "getCostOfLivingCategories",
                    "tags": ["Categories"],
                    "responses": {
                        "200": _ok(
                            "List of cost of living categories",
                            {
                                "type": "array",
                                "items": _ref("CategoryDefinition"),
                            }
                        )
                    }
                }
            },
            "/csv-profiles": {
                "get": {
                    "summary": "List all CSV profiles",
                    "description": (
                        "Returns all CSV profile definitions."
                    ),
                    "operationId": "getCsvProfiles",
                    "tags": ["CSV Profiles"],
                    "responses": {
                        "200": _ok(
                            "List of CSV profiles",
                            {
                                "type": "array",
                                "items": _ref("CsvProfile"),
                            }
                        )
                    }
                }
            },
            "/csv-profiles/{profile_id}": {
                "get": {
                    "summary": "Get specific CSV profile",
                    "description": "Returns a specific CSV profile.",
                    "operationId": "getCsvProfile",
                    "tags": ["CSV Profiles"],
                    "parameters": [
                        _param(
                            "profile_id", "path",
                            "CSV profile identifier",
                            required=True
                        ),
                    ],
                    "responses": {
                        "200": _ok(
                            "CSV profile",
                            _ref("CsvProfile")
                        ),
                        **_errors(**{"404": "Not found"}),
                    },
                }
            },
            "/openapi.json": {
                "get": {
                    "summary": "Get OpenAPI specification",
                    "description": (
                        "Returns the complete OpenAPI 3.0.3 "
                        "specification."
                    ),
                    "operationId": "getOpenApiSpec",
                    "tags": ["Documentation"],
                    "responses": {
                        "200": _ok(
                            "OpenAPI specification",
                            {"type": "object"}
                        )
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "cookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session_token"
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "HTTP status code"
                        },
                        "message": {
                            "type": "string",
                            "description": (
                                "Human-readable error description"
                            )
                        },
                        "details": {
                            "type": "object",
                            "description": (
                                "Additional error details for "
                                "debugging"
                            )
                        }
                    }
                },
                "MessageResponse": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "example": (
                                "Transaction deleted successfully"
                            )
                        }
                    }
                },
                "CategoryDefinition": {
                    "type": "object",
                    "required": ["id", "default_name", "patterns"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": (
                                "Unique category identifier"
                            ),
                            "example": "grocery"
                        },
                        "default_name": {
                            "type": "string",
                            "description": "Default display name",
                            "example": "Grocery"
                        },
                        "patterns": {
                            "type": "array",
                            "description": "Regex patterns",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                },
                "CsvProfile": {
                    "type": "object",
                    "required": ["id", "name", "csv_config"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "example": "otp-hu"
                        },
                        "name": {
                            "type": "string",
                            "example": "OTP Bank"
                        },
                        "description": {
                            "type": "string"
                        },
                        "version": {
                            "type": "string"
                        },
                        "csv_config": {
                            "type": "object",
                            "properties": {
                                "dialect": {
                                    "type": "string"
                                },
                                "delimiter": {
                                    "type": "string"
                                },
                                "date_attribute_format": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                },
                "UserSummary": {
                    "type": "object",
                    "required": ["id", "username", "created_at"],
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "username": {
                            "type": "string"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    }
                },
                "UserDetail": {
                    "type": "object",
                    "required": ["id", "username", "created_at"],
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "username": {
                            "type": "string"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "last_login_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True
                        },
                        "is_active": {
                            "type": "boolean"
                        },
                        "opt_in_sharing": {
                            "type": "boolean"
                        }
                    }
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {
                            "type": "string"
                        },
                        "password": {
                            "type": "string",
                            "format": "password"
                        }
                    }
                },
                "RegisterResponse": {
                    "type": "object",
                    "required": [
                        "user", "recovery_code", "csrf_token"
                    ],
                    "properties": {
                        "user": _ref("UserSummary"),
                        "recovery_code": {
                            "type": "string",
                            "description": (
                                "One-time recovery code, displayed "
                                "only once and not retrievable later"
                            )
                        },
                        "csrf_token": {
                            "type": "string"
                        },
                        "session_expires_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    }
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {
                            "type": "string"
                        },
                        "password": {
                            "type": "string",
                            "format": "password"
                        },
                        "remember_me": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                },
                "LoginResponse": {
                    "type": "object",
                    "required": ["user", "csrf_token"],
                    "properties": {
                        "user": _ref("UserSummary"),
                        "csrf_token": {
                            "type": "string"
                        },
                        "session_expires_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    }
                },
                "MeResponse": {
                    "type": "object",
                    "required": ["user"],
                    "properties": {
                        "user": _ref("UserDetail"),
                        "csrf_token": {
                            "type": "string",
                            "nullable": True,
                            "description": (
                                "Present only when the session does "
                                "not have a CSRF token yet"
                            )
                        }
                    }
                },
                "ResetPasswordRequest": {
                    "type": "object",
                    "required": [
                        "username", "recovery_code", "new_password"
                    ],
                    "properties": {
                        "username": {
                            "type": "string"
                        },
                        "recovery_code": {
                            "type": "string"
                        },
                        "new_password": {
                            "type": "string",
                            "format": "password"
                        }
                    }
                },
                "ResetPasswordResponse": {
                    "type": "object",
                    "required": ["user", "new_recovery_code"],
                    "properties": {
                        "user": _ref("UserDetail"),
                        "new_recovery_code": {
                            "type": "string",
                            "description": (
                                "New one-time recovery code, "
                                "displayed only once"
                            )
                        }
                    }
                },
                "CsrfTokenResponse": {
                    "type": "object",
                    "required": ["csrf_token"],
                    "properties": {
                        "csrf_token": {
                            "type": "string"
                        }
                    }
                },
                "ProcessingRequest": {
                    "type": "object",
                    "required": ["csv_file"],
                    "properties": {
                        "csv_file": {
                            "type": "string",
                            "format": "binary",
                            "description": "CSV file"
                        },
                        "config_file": {
                            "type": "string",
                            "format": "binary",
                            "description": "Optional YAML config"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "example": "2024-01-01"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "example": "2024-12-31"
                        },
                        "date_format": {
                            "type": "string",
                            "example": "%Y.%m.%d"
                        },
                        "ml_enabled": {
                            "type": "boolean",
                            "default": False
                        },
                        "category_filter": {
                            "type": "string",
                            "example": "grocery"
                        },
                        "csv_profile_id": {
                            "type": "string",
                            "example": "otp-hu"
                        }
                    }
                },
                "ProcessingResultListItem": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": (
                                "Unique identifier for the "
                                "processing result"
                            ),
                            "example": (
                                "550e8400-e29b-41d4-"
                                "a716-446655440000"
                            )
                        },
                        "csv_profile_id": {
                            "type": "string",
                            "nullable": True,
                            "description": (
                                "CSV profile ID used for processing"
                            ),
                            "example": "otp-hu"
                        },
                        "row_count": {
                            "type": "integer",
                            "nullable": True,
                            "description": (
                                "Number of aggregated rows"
                            )
                        },
                        "processing_time": {
                            "type": "number",
                            "nullable": True,
                            "description": (
                                "Processing duration in seconds"
                            )
                        },
                        "ml_enabled": {
                            "type": "boolean",
                            "nullable": True
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "transaction_start_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True,
                            "description": (
                                "Earliest date among the "
                                "transactions linked to this result"
                            )
                        },
                        "transaction_end_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True,
                            "description": (
                                "Latest date among the "
                                "transactions linked to this result"
                            )
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True,
                            "description": (
                                "When the processing result was "
                                "created"
                            )
                        }
                    }
                },
                "ProcessingResultCreated": {
                    "type": "object",
                    "required": ["result_id", "row_count"],
                    "properties": {
                        "result_id": {
                            "type": "string",
                            "description": (
                                "UUID of the created processing "
                                "result"
                            )
                        },
                        "user_id": {
                            "type": "integer"
                        },
                        "csv_profile_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "row_count": {
                            "type": "integer",
                            "description": "Number of aggregated rows"
                        },
                        "transactions_count": {
                            "type": "integer",
                            "description": (
                                "Number of persisted transactions"
                            )
                        },
                        "processing_time": {
                            "type": "number",
                            "description": (
                                "Processing duration in seconds"
                            )
                        },
                        "ml_enabled": {
                            "type": "boolean"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "message": {
                            "type": "string"
                        }
                    }
                },
                "ProcessingResultMetadata": {
                    "type": "object",
                    "required": ["result_id"],
                    "properties": {
                        "result_id": {
                            "type": "string"
                        },
                        "user_id": {
                            "type": "integer"
                        },
                        "csv_profile_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "row_count": {
                            "type": "integer"
                        },
                        "processing_time": {
                            "type": "number",
                            "nullable": True
                        },
                        "ml_enabled": {
                            "type": "boolean",
                            "nullable": True
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True
                        },
                        "transaction_start_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True,
                            "description": (
                                "Earliest date among the "
                                "transactions linked to this result"
                            )
                        },
                        "transaction_end_date": {
                            "type": "string",
                            "format": "date",
                            "nullable": True,
                            "description": (
                                "Latest date among the "
                                "transactions linked to this result"
                            )
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True
                        },
                        "transactions_url": {
                            "type": "string",
                            "description": (
                                "Link to the transactions endpoint "
                                "filtered by this result"
                            )
                        }
                    }
                },
                "TransactionApiResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "result_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "date": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "transaction_type": {"type": "string"},
                        "original_partner": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "account": {"type": "string"},
                        "deduplication_hash": {"type": "string"},
                        "category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "notice": {
                            "type": "string",
                            "nullable": True
                        },
                        "confidence": {
                            "type": "number",
                            "nullable": True
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "required": [
                        "id", "user_id", "date", "transaction_type",
                        "original_partner", "amount", "currency",
                        "account", "deduplication_hash"
                    ]
                },
                "CreateTransactionRequest": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date"
                        },
                        "transaction_type": {"type": "string"},
                        "original_partner": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "account": {"type": "string"},
                        "category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "notice": {
                            "type": "string",
                            "nullable": True
                        },
                        "confidence": {
                            "type": "number",
                            "nullable": True
                        }
                    },
                    "required": [
                        "date", "transaction_type",
                        "original_partner", "amount", "currency",
                        "account"
                    ]
                },
                "UpdateTransactionRequest": {
                    "type": "object",
                    "properties": {
                        "category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "notice": {
                            "type": "string",
                            "nullable": True
                        },
                        "confidence": {
                            "type": "number",
                            "nullable": True
                        }
                    }
                },
                "ListTransactionsResponse": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": _ref("TransactionApiResponse")
                        },
                        "total_count": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"}
                    }
                },
                "AggregatedTransactionsResponse": {
                    "type": "object",
                    "required": ["group_by", "groups", "highlights"],
                    "properties": {
                        "result_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "account": {
                            "type": "string",
                            "nullable": True
                        },
                        "category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "month": {
                            "type": "string",
                            "nullable": True,
                            "example": "2026-09"
                        },
                        "group_by": {
                            "type": "string",
                            "enum": [
                                "category", "month",
                                "account", "category_month"
                            ]
                        },
                        "groups": {
                            "type": "object",
                            "description": (
                                "Group key to transactions in "
                                "the group"
                            ),
                            "additionalProperties": {
                                "type": "array",
                                "items": _ref(
                                    "TransactionApiResponse"
                                )
                            }
                        },
                        "highlights": {
                            "type": "object",
                            "description": (
                                "Group key to statistical "
                                "highlight types"
                            ),
                            "additionalProperties": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "total_count": {"type": "integer"}
                    }
                },
                "CorrectionApiResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "original_partner": {"type": "string"},
                        "corrected_partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_notice": {
                            "type": "string",
                            "nullable": True
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "required": [
                        "id", "user_id", "original_partner"
                    ]
                },
                "CreateCorrectionRequest": {
                    "type": "object",
                    "properties": {
                        "original_partner": {"type": "string"},
                        "corrected_partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_notice": {
                            "type": "string",
                            "nullable": True
                        }
                    },
                    "required": ["original_partner"]
                },
                "UpdateCorrectionRequest": {
                    "type": "object",
                    "properties": {
                        "corrected_partner": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_category_id": {
                            "type": "string",
                            "nullable": True
                        },
                        "corrected_notice": {
                            "type": "string",
                            "nullable": True
                        }
                    }
                },
                "ListCorrectionsResponse": {
                    "type": "object",
                    "properties": {
                        "corrections": {
                            "type": "array",
                            "items": _ref("CorrectionApiResponse")
                        },
                        "total_count": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"}
                    }
                },
                "RecalculateStatisticsRequest": {
                    "type": "object",
                    "required": ["algorithms", "direction"],
                    "properties": {
                        "result_id": {
                            "type": "string",
                            "description": (
                                "Optional processing result to "
                                "scope to. Omitted = all user "
                                "transactions."
                            )
                        },
                        "algorithms": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["rows", "columns"]
                        }
                    }
                },
                "RecalculateApiResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "default": "success"
                        },
                        "result_id": {
                            "type": ["string", "null"],
                            "description": (
                                "Processing result identifier "
                                "(null = all user transactions)"
                            )
                        },
                        "highlights": {
                            "type": "object",
                            "description": (
                                "Statistical highlights keyed by "
                                "cell ID "
                                "'{account}|{month}|{category}'"
                            )
                        },
                        "algorithms": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "direction": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }

"""OpenAPI 3.0 schema for whatsthedamage v2 API.

This module defines the OpenAPI specification for the v2 API endpoints.
V2 API focuses on detailed transaction-level data for DataTables rendering.
"""
from typing import Any


def get_openapi_schema() -> dict[str, Any]:
    """Generate OpenAPI 3.0 schema for v2 API.

    Returns:
        dict: OpenAPI 3.0 specification
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "whatsthedamage API v2",
            "description": (
                "REST API for processing bank transaction CSV exports. "
                "V2 provides detailed transaction-level data with aggregation "
                "for DataTables rendering. Supports regex-based and "
                "ML-based categorization."
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
        "paths": {
            "/transactions": {
                "post": {
                    "summary": "Create transaction processing result",
                    "description": (
                        "Upload a CSV file containing bank transactions "
                        "and receive detailed transaction data grouped by "
                        "category and month. Requires authentication."
                    ),
                    "operationId": "createTransaction",
                    "tags": ["Transactions"],
                    "security": [{"cookieAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "$ref": "#/components/schemas/ProcessingRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Transaction processing result created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DetailedResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Not authenticated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "422": {
                            "description": "Unprocessable entity",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                },
                "get": {
                    "summary": "List transaction processing results",
                    "description": "Get a paginated list of processing results for the authenticated user.",
                    "operationId": "listTransactions",
                    "tags": ["Transactions"],
                    "security": [{"cookieAuth": []}],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 100
                            }
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of processing results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/ProcessingResultListItem"
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Not authenticated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/transactions/{result_id}": {
                "get": {
                    "summary": "Get transaction processing result",
                    "description": "Get a specific processing result by ID.",
                    "operationId": "getTransaction",
                    "tags": ["Transactions"],
                    "security": [{"cookieAuth": []}],
                    "parameters": [
                        {
                            "name": "result_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Processing result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ResultsApiResponse"
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Not authenticated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "403": {
                            "description": "Forbidden (not your result)",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/results/{result_id}": {
                "get": {
                    "summary": "Get processing results",
                    "description": "Retrieve cached processing results.",
                    "operationId": "getResults",
                    "tags": ["Results"],
                    "parameters": [
                        {
                            "name": "result_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ResultsApiResponse"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/months":
                {
                    "get": {
                        "summary": "Get category months",
                        "description": "Get month-by-month aggregation for a category.",
                        "operationId": "getCategoryMonths",
                        "tags": ["Drilldown"],
                        "parameters": [
                            {
                                "name": "result_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            },
                            {
                                "name": "account_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            },
                            {
                                "name": "category_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/CategoryMonthsApiResponse"
                                        }
                                    }
                                }
                            },
                            "404": {
                                "description": "Not found",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            },
                            "500": {
                                "description": "Server error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
            "/results/{result_id}/accounts/{account_id}/months/{month_id}/categories":
                {
                    "get": {
                        "summary": "Get month categories",
                        "description": "Get category-by-category aggregation for a month.",
                        "operationId": "getMonthCategories",
                        "tags": ["Drilldown"],
                        "parameters": [
                            {
                                "name": "result_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            },
                            {
                                "name": "account_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            },
                            {
                                "name": "month_id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MonthCategoriesApiResponse"
                                        }
                                    }
                                }
                            },
                            "404": {
                                "description": "Not found",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            },
                            "500": {
                                "description": "Server error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
            "/results/{result_id}/accounts/{account_id}/categories/{category_id}/"
            "months/{month_id}/transactions": {
                "get": {
                    "summary": "Get category month transactions",
                    "description": "Get individual transaction details.",
                    "operationId": "getCategoryMonthTransactions",
                    "tags": ["Drilldown"],
                    "parameters": [
                        {
                            "name": "result_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "account_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "category_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        },
                        {
                            "name": "month_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/CategoryMonthTransactionsApiResponse"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/recalculate-statistics": {
                "post": {
                    "summary": "Recalculate statistics",
                    "description": "Recalculate statistical highlights.",
                    "operationId": "recalculateStatistics",
                    "tags": ["Statistics"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RecalculateStatisticsRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/RecalculateApiResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/categories": {
                "get": {
                    "summary": "Get all category definitions",
                    "description": "Returns all CategoryDefinition objects.",
                    "operationId": "getCategories",
                    "tags": ["Categories"],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/CategoryDefinition"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/categories/cost-of-living": {
                "get": {
                    "summary": "Get cost of living categories",
                    "description": "Returns cost of living category definitions.",
                    "operationId": "getCostOfLivingCategories",
                    "tags": ["Categories"],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/CategoryDefinition"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/csv-profiles": {
                "get": {
                    "summary": "List all CSV profiles",
                    "description": "Returns all CSV profile definitions.",
                    "operationId": "getCsvProfiles",
                    "tags": ["CSV Profiles"],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/CsvProfile"
                                        }
                                    }
                                }
                            }
                        }
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
                        {
                            "name": "profile_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/CsvProfile"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/openapi.json": {
                "get": {
                    "summary": "Get OpenAPI specification",
                    "description": "Returns complete OpenAPI 3.0.3 specification.",
                    "operationId": "getOpenApiSpec",
                    "tags": ["Documentation"],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
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
                "CategoryDefinition": {
                    "type": "object",
                    "required": ["id", "default_name", "patterns"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique category identifier",
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
                            "description": "Unique identifier for the processing result",
                            "example": "550e8400-e29b-41d4-a716-446655440000"
                        },
                        "csv_profile_id": {
                            "type": "string",
                            "nullable": True,
                            "description": "CSV profile ID used for processing",
                            "example": "otp-hu"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True,
                            "description": "When the processing result was created"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": True,
                            "description": "When the processing result was last updated"
                        }
                    }
                },
                "RecalculateStatisticsRequest": {
                    "type": "object",
                    "required": ["result_id", "algorithms", "direction"],
                    "properties": {
                        "result_id": {
                            "type": "string"
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
                            "type": "string"
                        },
                        "highlights": {
                            "type": "object"
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
                },
                "AmountField": {
                    "type": "object",
                    "required": ["display", "raw"],
                    "properties": {
                        "display": {
                            "type": "string",
                            "example": "HUF -45,600.50"
                        },
                        "raw": {
                            "type": "number",
                            "example": -45600.5
                        }
                    }
                },
                "DateField": {
                    "type": "object",
                    "required": ["display", "timestamp"],
                    "properties": {
                        "display": {
                            "type": "string",
                            "example": "January"
                        },
                        "timestamp": {
                            "type": "integer",
                            "example": 1704067200
                        }
                    }
                },
                "DetailRow": {
                    "type": "object",
                    "required": ["date", "amount", "merchant", "currency"],
                    "properties": {
                        "date": {
                            "$ref": "#/components/schemas/DateField"
                        },
                        "amount": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "merchant": {
                            "type": "string",
                            "example": "TESCO"
                        },
                        "currency": {
                            "type": "string",
                            "example": "HUF"
                        },
                        "type": {
                            "type": "string"
                        },
                        "confidence": {
                            "type": "number"
                        },
                        "notice": {
                            "type": "string"
                        }
                    }
                },
                "AggregatedRow": {
                    "type": "object",
                    "required": ["category_id", "total", "date", "details"],
                    "properties": {
                        "category_id": {
                            "type": "string"
                        },
                        "total": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "date": {
                            "$ref": "#/components/schemas/DateField"
                        },
                        "details": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/DetailRow"
                            }
                        }
                    }
                },
                "DetailedResponse": {
                    "type": "object",
                    "required": ["data", "metadata"],
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/AggregatedRow"
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "result_id": {
                                    "type": "string"
                                },
                                "row_count": {
                                    "type": "integer"
                                },
                                "processing_time": {
                                    "type": "number"
                                },
                                "ml_enabled": {
                                    "type": "boolean"
                                },
                                "date_range": {
                                    "type": "object"
                                },
                                "cache_ttl": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["status", "error"],
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["error"]
                        },
                        "error": {
                            "type": "object",
                            "required": ["code", "message"],
                            "properties": {
                                "code": {
                                    "type": "integer"
                                },
                                "message": {
                                    "type": "string"
                                },
                                "details": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                },
                "Account": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "formatted_id": {
                            "type": "string"
                        },
                        "currency": {
                            "type": "string"
                        },
                        "dt_response": {
                            "type": "object"
                        }
                    }
                },
                "DrilldownUrlInfo": {
                    "type": "object",
                    "properties": {
                        "category_url": {
                            "type": "string"
                        },
                        "category_id": {
                            "type": "string"
                        }
                    }
                },
                "MonthUrlInfo": {
                    "type": "object",
                    "properties": {
                        "month_url": {
                            "type": "string"
                        },
                        "month_id": {
                            "type": "string"
                        }
                    }
                },
                "CellUrlInfo": {
                    "type": "object",
                    "properties": {
                        "cell_url": {
                            "type": "string"
                        },
                        "category_id": {
                            "type": "string"
                        },
                        "month_id": {
                            "type": "string"
                        }
                    }
                },
                "DrilldownUrls": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string"
                        },
                        "category_urls": {
                            "type": "object"
                        },
                        "month_urls": {
                            "type": "object"
                        },
                        "cell_urls": {
                            "type": "object"
                        }
                    }
                },
                "ResultsApiResponse": {
                    "type": "object",
                    "required": [
                        "result_id",
                        "accounts",
                        "highlights",
                        "drilldown_urls_by_account"
                    ],
                    "properties": {
                        "result_id": {
                            "type": "string"
                        },
                        "accounts": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/Account"
                            }
                        },
                        "highlights": {
                            "type": "object"
                        },
                        "drilldown_urls_by_account": {
                            "type": "object"
                        }
                    }
                },
                "MonthData": {
                    "type": "object",
                    "properties": {
                        "month_timestamp": {
                            "type": "integer"
                        },
                        "total": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "row_id": {
                            "type": "string"
                        },
                        "cell_url": {
                            "type": "string"
                        }
                    }
                },
                "CategoryData": {
                    "type": "object",
                    "properties": {
                        "category_id": {
                            "type": "string"
                        },
                        "total": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "row_id": {
                            "type": "string"
                        },
                        "category_url": {
                            "type": "string"
                        }
                    }
                },
                "TransactionDetail": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "$ref": "#/components/schemas/DateField"
                        },
                        "amount": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "merchant": {
                            "type": "string"
                        },
                        "currency": {
                            "type": "string"
                        },
                        "type": {
                            "type": "string"
                        },
                        "confidence": {
                            "type": "number"
                        },
                        "notice": {
                            "type": "string"
                        },
                        "row_id": {
                            "type": "string"
                        },
                        "category_id": {
                            "type": "string"
                        },
                        "month_id": {
                            "type": "string"
                        }
                    }
                },
                "CategoryMonthsApiResponse": {
                    "type": "object",
                    "properties": {
                        "result_id": {
                            "type": "string"
                        },
                        "account_id": {
                            "type": "string"
                        },
                        "account_name": {
                            "type": "string"
                        },
                        "account_formatted_id": {
                            "type": "string"
                        },
                        "account_currency": {
                            "type": "string"
                        },
                        "category_id": {
                            "type": "string"
                        },
                        "data": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/MonthData"
                            }
                        },
                        "highlights": {
                            "type": "object"
                        }
                    }
                },
                "MonthCategoriesApiResponse": {
                    "type": "object",
                    "properties": {
                        "result_id": {
                            "type": "string"
                        },
                        "account_id": {
                            "type": "string"
                        },
                        "account_name": {
                            "type": "string"
                        },
                        "account_formatted_id": {
                            "type": "string"
                        },
                        "account_currency": {
                            "type": "string"
                        },
                        "month_id": {
                            "type": "string"
                        },
                        "month_timestamp": {
                            "type": "integer"
                        },
                        "data": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/CategoryData"
                            }
                        },
                        "highlights": {
                            "type": "object"
                        }
                    }
                },
                "CategoryMonthTransactionsApiResponse": {
                    "type": "object",
                    "properties": {
                        "result_id": {
                            "type": "string"
                        },
                        "account_id": {
                            "type": "string"
                        },
                        "account_name": {
                            "type": "string"
                        },
                        "account_formatted_id": {
                            "type": "string"
                        },
                        "account_currency": {
                            "type": "string"
                        },
                        "category_id": {
                            "type": "string"
                        },
                        "month_id": {
                            "type": "string"
                        },
                        "month_timestamp": {
                            "type": "integer"
                        },
                        "data": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/TransactionDetail"
                            }
                        },
                        "highlights": {
                            "type": "object"
                        }
                    }
                },
                "TransactionApiResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "date": {"type": "string", "format": "date-time"},
                        "transaction_type": {"type": "string"},
                        "original_partner": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "account": {"type": "string"},
                        "deduplication_hash": {"type": "string"},
                        "category_id": {"type": "string", "nullable": True},
                        "partner": {"type": "string", "nullable": True},
                        "notice": {"type": "string", "nullable": True},
                        "confidence": {"type": "number", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "user_id", "date", "transaction_type", "original_partner", "amount", "currency", "account", "deduplication_hash"]
                },
                "CreateTransactionRequest": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "format": "date"},
                        "transaction_type": {"type": "string"},
                        "original_partner": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "account": {"type": "string"},
                        "category_id": {"type": "string", "nullable": True},
                        "partner": {"type": "string", "nullable": True},
                        "notice": {"type": "string", "nullable": True},
                        "confidence": {"type": "number", "nullable": True}
                    },
                    "required": ["date", "transaction_type", "original_partner", "amount", "currency", "account"]
                },
                "UpdateTransactionRequest": {
                    "type": "object",
                    "properties": {
                        "category_id": {"type": "string", "nullable": True},
                        "partner": {"type": "string", "nullable": True},
                        "notice": {"type": "string", "nullable": True},
                        "confidence": {"type": "number", "nullable": True}
                    }
                },
                "ListTransactionsQueryParams": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 100},
                        "offset": {"type": "integer", "default": 0},
                        "start_date": {"type": "string", "format": "date", "nullable": True},
                        "end_date": {"type": "string", "format": "date", "nullable": True},
                        "category_id": {"type": "string", "nullable": True},
                        "account": {"type": "string", "nullable": True},
                        "partner": {"type": "string", "nullable": True},
                        "transaction_type": {"type": "string", "nullable": True},
                        "month": {"type": "string", "nullable": True},
                        "min_amount": {"type": "number", "nullable": True},
                        "max_amount": {"type": "number", "nullable": True},
                        "sort_by": {"type": "string", "default": "date", "enum": ["date", "amount", "partner", "account", "category"]},
                        "sort_order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"}
                    }
                },
                "ListTransactionsResponse": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/TransactionApiResponse"}
                        },
                        "total_count": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"}
                    }
                },
                "CorrectionApiResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "original_partner": {"type": "string"},
                        "corrected_partner": {"type": "string", "nullable": True},
                        "corrected_category_id": {"type": "string", "nullable": True},
                        "corrected_notice": {"type": "string", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["id", "user_id", "original_partner"]
                },
                "CreateCorrectionRequest": {
                    "type": "object",
                    "properties": {
                        "original_partner": {"type": "string"},
                        "corrected_partner": {"type": "string", "nullable": True},
                        "corrected_category_id": {"type": "string", "nullable": True},
                        "corrected_notice": {"type": "string", "nullable": True}
                    },
                    "required": ["original_partner"]
                },
                "UpdateCorrectionRequest": {
                    "type": "object",
                    "properties": {
                        "corrected_partner": {"type": "string", "nullable": True},
                        "corrected_category_id": {"type": "string", "nullable": True},
                        "corrected_notice": {"type": "string", "nullable": True}
                    }
                },
                "ListCorrectionsResponse": {
                    "type": "object",
                    "properties": {
                        "corrections": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/CorrectionApiResponse"}
                        },
                        "total_count": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"}
                    }
                }
            }
        }
    }

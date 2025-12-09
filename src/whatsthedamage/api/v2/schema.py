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
                "for DataTables rendering. Client-side export is handled by DataTables. "
                "Supports both regex-based and ML-based transaction categorization."
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
            "/process": {
                "post": {
                    "summary": "Process CSV transaction file with details",
                    "description": (
                        "Upload a CSV file containing bank transactions and receive "
                        "detailed transaction data grouped by category and month. "
                        "Returns DataTables-compatible JSON for client-side rendering and export. "
                        "Optionally upload a YAML configuration file to customize processing."
                    ),
                    "operationId": "processTransactionsDetailed",
                    "tags": ["Processing"],
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
                        "200": {
                            "description": "Successfully processed transactions with details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DetailedResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid input or file format",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "422": {
                            "description": "Unprocessable entity - CSV processing error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Internal server error",
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
            }
        },
        "components": {
            "schemas": {
                "ProcessingRequest": {
                    "type": "object",
                    "required": ["csv_file"],
                    "properties": {
                        "csv_file": {
                            "type": "string",
                            "format": "binary",
                            "description": "CSV file containing bank transactions"
                        },
                        "config_file": {
                            "type": "string",
                            "format": "binary",
                            "description": "Optional YAML configuration file"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for filtering (format from config, default: %Y.%m.%d)",
                            "example": "2024.01.01"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for filtering (format from config, default: %Y.%m.%d)",
                            "example": "2024.12.31"
                        },
                        "date_format": {
                            "type": "string",
                            "description": "Date format string (Python strptime format). If not provided, uses config default.",
                            "example": "%Y.%m.%d"
                        },
                        "ml_enabled": {
                            "type": "boolean",
                            "default": False,
                            "description": "Enable ML-based categorization instead of regex patterns"
                        },
                        "category_filter": {
                            "type": "string",
                            "description": "Filter results to specific category",
                            "example": "Grocery"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["en", "hu"],
                            "default": "en",
                            "description": "Output language for month names and messages"
                        }
                    }
                },
                "DetailedResponse": {
                    "type": "object",
                    "required": ["data", "metadata"],
                    "properties": {
                        "data": {
                            "type": "array",
                            "description": "Aggregated transaction rows by category and month",
                            "items": {
                                "$ref": "#/components/schemas/AggregatedRow"
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "required": ["processing_time", "row_count", "ml_enabled"],
                            "properties": {
                                "processing_time": {
                                    "type": "number",
                                    "description": "Processing time in seconds",
                                    "example": 0.35
                                },
                                "row_count": {
                                    "type": "integer",
                                    "description": "Number of transactions processed",
                                    "example": 156
                                },
                                "ml_enabled": {
                                    "type": "boolean",
                                    "description": "Whether ML categorization was used"
                                },
                                "date_range": {
                                    "type": "object",
                                    "description": "Date range filter applied",
                                    "properties": {
                                        "start": {
                                            "type": "string",
                                            "format": "date"
                                        },
                                        "end": {
                                            "type": "string",
                                            "format": "date"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "AggregatedRow": {
                    "type": "object",
                    "required": ["category", "total", "month", "details"],
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Transaction category",
                            "example": "Grocery"
                        },
                        "total": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "month": {
                            "$ref": "#/components/schemas/DateField"
                        },
                        "details": {
                            "type": "array",
                            "description": "Individual transaction details",
                            "items": {
                                "$ref": "#/components/schemas/DetailRow"
                            }
                        }
                    }
                },
                "AmountField": {
                    "type": "object",
                    "required": ["display", "raw"],
                    "description": "Field with formatted display value and raw numeric value",
                    "properties": {
                        "display": {
                            "type": "string",
                            "description": "Formatted value for display",
                            "example": "HUF -45,600.50"
                        },
                        "raw": {
                            "type": "number",
                            "description": "Raw numeric value for calculations/sorting",
                            "example": -45600.50
                        }
                    }
                },
                "DateField": {
                    "type": "object",
                    "required": ["display", "timestamp"],
                    "description": "Date field with formatted display and Unix timestamp",
                    "properties": {
                        "display": {
                            "type": "string",
                            "description": "Formatted date or month name",
                            "example": "January"
                        },
                        "timestamp": {
                            "type": "integer",
                            "description": "Unix epoch timestamp",
                            "example": 1704067200
                        }
                    }
                },
                "DetailRow": {
                    "type": "object",
                    "required": ["date", "amount", "merchant", "currency"],
                    "description": "Individual transaction detail",
                    "properties": {
                        "date": {
                            "$ref": "#/components/schemas/DateField"
                        },
                        "amount": {
                            "$ref": "#/components/schemas/AmountField"
                        },
                        "merchant": {
                            "type": "string",
                            "description": "Merchant or transaction partner",
                            "example": "TESCO"
                        },
                        "currency": {
                            "type": "string",
                            "description": "Transaction currency code",
                            "example": "HUF"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["status", "error"],
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["error"],
                            "description": "Response status"
                        },
                        "error": {
                            "type": "object",
                            "required": ["code", "message"],
                            "properties": {
                                "code": {
                                    "type": "integer",
                                    "description": "HTTP status code",
                                    "example": 404
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Error message",
                                    "example": "Results expired, please re-process"
                                },
                                "details": {
                                    "type": "string",
                                    "description": "Additional error details"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

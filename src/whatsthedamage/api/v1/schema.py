"""OpenAPI 3.0 schema for whatsthedamage v1 API.

This module defines the OpenAPI specification for the v1 API endpoints.
V1 API focuses on summary-level transaction data (aggregated totals by category).
"""
from typing import Any


def get_openapi_schema() -> dict[str, Any]:
    """Generate OpenAPI 3.0 schema for v1 API.
    
    Returns:
        dict: OpenAPI 3.0 specification
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "whatsthedamage API v1",
            "description": (
                "REST API for processing bank transaction CSV exports. "
                "V1 provides summary-level aggregated data (totals by category). "
                "Supports both regex-based and ML-based transaction categorization."
            ),
            "version": "1.0.0",
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
                "url": "/api/v1",
                "description": "V1 API base path"
            }
        ],
        "paths": {
            "/process": {
                "post": {
                    "summary": "Process CSV transaction file",
                    "description": (
                        "Upload a CSV file containing bank transactions and receive "
                        "aggregated summary data grouped by category. Optionally upload "
                        "a YAML configuration file to customize processing."
                    ),
                    "operationId": "processTransactions",
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
                            "description": "Successfully processed transactions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SummaryResponse"
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
                "SummaryResponse": {
                    "type": "object",
                    "required": ["status", "data", "metadata"],
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success"],
                            "description": "Response status"
                        },
                        "data": {
                            "type": "object",
                            "description": "Summary data grouped by category and month",
                            "additionalProperties": {
                                "type": "object",
                                "description": "Category name as key",
                                "additionalProperties": {
                                    "type": "number",
                                    "description": "Month name (or 'Total') as key, amount as value"
                                }
                            },
                            "example": {
                                "Grocery": {
                                    "January": -45600.50,
                                    "February": -52300.00,
                                    "Total": -97900.50
                                },
                                "Salary": {
                                    "January": 350000.00,
                                    "February": 350000.00,
                                    "Total": 700000.00
                                },
                                "Balance": {
                                    "January": 304399.50,
                                    "February": 297700.00,
                                    "Total": 602099.50
                                }
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "required": ["processing_time", "row_count", "ml_enabled"],
                            "properties": {
                                "processing_time": {
                                    "type": "number",
                                    "description": "Processing time in seconds",
                                    "example": 0.25
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
                                "filters_applied": {
                                    "type": "object",
                                    "description": "Filters applied during processing",
                                    "properties": {
                                        "start_date": {
                                            "type": "string",
                                            "format": "date"
                                        },
                                        "end_date": {
                                            "type": "string",
                                            "format": "date"
                                        },
                                        "category": {
                                            "type": "string"
                                        }
                                    }
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
                                    "example": 400
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Error message",
                                    "example": "Invalid CSV file format"
                                },
                                "details": {
                                    "type": "string",
                                    "description": "Additional error details",
                                    "example": "Missing required column: Transaction Date"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

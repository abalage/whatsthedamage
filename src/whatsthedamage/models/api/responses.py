"""API v2 Response Data Transfer Objects.

These Pydantic models define the exact contract for each API endpoint response,
ensuring type safety and consistency between backend and frontend.

Each endpoint in api/v2/endpoints.py should return one of these models.

For new endpoints, consider using the ApiEnvelope<T> wrapper for standardized
response format with metadata and hypermedia links.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any, Generic, TypeVar
from datetime import datetime
from whatsthedamage.models.domain.account import Account


# =============================================================================
# Standard Response Envelope (for new endpoints)
# =============================================================================

T = TypeVar('T')

class ApiEnvelope(BaseModel, Generic[T]):
    """Standard response envelope for API v2 endpoints.

    Provides a consistent structure for all API responses, enabling:
    - Standardized metadata (status, timestamp, request_id)
    - Hypermedia navigation (links)
    - Consistent error handling format
    - Type-safe data payload

    Recommended for new endpoints. Existing endpoints maintain their specific
    response formats for backward compatibility.

    Attributes:
        status (str): Operation status ('success' or 'error')
        data (T): The endpoint-specific response payload
        meta (Dict[str, Any]): Response metadata (timestamp, request_id, version, etc.)
        links (Dict[str, str]): Hypermedia navigation links (self, related resources)
        timestamp (datetime): Response generation timestamp in UTC

    Example usage::

        @v2_bp.route('/new-endpoint')
        def new_endpoint():
            payload = SomeDataModel(...)
            return ApiEnvelope[SomeDataModel](
                status='success',
                data=payload,
                meta={'request_id': '...', 'version': 'v2'},
                links={'self': '/api/v2/new-endpoint'}
            )
    """
    status: str = Field(
        default="success",
        description="Response status: 'success' for 2xx, 'error' for 4xx/5xx"
    )
    data: T = Field(
        description="Endpoint-specific response data payload"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata including timestamp, request_id, version"
    )
    links: Dict[str, str] = Field(
        default_factory=dict,
        description="Hypermedia links for navigation (self, related, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response generation timestamp in UTC"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {"result_id": "...", "items": []},
                "meta": {
                    "request_id": "req_abc123",
                    "version": "v2",
                    "api_version": "2.0"
                },
                "links": {
                    "self": "/api/v2/new-endpoint",
                    "doc": "/docs/api/v2/new-endpoint"
                },
                "timestamp": "2025-01-01T00:00:00Z"
            }
        }
    )


# =============================================================================
# Process Endpoint Response



# =============================================================================
# Results Endpoint Responses
# =============================================================================

class DrilldownUrlInfo(BaseModel):
    """URL information for drilldown navigation."""
    category_url: str = Field(description="URL to view category details")
    category_id: str = Field(description="Category identifier")


class MonthUrlInfo(BaseModel):
    """URL information for month navigation."""
    month_url: str = Field(description="URL to view month details")
    month_id: str = Field(description="Month identifier")


class CellUrlInfo(BaseModel):
    """URL information for cell navigation."""
    cell_url: str = Field(description="URL to view cell/transaction details")
    category_id: str = Field(description="Category identifier for the cell")
    month_id: str = Field(description="Month identifier for the cell")


class DrilldownUrls(BaseModel):
    """All drilldown URLs for a single account."""
    account_id: Optional[str] = Field(
        default=None,
        description="Account identifier"
    )
    category_urls: Dict[str, DrilldownUrlInfo] = Field(
        default_factory=dict,
        description="Category drilldown URLs mapped by category ID"
    )
    month_urls: Dict[str, MonthUrlInfo] = Field(
        default_factory=dict,
        description="Month drilldown URLs mapped by month ID"
    )
    cell_urls: Dict[str, CellUrlInfo] = Field(
        default_factory=dict,
        description="Cell drilldown URLs mapped by row ID"
    )


class ResultsApiResponse(BaseModel):
    """Response for GET /api/v2/results/<result_id> endpoint.

    Returns cached processing results with drilldown URLs for frontend rendering.

    Attributes:
        result_id: UUID of the cached processing result
        accounts: List of Account objects with processing data
        highlights: Statistical highlights mapped by row_id to highlight types
        drilldown_urls_by_account: Navigation URLs for drilldown views organized by account
    """
    result_id: str = Field(description="Unique identifier for this processing result")
    accounts: List[Account] = Field(
        description="List of account data with processing results"
    )
    highlights: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Statistical highlights mapped by row_id to highlight types"
    )
    drilldown_urls_by_account: Dict[str, DrilldownUrls] = Field(
        default_factory=dict,
        description="Drilldown navigation URLs organized by account ID"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "accounts_data": {
                    "accounts": [
                        {
                            "id": "account_1",
                            "name": "Primary Account",
                            "dt_response": {
                                "data": []
                            }
                        }
                    ],
                    "highlights": {
                        "row_abc123": ["outlier", "pareto"]
                    }
                },
                "drilldown_urls_by_account": {}
            }
        }
    )


# =============================================================================
# Drilldown Endpoint Responses
# =============================================================================

class MonthData(BaseModel):
    """Data for a single month in category months response.

    Frontend should use month_timestamp to format the month display name
    according to the current locale.
    """
    month_timestamp: int = Field(description="Unix timestamp for the month")
    total: Dict[str, Any] = Field(
        description="Total amount with display and raw values"
    )
    row_id: str = Field(description="Unique row identifier")
    cell_url: str = Field(description="URL for drilling down to cell details")


class CategoryMonthsApiResponse(BaseModel):
    """Response for GET /api/v2/results/<result_id>/accounts/<account_id>/categories/<category_id>/months endpoint.

    Returns month-by-month aggregation for a specific category.
    """
    result_id: str = Field(description="Processing result identifier")
    account_id: str = Field(description="Account identifier")
    account_name: str = Field(description="Account display name")
    category_id: str = Field(description="Category identifier (e.g., 'grocery'). Frontend should use /categories endpoint to get display name.")
    data: List[MonthData] = Field(
        description="Month-by-month aggregation data for this category"
    )
    highlights: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Statistical highlights for drilldown rows, mapped by row_id to highlight types"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "account_id": "account_1",
                "account_name": "Primary Account",
                "category_id": "cat_groceries",
                "category_name": "Groceries",
                "data": [
                    {
                        "month_timestamp": 1704067200,
                        "total": {"display": "-500.00", "raw": -500.0},
                        "row_id": "row_001",
                        "cell_url": "/api/v2/results/.../transactions"
                    }
                ],
                "highlights": {
                    "row_001": ["outlier"]
                }
            }
        }
    )


class CategoryData(BaseModel):
    """Data for a single category in month categories response."""
    category: str = Field(description="Category name")
    total: Dict[str, Any] = Field(
        description="Total amount with display and raw values"
    )
    row_id: str = Field(description="Unique row identifier")
    category_url: str = Field(description="URL for drilling down to category details")


class MonthCategoriesApiResponse(BaseModel):
    """Response for GET /api/v2/results/<result_id>/accounts/<account_id>/months/<month_id>/categories endpoint.

    Returns category-by-category aggregation for a specific month.
    Frontend should use month_timestamp to format the month display name.
    """
    result_id: str = Field(description="Processing result identifier")
    account_id: str = Field(description="Account identifier")
    account_name: str = Field(description="Account display name")
    month_id: str = Field(description="Month identifier (opaque ID for URL routing)")
    month_timestamp: int = Field(description="Unix timestamp for the month")
    data: List[CategoryData] = Field(
        description="Category-by-category aggregation data for this month"
    )
    highlights: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Statistical highlights for drilldown rows, mapped by row_id to highlight types"
    )


class TransactionDetail(BaseModel):
    """Data for a single transaction in drilldown response."""
    date: Dict[str, str] = Field(
        description="Date information with display format"
    )
    amount: Dict[str, Any] = Field(
        description="Amount with display and raw values"
    )
    merchant: str = Field(description="Merchant or transaction description")
    row_id: str = Field(description="Unique row identifier")
    currency: str = Field(default="", description="Currency code")
    type: str = Field(default="", description="Transaction type")
    confidence: Optional[float] = Field(default=None, description="ML confidence score if applicable")
    notice: Optional[str] = Field(default=None, description="Transaction notice or memo")
    category_id: str = Field(default="", description="Category identifier")
    month_id: str = Field(default="", description="Month identifier")


class CategoryMonthTransactionsApiResponse(BaseModel):
    """Response for GET /api/v2/results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions endpoint.

    Returns individual transaction details for a specific category and month.
    Frontend should use month_timestamp to format the month display name.
    """
    result_id: str = Field(description="Processing result identifier")
    account_id: str = Field(description="Account identifier")
    account_name: str = Field(description="Account display name")
    category_id: str = Field(description="Category identifier (e.g., 'grocery'). Frontend should use /categories endpoint to get display name.")
    month_id: str = Field(description="Month identifier (opaque ID for URL routing)")
    month_timestamp: int = Field(description="Unix timestamp for the month")
    data: List[TransactionDetail] = Field(
        description="Individual transaction details"
    )
    highlights: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Statistical highlights for transactions, mapped by row_id to highlight types"
    )


# =============================================================================
# Recalculate Statistics Endpoint Response
# =============================================================================

class RecalculateApiResponse(BaseModel):
    """Response for POST /api/v2/recalculate-statistics endpoint.

    Returns updated statistical highlights with new algorithm settings.

    Attributes:
        status: Operation status (always 'success' for 200 responses)
        result_id: Processing result identifier
        highlights: Updated statistical highlights mapped by row_id to highlight types
        algorithms: List of algorithm names used (e.g., ['iqr', 'pareto'])
        direction: Analysis direction ('rows' or 'columns')
    """
    status: str = Field(
        default="success",
        description="Operation status"
    )
    result_id: str = Field(description="Processing result identifier")
    highlights: Dict[str, List[str]] = Field(
        description="Updated statistical highlights mapped by row_id to list of highlight types"
    )
    algorithms: List[str] = Field(
        description="List of algorithm names used (e.g., ['iqr', 'pareto'])"
    )
    direction: str = Field(
        description="Analysis direction: 'rows' for row-based analysis or 'columns' for column-based analysis"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "highlights": {
                    "row_abc123": ["outlier", "pareto"],
                    "row_def456": ["outlier"]
                },
                "algorithms": ["iqr", "pareto"],
                "direction": "columns"
            }
        }
    )


# =============================================================================
# Error Response
# =============================================================================

class ErrorApiResponse(BaseModel):
    """Standard error response format for all API v2 endpoints.

    All error responses (non-200 status codes) should use this format.

    Attributes:
        code: HTTP status code
        message: Human-readable error description
        details: Optional additional error context/diagnostics
    """
    code: int = Field(
        description="HTTP status code (400, 404, 422, 500, etc.)"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details for debugging"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 400,
                "message": "Missing required file: csv_file",
                "details": {
                    "field": "csv_file",
                    "expected": "multipart/form-data"
                }
            }
        }
    )

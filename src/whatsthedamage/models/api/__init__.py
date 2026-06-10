"""API-specific models for REST API v2 endpoints.

This package contains all Pydantic models used for API request/response contracts.
"""

from whatsthedamage.models.api.requests import ProcessingRequest
from whatsthedamage.models.api.responses import (
    ApiEnvelope,
    AccountDataResponse,
    AccountsDataResponse,
    DrilldownUrlInfo,
    MonthUrlInfo,
    CellUrlInfo,
    DrilldownUrls,
    ResultsApiResponse,
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse,
    TransactionDetail,
    CategoryData,
    MonthData,
    RecalculateApiResponse,
    ErrorApiResponse,
)
from whatsthedamage.models.api.common import ProcessingMetadata, ErrorResponse

__all__ = [
    # Request models
    'ProcessingRequest',
    # Response models
    'ApiEnvelope',
    'AccountDataResponse',
    'AccountsDataResponse',
    'DrilldownUrlInfo',
    'MonthUrlInfo',
    'CellUrlInfo',
    'DrilldownUrls',
    'ResultsApiResponse',
    'CategoryMonthsApiResponse',
    'MonthCategoriesApiResponse',
    'CategoryMonthTransactionsApiResponse',
    'TransactionDetail',
    'CategoryData',
    'MonthData',
    'RecalculateApiResponse',
    'ErrorApiResponse',
    # Common models
    'ProcessingMetadata',
    'ErrorResponse',
]

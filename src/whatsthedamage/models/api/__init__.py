"""API-specific models for REST API v2 endpoints.

This package provides a clean organization of API-related models.
"""

# Request models
from whatsthedamage.models.api.requests import ProcessingRequest

# Response models
from whatsthedamage.models.api.responses import (
    ApiEnvelope,
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

# Common models
from whatsthedamage.models.api.common import ProcessingMetadata, ErrorResponse

__all__ = [
    # Request models
    'ProcessingRequest',
    # Common models
    'ProcessingMetadata',
    'ErrorResponse',
    # Response models
    'ApiEnvelope',
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
]

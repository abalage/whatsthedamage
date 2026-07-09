"""API-specific models for REST API v2 endpoints.

This package provides a clean organization of API-related models.
"""
from typing import TYPE_CHECKING

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
    CategoryData,
    MonthData,
    RecalculateApiResponse,
)

# Common models
from whatsthedamage.models.api.common import ProcessingMetadata
from whatsthedamage.models.common.error_models import ErrorResponse

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
    'CategoryData',
    'MonthData',
    'RecalculateApiResponse',
]

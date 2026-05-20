"""Interfaces for service layer components.

This module defines abstract base classes (interfaces) for service components
to enable better testability through dependency injection and mocking.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from whatsthedamage.models.dt_models import DataTablesResponse, StatisticalMetadata
from whatsthedamage.models.api_responses import (
    CategoryMonthsApiResponse,
    MonthCategoriesApiResponse,
    CategoryMonthTransactionsApiResponse
)

class ICacheService(ABC):
    """Interface for cache service operations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data by key.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached data or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Store data in cache.

        Args:
            key: Cache key
            value: Data to cache
            timeout: Optional timeout in seconds
        """
        pass

class IIdMappingService(ABC):
    """Interface for ID mapping service operations."""

    @abstractmethod
    def get_account_number(self, result_id: str, account_id: str) -> Optional[str]:
        """Get original account number from secure account ID.

        Args:
            result_id: Processing result ID
            account_id: Secure account ID

        Returns:
            Original account number or None if not found
        """
        pass

    @abstractmethod
    def get_account_id(self, result_id: str, account_number: str) -> Optional[str]:
        """Get secure account ID from original account number.

        Args:
            result_id: Processing result ID
            account_number: Original account number

        Returns:
            Secure account ID or None if not found
        """
        pass

    @abstractmethod
    def get_category_name(self, result_id: str, category_id: str) -> Optional[str]:
        """Get original category name from secure category ID.

        Args:
            result_id: Processing result ID
            category_id: Secure category ID

        Returns:
            Original category name or None if not found
        """
        pass

    @abstractmethod
    def get_category_id(self, result_id: str, category_name: str) -> Optional[str]:
        """Get secure category ID from original category name.

        Args:
            result_id: Processing result ID
            category_name: Original category name

        Returns:
            Secure category ID or None if not found
        """
        pass

    @abstractmethod
    def get_month_timestamp(self, month_id: str) -> Optional[str]:
        """Get original month timestamp from secure month ID.

        Args:
            month_id: Secure month ID

        Returns:
            Original month timestamp or None if not found
        """
        pass

    @abstractmethod
    def get_month_id(self, month_timestamp: str) -> Optional[str]:
        """Get secure month ID from original month timestamp.

        Args:
            month_timestamp: Original month timestamp

        Returns:
            Secure month ID or None if not found
        """
        pass

class IDataFormattingService(ABC):
    """Interface for data formatting service operations."""

    @abstractmethod
    def format_account_id(self, account_number: str) -> str:
        """Format account number for display.

        Args:
            account_number: Original account number

        Returns:
            Formatted account string
        """
        pass

    @abstractmethod
    def _convert_metadata_to_highlights_dict(self, statistical_metadata: 'StatisticalMetadata') -> Dict[str, List[str]]:
        """Convert statistical metadata to highlights dictionary.

        Args:
            statistical_metadata: Statistical metadata from processing

        Returns:
            Dictionary mapping row IDs to highlight types
        """
        pass

class IStatisticalAnalysisService(ABC):
    """Interface for statistical analysis service operations."""

    @abstractmethod
    def compute_statistical_metadata(
        self,
        datatables_responses: Dict[str, DataTablesResponse],
        algorithms: List[str],
        direction: Optional[str] = None
    ) -> StatisticalMetadata:
        """Compute statistical metadata for processing results.

        Args:
            datatables_responses: Processing results by account
            algorithms: List of algorithm names to use
            direction: Analysis direction ('columns' or 'rows')

        Returns:
            Statistical metadata object
        """
        pass


class IDrilldownResponseService(ABC):
    """Interface for drilldown response service operations."""

    @abstractmethod
    def get_category_months_response(
        self,
        result_id: str,
        account_id: str,
        category_id: str
    ) -> CategoryMonthsApiResponse:
        """Build response for category months drilldown endpoint.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to get months for

        Returns:
            CategoryMonthsApiResponse: Pydantic model with months data, highlights, and drilldown URLs

        Raises:
            ValueError: If result, account, or category not found
        """
        pass

    @abstractmethod
    def get_month_categories_response(
        self,
        result_id: str,
        account_id: str,
        month_id: str
    ) -> MonthCategoriesApiResponse:
        """Build response for month categories drilldown endpoint.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            month_id: Secure month ID to get categories for

        Returns:
            MonthCategoriesApiResponse: Pydantic model with categories data, highlights, and drilldown URLs

        Raises:
            ValueError: If result, account, or month not found
        """
        pass

    @abstractmethod
    def get_category_month_transactions_response(
        self,
        result_id: str,
        account_id: str,
        category_id: str,
        month_id: str
    ) -> CategoryMonthTransactionsApiResponse:
        """Build response for category month transactions drilldown endpoint.

        Args:
            result_id: UUID of the cached processing result
            account_id: Secure account ID to filter by
            category_id: Secure category ID to filter by
            month_id: Secure month ID to filter by

        Returns:
            CategoryMonthTransactionsApiResponse: Pydantic model with transaction details, highlights, and metadata

        Raises:
            ValueError: If result, account, category, month, or transactions not found
        """
        pass
